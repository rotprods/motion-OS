from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence
import json

from .ingest import VideoMeta
from .segmentation import Shot, validate_shot_coverage


SCHEMA_VERSION = "1.0.0"


def _shot_dict(shot: Shot) -> dict[str, Any]:
    return {
        "id": shot.shot_id,
        "start_ms": shot.start_ms,
        "end_ms": shot.end_ms,
        "start_frame": shot.start_frame,
        "end_frame": shot.end_frame,
        "confidence": shot.confidence,
        "method": shot.method,
    }


def assemble_feature_pack(
    *,
    video_meta: VideoMeta,
    shots: Sequence[Shot],
    keyframes: Sequence[Mapping[str, Any]],
    ocr: Sequence[Mapping[str, Any]] = (),
    color_stats: Mapping[str, Any] | None = None,
    layout_stats: Mapping[str, Any] | None = None,
    motion_stats: Mapping[str, Any] | None = None,
    fx_stats: Mapping[str, Any] | None = None,
    asset_stats: Mapping[str, Any] | None = None,
    audio_stats: Mapping[str, Any] | None = None,
    extraction_provenance: Sequence[Mapping[str, Any]] = (),
    warnings: Sequence[str] = (),
) -> dict[str, Any]:
    total_frames = video_meta.frame_count
    if total_frames is None:
        total_frames = round(video_meta.duration_ms * video_meta.fps / 1000.0)
    coverage_errors = validate_shot_coverage(shots, total_frames)
    all_warnings = list(warnings) + [f"shot_coverage:{e}" for e in coverage_errors]
    return {
        "schema_version": SCHEMA_VERSION,
        "video_meta": {
            "duration_ms": video_meta.duration_ms,
            "fps": video_meta.fps,
            "resolution": {"w": video_meta.width, "h": video_meta.height},
            "aspect_ratio": video_meta.aspect_ratio,
            "codec": video_meta.codec,
            "bitrate": video_meta.bitrate,
            "fps_rational": [video_meta.fps_num, video_meta.fps_den],
            "frame_count": total_frames,
            "source_sha256": video_meta.source_sha256,
        },
        "shots": [_shot_dict(s) for s in shots],
        "keyframes": [dict(k) for k in keyframes],
        "ocr": [dict(x) for x in ocr],
        "color_stats": dict(color_stats or {}),
        "layout_stats": dict(layout_stats or {}),
        "motion_stats": dict(motion_stats or {}),
        "fx_stats": dict(fx_stats or {}),
        "asset_stats": dict(asset_stats or {}),
        "audio_stats": dict(audio_stats or {}),
        "extraction_provenance": [dict(x) for x in extraction_provenance],
        "warnings": all_warnings,
    }


def validate_feature_pack(pack: Mapping[str, Any], schema_path: str | Path = "schemas/feature_pack.schema.json") -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - CI dev deps include jsonschema
        raise RuntimeError("jsonschema is required to validate Feature Packs") from exc
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    jsonschema.validate(instance=dict(pack), schema=schema)


def evidence_coverage(pack: Mapping[str, Any]) -> dict[str, float]:
    """Report evidence coverage for inferred record collections that expose evidence_refs."""
    collections = ["ocr"]
    result: dict[str, float] = {}
    for key in collections:
        items = list(pack.get(key) or [])
        if not items:
            result[key] = 1.0
            continue
        supported = sum(bool(item.get("evidence_refs")) for item in items)
        result[key] = round(supported / len(items), 4)
    return result
