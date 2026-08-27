from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE_PATH = ROOT / "config" / "avatar_profiles.json"
DEFAULT_SCHEMA_PATH = ROOT / "schemas" / "avatar_content_manifest.schema.json"

DRIVERS = {"MONEY", "LOVE", "HEALTH", "PERSONAL_GROWTH"}
BEAT_ID_RE = re.compile(r"^B\d{2}_[A-Z0-9_]+$")
WORD_RE = re.compile(r"\b[\wÁÉÍÓÚÜÑáéíóúüñ'-]+\b", re.UNICODE)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "ERROR"


def load_profiles(path: Path | str = DEFAULT_PROFILE_PATH) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_profile(profile_id: str, path: Path | str = DEFAULT_PROFILE_PATH) -> dict[str, Any]:
    payload = load_profiles(path)
    try:
        return deepcopy(payload["profiles"][profile_id])
    except KeyError as exc:
        raise KeyError(f"Unknown avatar profile: {profile_id}") from exc


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def estimate_duration_s(text: str, profile: Mapping[str, Any], phonetic_expansion_chars: int = 0) -> float:
    speed = float(profile.get("speed", 1.0))
    wps = max(float(profile.get("initial_words_per_second", 2.5)) * speed, 0.1)
    base = word_count(text) / wps
    costs = profile.get("pause_cost_s", {})
    pause = (
        text.count(",") * float(costs.get("comma", 0.10))
        + len(re.findall(r"[.!?]", text)) * float(costs.get("sentence", 0.22))
        + text.count("…") * float(costs.get("ellipsis", 0.32))
        + text.count(":") * float(costs.get("colon", 0.16))
    )
    expansion = max(phonetic_expansion_chars, 0) * 0.012 / max(speed, 0.1)
    return round(base + pause + expansion, 2)


def apply_pronunciation_overrides(display_text: str, overrides: Mapping[str, str]) -> str:
    """Build provider-safe TTS text without mutating canonical display text."""
    result = str(display_text)
    for source in sorted(overrides, key=len, reverse=True):
        target = overrides[source]
        pattern = re.compile(rf"(?<!\w){re.escape(source)}(?!\w)", re.IGNORECASE)
        result = pattern.sub(target, result)
    return result


def build_avatar_request(manifest: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "provider": profile["provider"],
        "avatarId": profile["look_id"],
        "voiceId": profile["voice_id"],
        "script": manifest["script_tts_text"],
        "aspectRatio": profile["aspect_ratio"],
        "resolution": profile["resolution"],
        "outputFormat": profile.get("output_format", "mp4"),
        "expressiveness": profile.get("expressiveness", "medium"),
        "voiceSettings": {"speed": profile.get("speed", 1.0), "pitch": 0, "volume": 1},
    }


def ingest_render_telemetry(manifest: Mapping[str, Any], *, provider_job_id: str | None, status: str | None,
                            actual_duration_s: float | None = None, asset_ref: str | None = None,
                            credits_used: float | None = None) -> dict[str, Any]:
    out = deepcopy(dict(manifest))
    out.setdefault("render", {})
    out["render"].update({
        "provider_job_id": provider_job_id,
        "status": status,
        "actual_duration_s": actual_duration_s,
        "asset_ref": asset_ref,
        "credits_used": credits_used,
    })
    return out


def validate_manifest(manifest: Mapping[str, Any], profile: Mapping[str, Any] | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    driver = manifest.get("viral_driver")
    if driver not in DRIVERS:
        issues.append(ValidationIssue("DRIVER_INVALID", f"viral_driver must be one of {sorted(DRIVERS)}"))

    target = manifest.get("duration_target_s")
    if not isinstance(target, (int, float)) or not 30 <= float(target) <= 45:
        issues.append(ValidationIssue("TARGET_DURATION_INVALID", "duration_target_s must be within 30–45s"))

    beats = manifest.get("semantic_beats") or []
    ids = [b.get("id") for b in beats if isinstance(b, Mapping)]
    if len(ids) != len(set(ids)):
        issues.append(ValidationIssue("BEAT_ID_DUPLICATE", "semantic beat IDs must be unique"))
    malformed = [bid for bid in ids if not isinstance(bid, str) or not BEAT_ID_RE.match(bid)]
    if malformed:
        issues.append(ValidationIssue("BEAT_ID_INVALID", f"invalid beat IDs: {malformed}"))

    cta = manifest.get("cta") or {}
    if not cta.get("text"):
        issues.append(ValidationIssue("CTA_MISSING", "CTA text is required"))
    if cta.get("target_beat_id") and cta.get("target_beat_id") not in ids:
        issues.append(ValidationIssue("CTA_BEAT_MISSING", "CTA target beat must exist"))
    if not str(manifest.get("moral", "")).strip():
        issues.append(ValidationIssue("MORAL_MISSING", "moral/payoff is required"))
    if not manifest.get("source_refs"):
        issues.append(ValidationIssue("SOURCE_REFS_MISSING", "at least one source reference is required"))
    if not manifest.get("claim_notes"):
        issues.append(ValidationIssue("CLAIM_NOTES_MISSING", "claim provenance cannot be dropped"))

    display = str(manifest.get("script_display_text", ""))
    tts = str(manifest.get("script_tts_text", ""))
    if not display or not tts:
        issues.append(ValidationIssue("SCRIPT_MISSING", "display and TTS scripts are both required"))
    overrides = manifest.get("pronunciation_overrides") or {}
    if overrides and display == tts:
        issues.append(ValidationIssue("TTS_NOT_NORMALIZED", "pronunciation overrides exist but display/TTS text are identical"))

    if profile is not None and tts:
        expansion = max(len(tts) - len(display), 0)
        estimated = estimate_duration_s(tts, profile, phonetic_expansion_chars=expansion)
        hard_min = float(profile.get("duration_hard_min_s", 30))
        hard_max = float(profile.get("duration_hard_max_s", 45))
        if not hard_min <= estimated <= hard_max:
            issues.append(ValidationIssue("ESTIMATED_DURATION_OUT_OF_RANGE", f"estimated duration {estimated}s outside {hard_min:.0f}–{hard_max:.0f}s"))

    # Retention heuristic: if target is known, average beat duration should remain close to 3s.
    if isinstance(target, (int, float)) and beats:
        avg = float(target) / len(beats)
        if avg > 4.5:
            issues.append(ValidationIssue("RETENTION_BEAT_DENSITY_LOW", f"average semantic beat spacing {avg:.2f}s is too sparse", "WARN"))

    return issues


def assert_manifest(manifest: Mapping[str, Any], profile: Mapping[str, Any] | None = None) -> None:
    issues = [x for x in validate_manifest(manifest, profile) if x.severity == "ERROR"]
    if issues:
        raise ValueError("; ".join(f"{x.code}: {x.message}" for x in issues))


def schema_validate(manifest: Mapping[str, Any], schema_path: Path | str = DEFAULT_SCHEMA_PATH) -> None:
    """Optional jsonschema validation; dependency is part of the dev extra."""
    from jsonschema import Draft202012Validator

    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(dict(manifest))


def serialize_manifest(manifest: Mapping[str, Any]) -> str:
    return json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def deserialize_manifest(payload: str) -> dict[str, Any]:
    return json.loads(payload)
