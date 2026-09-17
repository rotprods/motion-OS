from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import math


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


def _frame_index(raw: object, *, name: str) -> int:
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise ActionInventoryError(f"{name} must be an integer frame index")
    if raw < 0:
        raise ActionInventoryError(f"{name} must be non-negative")
    return raw


def _finite_nonnegative(raw: object, *, name: str) -> float:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ActionInventoryError(f"{name} must be a finite non-negative number")
    value = float(raw)
    if not math.isfinite(value) or value < 0:
        raise ActionInventoryError(f"{name} must be a finite non-negative number")
    return value


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

    ordered = sorted(scenes.values(), key=lambda item: _frame_index(item["start_frame"], name="scene.start_frame"))
    if not ordered or _frame_index(ordered[0]["start_frame"], name="scene.start_frame") != 0:
        raise ActionInventoryError("scene coverage must start at frame 0")
    for index, scene in enumerate(ordered):
        start = _frame_index(scene["start_frame"], name="scene.start_frame")
        end = _frame_index(scene["end_frame"], name="scene.end_frame")
        if start >= end:
            raise ActionInventoryError(f"invalid scene range: {scene['scene_id']}")
        if index and _frame_index(ordered[index - 1]["end_frame"], name="scene.end_frame") != start:
            raise ActionInventoryError("scene ranges must be contiguous")

    per_scene = {scene_id: 0 for scene_id in scenes}
    subevent_ids: set[str] = set()
    for action in actions:
        scene_id = str(action["scene_id"])
        if scene_id not in scenes:
            raise ActionInventoryError(f"action references unknown scene: {scene_id}")
        scene = scenes[scene_id]
        start = _frame_index(action["start_frame"], name="action.start_frame")
        impact = _frame_index(action["impact_frame"], name="action.impact_frame")
        end = _frame_index(action["end_frame"], name="action.end_frame")
        scene_start = _frame_index(scene["start_frame"], name="scene.start_frame")
        scene_end = _frame_index(scene["end_frame"], name="scene.end_frame")
        if not (scene_start <= start <= impact <= end < scene_end):
            raise ActionInventoryError(f"action {action['action_id']} exceeds scene or has invalid timing")
        mapping = action.get("renderer_mapping", {})
        missing = [renderer for renderer in RENDERERS if not str(mapping.get(renderer, "")).strip()]
        if missing:
            raise ActionInventoryError(f"action {action['action_id']} missing renderer mappings: {missing}")
        if not action.get("evidence_refs"):
            raise ActionInventoryError(f"action {action['action_id']} has no evidence_refs")

        confidence = action.get("confidence")
        if confidence is not None and not 0.0 <= _finite_nonnegative(confidence, name="action.confidence") <= 1.0:
            raise ActionInventoryError(f"action {action['action_id']} confidence must be between 0 and 1")

        subevents = list(action.get("subevents", []))
        if action.get("temporal_mode") == "staggered" and not subevents:
            raise ActionInventoryError(f"staggered action {action['action_id']} requires explicit subevents")
        for subevent in subevents:
            subevent_id = str(subevent["subevent_id"])
            if subevent_id in subevent_ids:
                raise ActionInventoryError(f"duplicate subevent_id: {subevent_id}")
            subevent_ids.add(subevent_id)
            sub_start = _frame_index(subevent["start_frame"], name="subevent.start_frame")
            sub_impact = _frame_index(subevent["impact_frame"], name="subevent.impact_frame")
            sub_end = _frame_index(subevent["end_frame"], name="subevent.end_frame")
            if not (start <= sub_start <= sub_impact <= sub_end <= end):
                raise ActionInventoryError(
                    f"subevent {subevent_id} exceeds parent action {action['action_id']} or has invalid timing"
                )
            sub_confidence = subevent.get("confidence")
            if sub_confidence is not None and not 0.0 <= _finite_nonnegative(sub_confidence, name="subevent.confidence") <= 1.0:
                raise ActionInventoryError(f"subevent {subevent_id} confidence must be between 0 and 1")
            if not subevent.get("evidence_refs"):
                raise ActionInventoryError(f"subevent {subevent_id} has no evidence_refs")
        per_scene[scene_id] += 1
    empty = [scene_id for scene_id, count in per_scene.items() if count == 0]
    if empty:
        raise ActionInventoryError(f"scenes without operations: {empty}")


def actions_covering_frame(inventory: Mapping[str, Any], frame: int) -> tuple[str, ...]:
    frame = _frame_index(frame, name="frame")
    return tuple(
        str(action["action_id"])
        for action in inventory["actions"]
        if int(action["start_frame"]) <= frame <= int(action["end_frame"])
    )


def peak_coverage(inventory: Mapping[str, Any], peaks: Sequence[int]) -> tuple[PeakCoverage, ...]:
    return tuple(PeakCoverage(_frame_index(frame, name="peak.frame"), actions_covering_frame(inventory, frame)) for frame in peaks)


def _action_anchors(action: Mapping[str, Any]) -> list[int]:
    anchors = [int(action[key]) for key in ("start_frame", "impact_frame", "end_frame")]
    for subevent in action.get("subevents", []):
        anchors.extend(int(subevent[key]) for key in ("start_frame", "impact_frame", "end_frame"))
    return sorted(set(anchors))


def adjudicate_peak(inventory: Mapping[str, Any], frame: int, *, tolerance_frames: int = 5) -> PeakAdjudication:
    frame = _frame_index(frame, name="frame")
    if isinstance(tolerance_frames, bool) or not isinstance(tolerance_frames, int) or tolerance_frames < 0:
        raise ActionInventoryError("tolerance_frames must be a non-negative integer")
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
    if isinstance(percentile, bool) or not isinstance(percentile, (int, float)) or not math.isfinite(float(percentile)) or not 0 <= float(percentile) <= 100:
        raise ActionInventoryError("percentile must be finite and between 0 and 100")
    if isinstance(min_separation, bool) or not isinstance(min_separation, int) or min_separation < 1:
        raise ActionInventoryError("min_separation must be a positive integer")
    normalized = [_finite_nonnegative(value, name="peak metric") for value in values]
    ordered = sorted(normalized)
    rank = min(len(ordered) - 1, max(0, int(round((float(percentile) / 100.0) * (len(ordered) - 1)))))
    threshold = ordered[rank]
    peaks: list[int] = []
    for index in range(1, len(normalized) - 1):
        value = normalized[index]
        if value < threshold or value < normalized[index - 1] or value < normalized[index + 1]:
            continue
        if peaks and index - peaks[-1] < min_separation:
            if value > normalized[peaks[-1]]:
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


def _validated_frame_metrics(inventory: Mapping[str, Any], frame_metrics: Mapping[str, Any]) -> tuple[list[float], list[float]]:
    frames = frame_metrics.get("frames", [])
    if not isinstance(frames, list) or not frames:
        raise ActionInventoryError("frame_metrics.frames must be a non-empty list")
    scenes = sorted(inventory["scenes"], key=lambda item: int(item["start_frame"]))
    expected_count = int(scenes[-1]["end_frame"])
    if len(frames) != expected_count:
        raise ActionInventoryError(f"frame metric coverage mismatch: {len(frames)} != {expected_count}")
    mad: list[float] = []
    flow: list[float] = []
    for expected_frame, item in enumerate(frames):
        if not isinstance(item, Mapping):
            raise ActionInventoryError(f"frame metric row {expected_frame} must be an object")
        actual_frame = _frame_index(item.get("frame"), name="frame_metrics.frame")
        if actual_frame != expected_frame:
            raise ActionInventoryError(
                f"frame metric identity/order mismatch: expected {expected_frame}, got {actual_frame}"
            )
        mad.append(_finite_nonnegative(item.get("mad"), name=f"frame[{expected_frame}].mad"))
        flow.append(_finite_nonnegative(item.get("flow_p90"), name=f"frame[{expected_frame}].flow_p90"))
    return mad, flow


def gauntlet_coverage_from_frame_metrics(inventory: Mapping[str, Any], frame_metrics: Mapping[str, Any]) -> dict[str, Any]:
    validate_action_inventory(inventory)
    if not isinstance(frame_metrics, Mapping):
        raise ActionInventoryError("frame_metrics must be an object")
    mad, flow = _validated_frame_metrics(inventory, frame_metrics)
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
        "schema_version": "1.2.0",
        "scene_coverage": 1.0,
        "frame_metric_coverage": 1.0,
        "frame_metric_identity": "explicit_contiguous_zero_based",
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
