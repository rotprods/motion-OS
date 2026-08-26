from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


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


def compile_request(manifest: dict[str, Any], profile: dict[str, Any], *, title: str,
                    motion_prompt: str | None = None) -> dict[str, Any]:
    script = manifest.get("script_tts_text")
    if not script:
        raise ValueError("manifest.script_tts_text required")
    request = HeyGenRequest(
        avatarId=profile["look_id"],
        voiceId=profile["voice_id"],
        script=script,
        title=title,
        aspectRatio=profile.get("aspect_ratio", "9:16"),
        resolution=profile.get("resolution", "1080p"),
        outputFormat=profile.get("output_format", "mp4"),
        expressiveness=profile.get("expressiveness", "medium"),
        motionPrompt=motion_prompt,
        voiceSettings={"speed": profile.get("speed", 1.0), "pitch": 0, "volume": 1},
    )
    return request.to_payload()


def ingest_render_telemetry(manifest: dict[str, Any], provider_result: dict[str, Any]) -> dict[str, Any]:
    out = dict(manifest)
    render = dict(out.get("render", {}))
    render.update({
        "provider_job_id": provider_result.get("id") or provider_result.get("video_id") or render.get("provider_job_id"),
        "status": provider_result.get("status", render.get("status")),
        "actual_duration_s": provider_result.get("duration", render.get("actual_duration_s")),
        "asset_ref": provider_result.get("video_url", render.get("asset_ref")),
        "thumbnail_ref": provider_result.get("thumbnail_url", render.get("thumbnail_ref")),
        "failure_code": provider_result.get("failure_code"),
        "failure_message": provider_result.get("failure_message"),
    })
    out["render"] = render
    return out
