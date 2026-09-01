#!/usr/bin/env python3
"""Project an S04 source-bound measurement into an explicit nine-dimension authority result.

This script never upgrades a partial/flattened-source measurement to full fidelity.
It closes only measured P0/P1 reconstruction defects whose declared gates pass.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ROLES = ("setup", "hero", "tail")

THRESHOLDS = {
    "mean_bbox_iou_min": 0.90,
    "mean_centroid_error_px_max": 3.0,
    "mean_area_error_pct_max": 8.0,
    "audio_onset_error_frames_max": 1.5,
}


def _num(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    return float(value)


def build_qualification(measurement: dict, *, renderer_head: str, artifact_id: int, artifact_digest: str) -> dict:
    if not SHA256_RE.fullmatch(renderer_head):
        raise ValueError("renderer_head must be a lowercase 64-char sha")
    if isinstance(artifact_id, bool) or not isinstance(artifact_id, int) or artifact_id <= 0:
        raise ValueError("artifact_id must be a positive integer")
    if not DIGEST_RE.fullmatch(artifact_digest):
        raise ValueError("artifact_digest must be sha256:<64 lowercase hex>")

    components = measurement.get("component_metrics") or measurement.get("post_repair", {}).get("components")
    audio = measurement.get("audio") or measurement.get("post_repair", {}).get("audio")
    source = measurement.get("source")
    if not isinstance(components, dict) or not isinstance(audio, dict) or not isinstance(source, dict):
        raise ValueError("measurement must bind source, component metrics and audio")

    role_results = {}
    for role in ROLES:
        metric = components.get(role)
        if not isinstance(metric, dict):
            raise ValueError(f"missing role metric: {role}")
        iou = _num(metric["mean_bbox_iou"], f"{role}.mean_bbox_iou")
        centroid = _num(metric["mean_centroid_error_px"], f"{role}.mean_centroid_error_px")
        area = _num(metric["mean_area_error_pct"], f"{role}.mean_area_error_pct")
        temporal = metric.get("temporal_visibility_exact") is True
        passed = (
            iou >= THRESHOLDS["mean_bbox_iou_min"]
            and centroid <= THRESHOLDS["mean_centroid_error_px_max"]
            and area <= THRESHOLDS["mean_area_error_pct_max"]
            and temporal
        )
        role_results[role] = {
            "pass": passed,
            "mean_bbox_iou": iou,
            "mean_centroid_error_px": centroid,
            "mean_area_error_pct": area,
            "temporal_visibility_exact": temporal,
        }

    onset_error = _num(audio["absolute_error_frames"], "audio.absolute_error_frames")
    audio_timing_pass = onset_error <= THRESHOLDS["audio_onset_error_frames_max"]
    p0_p1_closed = all(v["pass"] for v in role_results.values()) and audio_timing_pass

    dimensions = {
        "temporal": {"state": "PASS" if all(v["temporal_visibility_exact"] for v in role_results.values()) else "FAIL"},
        "typography": {
            "state": "STRUCTURAL_PASS_IDENTITY_BLOCKED" if all(v["pass"] for v in role_results.values()) else "FAIL",
            "exact_font_identity": "UNKNOWN",
            "glyph_morphology_authority": "BLOCKED_WITHOUT_FONT_OR_RASTER_GLYPH_SOURCE",
        },
        "motion": {
            "state": "PASS_CAPTION_TRAJECTORIES_ONLY" if all(v["pass"] for v in role_results.values()) else "FAIL",
            "subject_reframe": "NOT_QUALIFIED_WITHOUT_CLEAN_LAYER",
        },
        "camera": {"state": "BLOCKED_SOURCE_LAYER_LIMIT"},
        "depth": {"state": "SOURCE_NATIVE_PLATE_UNQUALIFIED"},
        "color": {"state": "P2_VISIBLE_OUTPUT_PROXY_ONLY"},
        "fx": {"state": "PARTIAL_BLOCKED_ORIGINAL_EFFECT_STACK_UNKNOWN"},
        "audio": {
            "state": "PASS_TIMING_IDENTITY_BLOCKED" if audio_timing_pass else "FAIL_TIMING",
            "onset_error_frames": onset_error,
            "sfx_identity": "INFERRED_FROM_MIXED_AUDIO",
        },
        "retention": {
            "state": "PASS_MODELED_EDITORIAL_BEATS" if p0_p1_closed else "PARTIAL",
            "scope": "modeled S04 editorial caption/audio beats only",
        },
    }

    return {
        "schema_version": "motion-os.s04-qualification-v2/1.0.0",
        "scene_id": "S04_CIENTIFICAMENTE",
        "source": source,
        "renderer": {
            "renderer": "remotion",
            "head_sha": renderer_head,
            "artifact_id": artifact_id,
            "artifact_digest": artifact_digest,
        },
        "thresholds": THRESHOLDS,
        "role_results": role_results,
        "audio_timing_pass": audio_timing_pass,
        "p0_p1_measured_repair_closed": p0_p1_closed,
        "dimensions": dimensions,
        "full_9d_fidelity_validated": False,
        "authority_state": (
            "SOURCE_BOUND_PARTIAL_QUALIFICATION_P0P1_CLOSED"
            if p0_p1_closed
            else "SOURCE_BOUND_DEFECTS_REMAIN"
        ),
        "promotion_ceiling": "EMPIRICAL_PARTIAL_ONLY_NOT_CANONICAL_TEMPLATE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--measurement", type=Path, required=True)
    parser.add_argument("--renderer-head", required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    measurement = json.loads(args.measurement.read_text(encoding="utf-8"))
    result = build_qualification(
        measurement,
        renderer_head=args.renderer_head,
        artifact_id=args.artifact_id,
        artifact_digest=args.artifact_digest,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["p0_p1_measured_repair_closed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
