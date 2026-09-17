from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json


class ActionInventoryError(ValueError):
    pass


RENDERERS = ("after_effects", "remotion", "hyperframes")


@dataclass(frozen=True, slots=True)
class PeakCoverage:
    frame: int
    action_ids: tuple[str, ...]

    @property
    def covered(self) -> bool:
        return bool(self.action_ids)


@dataclass(frozen=True, slots=True)
class PeakAdjudication:
    frame: int
    status: str
    action_ids: tuple[str, ...]
    nearest_anchor_distance: int | None
    reason: str


def load_action_inventory(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_action_inventory(
    inventory: Mapping[str, Any],
    *,
    schema_path: str | Path = "schemas/reverse_engineering_action_inventory.schema.json",
) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("jsonschema is required to validate reverse-engineering action inventories") from exc
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    jsonschema.validate(instance=dict(inventory), schema=schema)

    scenes = {str(scene["scene_id"]): scene for scene in inventory["scenes"]}
    if len(scenes) != len(inventory["scenes"]):
        raise ActionInventoryError("scene ids must be unique")
    actions = list(inventory["actions"])
    action_ids = [str(action["action_id"]) for action in actions]
    if len(set(action_ids)) != len(action_ids):
        raise ActionInventoryError("action ids must be unique")

    ordered = sorted(scenes.values(), key=lambda item: int(item["start_frame"]))
    for index, scene in enumerate(ordered):
        start, end = int(scene["start_frame"]), int(scene["end_frame"])
        if start >= end:
            raise ActionInventoryError(f"invalid scene range: {scene['scene_id']}")
        if index and int(ordered[index - 1]["end_frame"]) != start:
            raise ActionInventoryError("scene ranges must be contiguous")

    per_scene = {scene_id: 0 for scene_id in scenes}
    subevent_ids: set[str] = set()
    for action in actions:
        scene_id = str(action["scene_id"])
        if scene_id not in scenes:
            raise ActionInventoryError(f"action references unknown scene: {scene_id}")
        scene = scenes[scene_id]
        start, impact, end = (int(action[key]) for key in ("start_frame", "impact_frame", "end_frame"))
        if not (int(scene["start_frame"]) <= start <= impact <= end <= int(scene["end_frame"])):
            raise ActionInventoryError(f"action {action['action_id']} exceeds scene or has invalid timing")
        mapping = action.get("renderer_mapping", {})
        missing = [renderer for renderer in RENDERERS if not str(mapping.get(renderer, "")).strip()]
        if missing:
            raise ActionInventoryError(f"action {action['action_id']} missing renderer mappings: {missing}")
        if not action.get("evidence_refs"):
            raise ActionInventoryError(f"action {action['action_id']} has no evidence_refs")

        subevents = list(action.get("subevents", []))
        if action.get("temporal_mode") == "staggered" and not subevents:
            raise ActionInventoryError(f"staggered action {action['action_id']} requires explicit subevents")
        for subevent in subevents:
            subevent_id = str(subevent["subevent_id"])
            if subevent_id in subevent_ids:
                raise ActionInventoryError(f"duplicate subevent_id: {subevent_id}")
            subevent_ids.add(subevent_id)
            sub_start, sub_impact, sub_end = (
                int(subevent[key]) for key in ("start_frame", "impact_frame", "end_frame")
            )
            if not (start <= sub_start <= sub_impact <= sub_end <= end):
                raise ActionInventoryError(
                    f"subevent {subevent_id} exceeds parent action {action['action_id']} or has invalid timing"
                )
            if not subevent.get("evidence_refs"):
                raise ActionInventoryError(f"subevent {subevent_id} has no evidence_refs")
        per_scene[scene_id] += 1
    empty = [scene_id for scene_id, count in per_scene.items() if count == 0]
    if empty:
        raise ActionInventoryError(f"scenes without operations: {empty}")


def actions_covering_frame(inventory: Mapping[str, Any], frame: int) -> tuple[str, ...]:
    return tuple(
        str(action["action_id"])
        for action in inventory["actions"]
        if int(action["start_frame"]) <= frame <= int(action["end_frame"])
    )


def peak_coverage(inventory: Mapping[str, Any], peaks: Sequence[int]) -> tuple[PeakCoverage, ...]:
    return tuple(PeakCoverage(int(frame), actions_covering_frame(inventory, int(frame))) for frame in peaks)


def _action_anchors(action: Mapping[str, Any]) -> list[int]:
    anchors = [int(action[key]) for key in ("start_frame", "impact_frame", "end_frame")]
    for subevent in action.get("subevents", []):
        anchors.extend(int(subevent[key]) for key in ("start_frame", "impact_frame", "end_frame"))
    return sorted(set(anchors))


def adjudicate_peak(inventory: Mapping[str, Any], frame: int, *, tolerance_frames: int = 5) -> PeakAdjudication:
    candidates = [
        action for action in inventory["actions"]
        if int(action["start_frame"]) <= frame <= int(action["end_frame"])
    ]
    ids = tuple(str(action["action_id"]) for action in candidates)
    if not candidates:
        return PeakAdjudication(frame, "unexplained", ids, None, "no action covers frame")

    anchors = [(abs(anchor - frame), action) for action in candidates for anchor in _action_anchors(action)]
    nearest = min((distance for distance, _ in anchors), default=None)
    if nearest is not None and nearest <= tolerance_frames:
        return PeakAdjudication(frame, "anchored", ids, nearest, "near action/subevent keyframe")

    continuous = [action for action in candidates if action.get("temporal_mode") == "continuous"]
    if continuous:
        return PeakAdjudication(
            frame, "continuous", tuple(str(action["action_id"]) for action in continuous), nearest,
            "inside deterministic continuous action window",
        )

    native = [
        action for action in candidates
        if action.get("motion_origin") == "source_native"
        or bool(action.get("parameters", {}).get("source_native_motion_allowed"))
    ]
    if native:
        return PeakAdjudication(
            frame, "source_native", tuple(str(action["action_id"]) for action in native), nearest,
            "visible change adjudicated as source-native motion, not an editing operation",
        )

    return PeakAdjudication(frame, "unexplained", ids, nearest, "covered by broad action window but not anchored")


def detect_local_peaks(values: Sequence[float], *, percentile: float = 90.0, min_separation: int = 4) -> list[int]:
    if not values:
        return []
    ordered = sorted(float(value) for value in values)
    rank = min(len(ordered) - 1, max(0, int(round((percentile / 100.0) * (len(ordered) - 1)))))
    threshold = ordered[rank]
    peaks: list[int] = []
    for index in range(1, len(values) - 1):
        value = float(values[index])
        if value < threshold or value < float(values[index - 1]) or value < float(values[index + 1]):
            continue
        if peaks and index - peaks[-1] < min_separation:
            if value > float(values[peaks[-1]]):
                peaks[-1] = index
            continue
        peaks.append(index)
    return peaks


def _adjudication_block(
    inventory: Mapping[str, Any], values: Sequence[float], *, percentile: float, tolerance_frames: int
) -> dict[str, Any]:
    peaks = detect_local_peaks(values, percentile=percentile)
    rows = [adjudicate_peak(inventory, frame, tolerance_frames=tolerance_frames) for frame in peaks]
    unexplained = [row.frame for row in rows if row.status == "unexplained"]
    return {
        "percentile": percentile,
        "peak_count": len(rows),
        "coverage": 1.0 if not unexplained else 1.0 - len(unexplained) / max(1, len(rows)),
        "unexplained_frames": unexplained,
        "peaks": [
            {
                "frame": row.frame,
                "status": row.status,
                "action_ids": list(row.action_ids),
                "nearest_anchor_distance": row.nearest_anchor_distance,
                "reason": row.reason,
            }
            for row in rows
        ],
    }


def gauntlet_coverage_from_frame_metrics(inventory: Mapping[str, Any], frame_metrics: Mapping[str, Any]) -> dict[str, Any]:
    frames = list(frame_metrics.get("frames", []))
    mad = [float(item.get("mad", 0.0)) for item in frames]
    flow = [float(item.get("flow_p90", 0.0)) for item in frames]
    mad_peaks = detect_local_peaks(mad, percentile=90.0)
    flow_peaks = detect_local_peaks(flow, percentile=90.0)
    mad_cov = peak_coverage(inventory, mad_peaks)
    flow_cov = peak_coverage(inventory, flow_peaks)
    uncovered_mad = [item.frame for item in mad_cov if not item.covered]
    uncovered_flow = [item.frame for item in flow_cov if not item.covered]
    deep = {
        "mad_p80": _adjudication_block(inventory, mad, percentile=80.0, tolerance_frames=5),
        "mad_p75": _adjudication_block(inventory, mad, percentile=75.0, tolerance_frames=5),
        "flow_p80": _adjudication_block(inventory, flow, percentile=80.0, tolerance_frames=5),
        "flow_p75": _adjudication_block(inventory, flow, percentile=75.0, tolerance_frames=5),
    }
    deep_unexplained = sorted({frame for block in deep.values() for frame in block["unexplained_frames"]})
    return {
        "schema_version": "1.1.0",
        "scene_coverage": 1.0,
        "action_count": len(inventory["actions"]),
        "mad_p90_peaks": [{"frame": item.frame, "action_ids": list(item.action_ids)} for item in mad_cov],
        "flow_p90_peaks": [{"frame": item.frame, "action_ids": list(item.action_ids)} for item in flow_cov],
        "mad_p90_coverage": 1.0 if not uncovered_mad else 1.0 - len(uncovered_mad) / max(1, len(mad_cov)),
        "flow_p90_coverage": 1.0 if not uncovered_flow else 1.0 - len(uncovered_flow) / max(1, len(flow_cov)),
        "uncovered_mad_frames": uncovered_mad,
        "uncovered_flow_frames": uncovered_flow,
        "deep_residual_review": deep,
        "deep_unexplained_frames": deep_unexplained,
        "observable_action_closed": not uncovered_mad and not uncovered_flow and not deep_unexplained,
    }
