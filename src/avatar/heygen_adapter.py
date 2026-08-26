from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
from urllib.parse import urlparse

ALLOWED_STATUSES = {None, "waiting", "pending", "queued", "processing", "running", "completed", "failed"}
ALLOWED_ASPECTS = {"9:16", "16:9"}
ALLOWED_RESOLUTIONS = {"720p", "1080p", "4k"}
ALLOWED_FORMATS = {"mp4", "webm"}
MAX_SCRIPT_CHARS = 20_000
MAX_MOTION_PROMPT_CHARS = 2_000
MAX_TITLE_CHARS = 160


@dataclass(frozen=True)
class HeyGenRequest:
    avatarId: str
    voiceId: str
    script: str
    title: str
    aspectRatio: str = "9:16"
    resolution: str = "1080p"
    outputFormat: str = "mp4"
    expressiveness: str = "medium"
    motionPrompt: str | None = None
    voiceSettings: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        return {k: v for k, v in payload.items() if v is not None}


def _safe_https_url(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError("provider URL must be a string")
    if len(value) > 4096:
        raise ValueError("provider URL too long")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("provider URL must be an absolute HTTPS URL without embedded credentials")
    return value


def validate_provider_result(provider_result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    status = provider_result.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"unknown provider status: {status}")
    duration = provider_result.get("duration")
    if duration is not None:
        try:
            value = float(duration)
            if value <= 0 or value > 3600:
                errors.append(f"implausible provider duration: {value}")
        except (TypeError, ValueError):
            errors.append("provider duration must be numeric")
    for field in ("video_url", "thumbnail_url"):
        try:
            _safe_https_url(provider_result.get(field))
        except ValueError as exc:
            errors.append(f"{field}: {exc}")
    job_id = provider_result.get("id") or provider_result.get("video_id")
    if job_id is not None and (not isinstance(job_id, str) or not job_id or len(job_id) > 256):
        errors.append("provider job id malformed")
    return errors


def compile_request(manifest: dict[str, Any], profile: dict[str, Any], *, title: str,
                    motion_prompt: str | None = None) -> dict[str, Any]:
    script = manifest.get("script_tts_text")
    if not isinstance(script, str) or not script.strip():
        raise ValueError("manifest.script_tts_text required")
    if len(script) > MAX_SCRIPT_CHARS:
        raise ValueError("manifest.script_tts_text exceeds provider-safe limit")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title required")
    if motion_prompt is not None and (not isinstance(motion_prompt, str) or len(motion_prompt) > MAX_MOTION_PROMPT_CHARS):
        raise ValueError("motion prompt malformed or too long")

    avatar_id = profile.get("look_id")
    voice_id = profile.get("voice_id")
    if not isinstance(avatar_id, str) or not avatar_id or len(avatar_id) > 256:
        raise ValueError("profile.look_id malformed")
    if not isinstance(voice_id, str) or not voice_id or len(voice_id) > 256:
        raise ValueError("profile.voice_id malformed")

    aspect = profile.get("aspect_ratio", "9:16")
    resolution = profile.get("resolution", "1080p")
    output_format = profile.get("output_format", "mp4")
    if aspect not in ALLOWED_ASPECTS:
        raise ValueError(f"unsupported aspect ratio: {aspect}")
    if resolution not in ALLOWED_RESOLUTIONS:
        raise ValueError(f"unsupported resolution: {resolution}")
    if output_format not in ALLOWED_FORMATS:
        raise ValueError(f"unsupported output format: {output_format}")
    if not 0.5 <= float(profile.get("speed", 1.0)) <= 1.5:
        raise ValueError("voice speed outside provider-safe range")
    request = HeyGenRequest(
        avatarId=avatar_id,
        voiceId=voice_id,
        script=script,
        title=title[:MAX_TITLE_CHARS],
        aspectRatio=aspect,
        resolution=resolution,
        outputFormat=output_format,
        expressiveness=profile.get("expressiveness", "medium"),
        motionPrompt=motion_prompt,
        voiceSettings={"speed": profile.get("speed", 1.0), "pitch": 0, "volume": 1},
    )
    return request.to_payload()


def ingest_render_telemetry(manifest: dict[str, Any], provider_result: dict[str, Any]) -> dict[str, Any]:
    errors = validate_provider_result(provider_result)
    if errors:
        raise ValueError("invalid provider telemetry: " + "; ".join(errors))
    out = dict(manifest)
    render = dict(out.get("render", {}))
    render.update({
        "provider_job_id": provider_result.get("id") or provider_result.get("video_id") or render.get("provider_job_id"),
        "status": provider_result.get("status", render.get("status")),
        "actual_duration_s": provider_result.get("duration", render.get("actual_duration_s")),
        "asset_ref": _safe_https_url(provider_result.get("video_url")) or render.get("asset_ref"),
        "thumbnail_ref": _safe_https_url(provider_result.get("thumbnail_url")) or render.get("thumbnail_ref"),
        "failure_code": provider_result.get("failure_code"),
        "failure_message": provider_result.get("failure_message"),
    })
    out["render"] = render
    return out
