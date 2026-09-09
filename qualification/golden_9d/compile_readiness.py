#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

DIMENSIONS = ("temporal", "motion", "camera", "typography", "depth", "color", "fx", "audio", "retention")
MODES = ("reconstruct_exact", "structural_template")
STATES = {"QUALIFIED", "PARTIAL", "BLOCKED", "UNKNOWN", "NOT_APPLICABLE"}


def compile_readiness(matrix: dict) -> dict:
    if matrix.get("schema_version") != "motion-os.golden-9d-matrix/v1":
        raise ValueError("unsupported golden 9D matrix schema")
    if tuple(matrix.get("dimensions", ())) != DIMENSIONS:
        raise ValueError("dimension order/coverage drift")

    scenes = matrix.get("scenes", {})
    if set(scenes) != {"S04_CIENTIFICAMENTE", "S11_UI_LIST", "S14_AUDIO_VISUAL_TEXTO", "S16_FACTOR_X"}:
        raise ValueError("golden scene set drift")

    by_mode: dict[str, dict] = {}
    for mode in MODES:
        counts = Counter()
        dimension_states: dict[str, list[dict]] = defaultdict(list)
        for scene_id, scene in scenes.items():
            head = scene.get("head_sha", "")
            if len(head) != 40 or any(c not in "0123456789abcdef" for c in head):
                raise ValueError(f"invalid head SHA for {scene_id}")
            ci = scene.get("ci", {})
            if ci.get("remotion_result") != "SUCCESS" or ci.get("merge_safe_result") != "SUCCESS":
                raise ValueError(f"live exact-head CI is not green for {scene_id}")
            for dimension in DIMENSIONS:
                q = scene["dimensions"][dimension][mode]
                state = q["state"]
                if state not in STATES:
                    raise ValueError(f"unknown state {scene_id}/{dimension}/{mode}: {state}")
                if state == "QUALIFIED" and not q.get("evidence_refs"):
                    raise ValueError(f"qualified state lacks evidence: {scene_id}/{dimension}/{mode}")
                if state == "QUALIFIED" and q.get("blocked_aspects"):
                    raise ValueError(f"qualified state still declares blockers: {scene_id}/{dimension}/{mode}")
                counts[state] += 1
                dimension_states[dimension].append({"scene": scene_id, "state": state})

        hard_blocked = {
            dim: rows
            for dim, rows in dimension_states.items()
            if any(row["state"] in {"BLOCKED", "UNKNOWN"} for row in rows)
        }
        incomplete = {
            dim: rows
            for dim, rows in dimension_states.items()
            if any(row["state"] != "QUALIFIED" for row in rows)
        }
        all_qualified = not incomplete
        by_mode[mode] = {
            "state_counts": dict(sorted(counts.items())),
            "dimension_rows": dict(dimension_states),
            "hard_blocked_dimensions": hard_blocked,
            "incomplete_dimensions": incomplete,
            "all_9d_qualified": all_qualified,
        }

    barrier = bool(matrix.get("barriers", {}).get("issue_48_open"))
    return {
        "schema_version": "motion-os.golden-9d-readiness/v1",
        "authority": "DERIVED_FAIL_CLOSED_READ_MODEL",
        "modes": by_mode,
        "promotion": {
            "issue_48_open": barrier,
            "reconstruct_exact_9d": by_mode["reconstruct_exact"]["all_9d_qualified"],
            "structural_template_9d": by_mode["structural_template"]["all_9d_qualified"],
            "canonical_template_eligible": (
                not barrier
                and by_mode["structural_template"]["all_9d_qualified"]
                and bool(matrix.get("promotion", {}).get("cross_renderer_parity_validated"))
                and bool(matrix.get("promotion", {}).get("empirically_generalized"))
            ),
        },
        "law": "No weighted or averaged score grants authority. Every required dimension must independently pass and global barriers must be closed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    readiness = compile_readiness(json.loads(args.matrix.read_text()))
    payload = json.dumps(readiness, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
