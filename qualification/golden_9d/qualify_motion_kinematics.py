#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def qualify(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("schema_version") != "motion-os.golden-motion-kinematics/v3":
        raise ValueError("unsupported motion kinematics artifact")
    if data.get("authority") != "DERIVED_FROM_PINNED_SOURCE_BOUND_TRACKS":
        raise ValueError("kinematics artifact lacks pinned-source authority")

    scene_results: dict[str, Any] = {}
    for scene_id, scene in data["scenes"].items():
        projection = scene["projection_mode"]
        entities = scene["entities"]
        if not entities:
            raise ValueError(f"scene has no kinematic entities: {scene_id}")

        transform_classes = Counter()
        clipped_segments = 0
        excluded_segments = 0
        eligible_translation_segments = 0
        low_confidence_curves = 0
        micro_candidates = 0
        total_samples = 0

        for entity in entities.values():
            if not entity.get("visible"):
                continue
            total_samples += int(entity["sample_count"])
            for sample in entity["samples"]:
                speed = sample.get("speed_px_per_frame")
                if speed is not None and 0.45 < float(speed) <= 1.5:
                    micro_candidates += 1
            for segment in entity["motion_segments"]:
                transform_classes[segment["dominant_transform_class"]] += 1
                if segment["screen_boundary_clipped"]:
                    clipped_segments += 1
                if not segment["structural_template_eligible"]:
                    excluded_segments += 1
                if (
                    segment["dominant_transform_class"] == "TRANSLATION_DOMINANT"
                    and not segment["screen_boundary_clipped"]
                    and segment["structural_template_eligible"]
                ):
                    eligible_translation_segments += 1
                if segment["curve_proxy_confidence"] in {"LOW", "NONE"}:
                    low_confidence_curves += 1

        keyframe_projection = projection.startswith("KEYFRAME_LINEAR")
        exact_blockers = [
            "original After Effects Graph Editor/easing curve is not directly observed",
            "bbox motion does not by itself identify transform-vs-mask-vs-asset-internal animation",
        ]
        structural_blockers = [
            "micro-motion candidates require optical-flow corroboration before becoming reusable grammar",
        ]
        if keyframe_projection:
            exact_blockers.append("speed profile is shaped by sparse-keyframe linear renderer projection")
            structural_blockers.append("easing family remains LOW authority under keyframe-linear projection")
        if clipped_segments:
            exact_blockers.append("screen/scene-boundary clipping hides part of the underlying object trajectory")
            structural_blockers.append("clipped bbox segments encode visible output, not hidden-object easing")
        if transform_classes["SCALE_OR_REVEAL_DOMINANT"] or transform_classes["MIXED_TRANSLATION_AND_SCALE"]:
            exact_blockers.append("material bbox shape/reveal changes prevent pure-translation inference on some segments")
        if excluded_segments:
            structural_blockers.append("SOURCE_LOCK ranges are intentionally excluded from reusable motion grammar")

        easing_state = "BLOCKED"
        if not keyframe_projection and eligible_translation_segments > 0:
            easing_state = "PARTIAL"

        scene_results[scene_id] = {
            "source_ref": scene["source_ref"],
            "projection_mode": projection,
            "visible_bbox_kinematics": {
                "state": "QUALIFIED",
                "authority": "QUALIFIED_TO_PINNED_SOURCE_TRACK_RESOLUTION",
                "sample_count": total_samples,
                "transform_class_counts": dict(sorted(transform_classes.items())),
                "clipped_segment_count": clipped_segments,
                "source_lock_excluded_segment_count": excluded_segments,
            },
            "micro_motion": {
                "state": "UNRESOLVED_PENDING_OPTICAL_FLOW" if micro_candidates else "NO_CANDIDATE_AT_CURRENT_THRESHOLD",
                "candidate_step_count": micro_candidates,
                "threshold_note": "0.45 < bbox centroid speed <= 1.5 px/frame is preserved as a candidate, not promoted as editorial motion.",
            },
            "easing_behavior": {
                "state": easing_state,
                "eligible_unclipped_translation_segment_count": eligible_translation_segments,
                "low_confidence_curve_count": low_confidence_curves,
                "authority": "BEHAVIORAL_PROXY_NOT_ORIGINAL_GRAPH_EDITOR",
            },
            "reconstruct_exact_motion": {
                "state": "PARTIAL",
                "qualified_aspects": ["source-visible bbox trajectory at pinned track resolution", "timing/order of measured motion states"],
                "blocked_aspects": sorted(set(exact_blockers)),
            },
            "structural_template_motion": {
                "state": "PARTIAL",
                "qualified_aspects": ["visible trajectory grammar", "transform-vs-reveal decomposition", "SOURCE_LOCK exclusion policy"],
                "blocked_aspects": sorted(set(structural_blockers)),
            },
        }

    return {
        "schema_version": "motion-os.golden-motion-qualification/v1",
        "authority": "DERIVED_DIMENSION_QUALIFICATION",
        "scene_results": scene_results,
        "cross_golden": {
            "visible_bbox_kinematics": "QUALIFIED_ACROSS_ALL_FOUR_AT_THEIR_PINNED_TRACK_RESOLUTION",
            "reconstruct_exact_motion": "PARTIAL",
            "structural_template_motion": "PARTIAL",
            "original_easing_graph": "BLOCKED",
            "micro_motion": "PENDING_T08_W2_OPTICAL_FLOW_CORROBORATION",
        },
        "w1_state": "COMPLETE_WITH_RESIDUAL_MOTION_AUTHORITY_BLOCKERS",
        "promotion_law": "W1 completion means the motion evidence and its uncertainty are compiled; it does not mean the 9D motion dimension is fully QUALIFIED.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kinematics", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = qualify(json.loads(args.kinematics.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "w1_state": result["w1_state"],
        "scene_count": len(result["scene_results"]),
        "cross_golden": result["cross_golden"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
