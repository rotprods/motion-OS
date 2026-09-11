#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

SCENES = {
    "S04_CIENTIFICAMENTE",
    "S11_UI_LIST",
    "S14_AUDIO_VISUAL_TEXTO",
    "S16_FACTOR_X",
}
STATES = {"QUALIFIED", "PARTIAL", "BLOCKED", "UNKNOWN", "NOT_APPLICABLE"}
CANONICAL_SOURCE_SHA = "9b3076cb542e358386942a0fb6b160f1345564d4326738f9a340e2b5b38e199d"
MICRO_CLASSES = {
    "CORROBORATED_DIRECTIONAL_PIXEL_FLOW",
    "PIXEL_ACTIVITY_DIRECTION_UNCERTAIN",
    "PIXEL_ACTIVITY_VISIBLE_CHANGE_ONLY_NO_TRANSLATION_PROMOTION",
    "NOT_CORROBORATED_ABOVE_BACKGROUND",
    "SOURCE_LOCK_EXCLUDED",
}


def _hex40(value: str) -> bool:
    return len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def _validate_depth(scene_id: str, depth: dict[str, Any]) -> dict[str, Any]:
    edges = depth.get("edges", [])
    unknowns = depth.get("unknown_relations", [])
    graph: dict[str, set[str]] = defaultdict(set)
    indegree: Counter[str] = Counter()
    nodes: set[str] = set()

    for edge in edges:
        front, behind = edge.get("front"), edge.get("behind")
        if not front or not behind or front == behind:
            raise ValueError(f"invalid depth edge for {scene_id}: {edge}")
        if behind in graph[front]:
            raise ValueError(f"duplicate depth edge for {scene_id}: {front}>{behind}")
        graph[front].add(behind)
        indegree[behind] += 1
        indegree.setdefault(front, 0)
        nodes.update((front, behind))
        if not edge.get("authority"):
            raise ValueError(f"depth edge lacks authority for {scene_id}: {front}>{behind}")

    for rel in unknowns:
        pair = rel.get("pair", [])
        if len(pair) != 2 or not rel.get("reason"):
            raise ValueError(f"invalid UNKNOWN depth relation for {scene_id}: {rel}")
        a, b = pair
        if b in graph.get(a, set()) or a in graph.get(b, set()):
            raise ValueError(f"UNKNOWN depth relation was laundered into an edge for {scene_id}: {a}<->{b}")
        nodes.update((a, b))

    q = deque(sorted(n for n in nodes if indegree[n] == 0))
    visited = 0
    work = Counter(indegree)
    while q:
        node = q.popleft()
        visited += 1
        for nxt in sorted(graph.get(node, ())):
            work[nxt] -= 1
            if work[nxt] == 0:
                q.append(nxt)
    if visited != len(nodes):
        raise ValueError(f"cycle in depth partial order for {scene_id}")

    for mode_key in ("reconstruct_exact_state", "structural_template_state"):
        if depth.get(mode_key) not in STATES:
            raise ValueError(f"invalid depth state for {scene_id}/{mode_key}")

    return {
        "edge_count": len(edges),
        "unknown_relation_count": len(unknowns),
        "acyclic": True,
        "nodes": sorted(nodes),
    }


def _validate_micro(data: dict[str, Any]) -> dict[str, Any]:
    cross = data["micro_motion_cross_golden"]
    if int(cross.get("candidate_count", -1)) != 220:
        raise ValueError("W1 micro-motion candidate universe drifted from 220")
    if cross.get("promotion") != "PARTIAL_MOTION_AUTHORITY_ONLY":
        raise ValueError("micro-motion evidence self-promoted beyond partial authority")

    scene_candidate_total = 0
    agg = Counter()
    for scene_id, scene in data["scenes"].items():
        mm = scene["micro_motion"]
        classes = mm.get("classes", {})
        unknown_classes = set(classes) - MICRO_CLASSES
        if unknown_classes:
            raise ValueError(f"unknown micro-motion class for {scene_id}: {sorted(unknown_classes)}")
        candidate_count = int(mm.get("candidate_count", -1))
        if sum(int(v) for v in classes.values()) != candidate_count:
            raise ValueError(f"micro-motion partition mismatch for {scene_id}")
        scene_candidate_total += candidate_count
        agg.update({k: int(v) for k, v in classes.items()})

    if scene_candidate_total != 220:
        raise ValueError("scene micro-motion counts do not sum to 220")

    directional = agg["CORROBORATED_DIRECTIONAL_PIXEL_FLOW"]
    activity_only = agg["PIXEL_ACTIVITY_DIRECTION_UNCERTAIN"] + agg[
        "PIXEL_ACTIVITY_VISIBLE_CHANGE_ONLY_NO_TRANSLATION_PROMOTION"
    ]
    not_corroborated = agg["NOT_CORROBORATED_ABOVE_BACKGROUND"]
    source_lock = agg["SOURCE_LOCK_EXCLUDED"]

    expected = {
        "corroborated_directional_pixel_flow": directional,
        "pixel_activity_no_translation_promotion": activity_only,
        "not_corroborated_above_background": not_corroborated,
        "source_lock_excluded": source_lock,
    }
    for key, value in expected.items():
        if int(cross.get(key, -1)) != value:
            raise ValueError(f"cross-golden micro-motion aggregate mismatch: {key}")

    if directional + activity_only + not_corroborated + source_lock != 220:
        raise ValueError("micro-motion aggregate is not a closed partition")

    return {
        "candidate_count": 220,
        "directional_corroborated": directional,
        "activity_without_translation_authority": activity_only,
        "not_corroborated": not_corroborated,
        "source_lock_excluded": source_lock,
    }


def _validate_camera(scene_id: str, scene: dict[str, Any]) -> dict[str, Any]:
    cam = scene["camera"]
    flow = scene["flow_summary"]
    for state_key in ("reconstruct_exact_state", "structural_template_state"):
        if cam.get(state_key) not in STATES:
            raise ValueError(f"invalid camera state for {scene_id}/{state_key}")

    bg_vec = float(flow.get("background_abs_vector_median", 999.0))
    klass = cam.get("observable_class", "")
    global_state = cam.get("global_frame_state", "")

    if "STATIC" in klass or "STATIC" in global_state:
        if bg_vec > 0.05:
            raise ValueError(f"static camera/canvas claim contradicts common background vector for {scene_id}: {bg_vec}")

    forbidden = ("PHYSICAL_CAMERA", "ORIGINAL_CAMERA", "CAMERA_TRANSLATION_PROVEN")
    text = json.dumps(cam, sort_keys=True)
    if any(token in text for token in forbidden):
        raise ValueError(f"unsupported physical camera authority in {scene_id}")

    if scene_id == "S04_CIENTIFICAMENTE":
        if cam.get("historical_action_A026") != "NOT_PROMOTED_TO_GLOBAL_CAMERA_AUTHORITY":
            raise ValueError("S04 A026 historical reframe was promoted without causal evidence")
    if scene_id == "S11_UI_LIST":
        if cam.get("group_lift_hypothesis") != "SUPPORTED_AS_FOREGROUND_GROUP_MOTION_NOT_CAMERA":
            raise ValueError("S11 group lift must remain foreground-group authority")
    if scene_id == "S14_AUDIO_VISUAL_TEXTO":
        if cam.get("shared_parent_hypothesis") != "SUPPORTED_AS_FOREGROUND_CAROUSEL_GROUP_NOT_CAMERA":
            raise ValueError("S14 carousel parent was laundered into camera authority")
    if scene_id == "S16_FACTOR_X":
        if cam.get("late_reflow_policy") != "SOURCE_LOCK_UNLESS_INDEPENDENTLY_PROVEN_EDITORIAL":
            raise ValueError("S16 late reflow lost SOURCE_LOCK policy")
        cal = cam.get("historical_calibration", {})
        if cal.get("late_common_overlay_dy_px") != [-4, -4, -4, -4, -2]:
            raise ValueError("S16 known late-reflow calibration drift")
        if int(cal.get("late_cumulative_dy_px", 0)) != -18:
            raise ValueError("S16 cumulative reflow calibration drift")

    return {
        "observable_class": klass,
        "background_common_vector_median_px": bg_vec,
        "reconstruct_exact_state": cam["reconstruct_exact_state"],
        "structural_template_state": cam["structural_template_state"],
    }


def compile_camera_depth(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("schema_version") != "motion-os.golden-w2-camera-depth-evidence/v1":
        raise ValueError("unsupported W2 camera/depth evidence schema")
    if data.get("authority") != "DERIVED_FROM_PHYSICAL_SOURCE_PIXEL_FLOW_AND_PINNED_SCENE_CONTRACTS":
        raise ValueError("W2 evidence lacks the required physical/source-bound authority chain")

    source = data.get("source_video", {})
    if source.get("sha256") != CANONICAL_SOURCE_SHA:
        raise ValueError("canonical source video SHA drift")
    if (source.get("fps"), source.get("width"), source.get("height")) != (30, 512, 1108):
        raise ValueError("canonical source media geometry drift")

    scenes = data.get("scenes", {})
    if set(scenes) != SCENES:
        raise ValueError("W2 golden scene set drift")
    refs = [scene.get("source_ref", "") for scene in scenes.values()]
    if any(not _hex40(ref) for ref in refs) or len(set(refs)) != 4:
        raise ValueError("W2 scene refs must be four unique exact commit SHAs")

    evidence = data.get("full_evidence", {})
    for name in ("optical_flow_baseline", "micro_motion_corroboration", "w1_motion_kinematics"):
        item = evidence.get(name, {})
        if not item.get("drive_id") or len(item.get("sha256", "")) != 64:
            raise ValueError(f"durable evidence pointer/hash missing: {name}")

    micro = _validate_micro(data)
    scene_results: dict[str, Any] = {}
    for scene_id in sorted(SCENES):
        scene = scenes[scene_id]
        scene_results[scene_id] = {
            "camera": _validate_camera(scene_id, scene),
            "depth": _validate_depth(scene_id, scene["depth"]),
            "micro_motion": {
                "candidate_count": scene["micro_motion"]["candidate_count"],
                "classes": scene["micro_motion"]["classes"],
            },
        }

    structural_camera_all = all(
        row["camera"]["structural_template_state"] == "QUALIFIED"
        for row in scene_results.values()
    )
    structural_depth_all = all(
        scenes[sid]["depth"]["structural_template_state"] == "QUALIFIED"
        for sid in SCENES
    )

    return {
        "schema_version": "motion-os.golden-w2-camera-depth-qualification/v1",
        "authority": "DERIVED_FAIL_CLOSED_W2_QUALIFICATION",
        "scene_results": scene_results,
        "micro_motion": micro,
        "cross_golden": {
            "camera_reconstruct_exact": "PARTIAL",
            "camera_structural_template": "QUALIFIED_ACROSS_ALL" if structural_camera_all else "PARTIAL",
            "depth_reconstruct_exact": "PARTIAL",
            "depth_structural_template": "QUALIFIED_ACROSS_ALL" if structural_depth_all else "PARTIAL",
            "original_camera_or_ae_parenting": "BLOCKED_OR_UNKNOWN",
            "source_lock_reflows": "EXCLUDED_FROM_STRUCTURAL_CAMERA_GRAMMAR",
        },
        "w2_state": "COMPLETE_WITH_EXPLICIT_CAUSAL_AND_DEPTH_UNKNOWNS",
        "promotion_law": (
            "W2 completion means camera/background/group-motion evidence and depth partial orders are executable and uncertainty-preserving; "
            "it does not prove original camera, AE parenting, full depth, or full 9D fidelity."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    result = compile_camera_depth(json.loads(args.evidence.read_text()))
    payload = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
