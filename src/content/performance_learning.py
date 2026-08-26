from __future__ import annotations

from dataclasses import dataclass, asdict
from statistics import mean
from typing import Any, Iterable


@dataclass(frozen=True)
class PerformanceRecord:
    content_id: str
    platform: str
    views: int | None = None
    retention_3s: float | None = None
    retention_5s: float | None = None
    average_watch_time_s: float | None = None
    completion_rate: float | None = None
    rewatches: int | None = None
    saves: int | None = None
    shares: int | None = None
    comments: int | None = None
    cta_conversions: int | None = None
    follows: int | None = None


def attach_attribution(manifest: dict[str, Any], perf: PerformanceRecord) -> dict[str, Any]:
    return {
        "performance": asdict(perf),
        "attribution": {
            "content_id": manifest.get("content_id"),
            "viral_driver": manifest.get("viral_driver"),
            "secondary_driver": manifest.get("secondary_driver"),
            "hook": manifest.get("hook"),
            "hook_family": manifest.get("hook_family"),
            "cta_placement": (manifest.get("cta") or {}).get("placement"),
            "duration_target_s": manifest.get("duration_target_s"),
            "duration_actual_s": (manifest.get("render") or {}).get("actual_duration_s"),
            "topic_family": manifest.get("topic_family"),
            "avatar_profile": (manifest.get("avatar") or {}).get("profile_id"),
            "beat_count": len(manifest.get("semantic_beats", [])),
        },
    }


def duration_mae(records: Iterable[dict[str, Any]]) -> float | None:
    errors = []
    for record in records:
        est = record.get("duration_estimate_s")
        actual = (record.get("render") or {}).get("actual_duration_s")
        if est is not None and actual is not None:
            errors.append(abs(float(est) - float(actual)))
    return round(mean(errors), 4) if errors else None


def normalized_duration_error(records: Iterable[dict[str, Any]]) -> float | None:
    errors = []
    for record in records:
        est = record.get("duration_estimate_s")
        actual = (record.get("render") or {}).get("actual_duration_s")
        if est is not None and actual:
            errors.append(abs(float(est) - float(actual)) / float(actual))
    return round(mean(errors), 6) if errors else None
