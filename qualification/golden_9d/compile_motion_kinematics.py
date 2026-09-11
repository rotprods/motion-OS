#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from pathlib import Path
from typing import Any

NUMBER = r"-?(?:\d+(?:\.\d+)?|\.\d+)"


def _array_body(text: str, name: str) -> str:
    match = re.search(rf"const\s+{re.escape(name)}[^=]*=\s*\[(.*?)\];", text, re.S)
    if not match:
        raise ValueError(f"array not found: {name}")
    return match.group(1)


def parse_keyframed_boxes(text: str, name: str) -> list[dict[str, float]]:
    body = _array_body(text, name)
    pattern = re.compile(
        rf"\{{\s*frame\s*:\s*(\d+)\s*,\s*x\s*:\s*({NUMBER})\s*,\s*y\s*:\s*({NUMBER})\s*,\s*width\s*:\s*({NUMBER})\s*,\s*height\s*:\s*({NUMBER})(?:\s*,\s*opacity\s*:\s*({NUMBER}))?\s*\}}"
    )
    rows: list[dict[str, float]] = []
    for m in pattern.finditer(body):
        row: dict[str, float] = {
            "frame": int(m.group(1)),
            "x": float(m.group(2)),
            "y": float(m.group(3)),
            "width": float(m.group(4)),
            "height": float(m.group(5)),
        }
        if m.group(6) is not None:
            row["opacity_proxy"] = float(m.group(6))
        rows.append(row)
    if not rows:
        raise ValueError(f"no keyframes parsed: {name}")
    if any(b["frame"] <= a["frame"] for a, b in zip(rows, rows[1:])):
        raise ValueError(f"keyframes must be strictly increasing: {name}")
    return rows


def interpolate_keyframes(rows: list[dict[str, float]]) -> list[dict[str, float]]:
    output: list[dict[str, float]] = []
    channels = ("x", "y", "width", "height", "opacity_proxy")
    for left, right in zip(rows, rows[1:]):
        start = int(left["frame"])
        end = int(right["frame"])
        for frame in range(start, end):
            if output and output[-1]["frame"] == frame:
                continue
            t = (frame - start) / (end - start)
            row: dict[str, float] = {"frame": frame}
            for ch in channels:
                if ch in left or ch in right:
                    lv = float(left.get(ch, 1.0 if ch == "opacity_proxy" else 0.0))
                    rv = float(right.get(ch, lv))
                    row[ch] = lv + (rv - lv) * t
            output.append(row)
    output.append(dict(rows[-1]))
    return output


def parse_indexed_tuples(text: str, name: str, factor: bool = False) -> list[dict[str, float] | None]:
    body = _array_body(text, name)
    raw = json.loads("[" + body + "]")
    rows: list[dict[str, float] | None] = []
    expected_width = 5 if factor else 4
    for frame, value in enumerate(raw):
        if value is None:
            rows.append(None)
            continue
        if len(value) != expected_width:
            raise ValueError(f"unexpected tuple width for {name}@{frame}: {len(value)}")
        row: dict[str, float] = {
            "frame": frame,
            "x": float(value[0]),
            "y": float(value[1]),
            "width": float(value[2]),
            "height": float(value[3]),
        }
        if factor:
            row["opacity_proxy"] = float(value[4])
        rows.append(row)
    return rows


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    t = pos - lo
    return ordered[lo] + (ordered[hi] - ordered[lo]) * t


def _direction(dx: float, dy: float, area_ratio: float) -> str:
    dist = math.hypot(dx, dy)
    if dist < 1.0 and abs(area_ratio - 1.0) > 0.03:
        return "SCALE_DOMINANT"
    if dist < 1.0:
        return "STATIC_OR_MICRO"
    if abs(dx) > abs(dy) * 1.5:
        return "RIGHT" if dx > 0 else "LEFT"
    if abs(dy) > abs(dx) * 1.5:
        return "DOWN" if dy > 0 else "UP"
    return ("DOWN_" if dy > 0 else "UP_") + ("RIGHT" if dx > 0 else "LEFT")


def _transform_components(a: dict[str, float], b: dict[str, float]) -> dict[str, Any]:
    acx, acy = a["x"] + a["width"] / 2, a["y"] + a["height"] / 2
    bcx, bcy = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    dx, dy = bcx - acx, bcy - acy
    dw, dh = b["width"] - a["width"], b["height"] - a["height"]
    left_delta = b["x"] - a["x"]
    top_delta = b["y"] - a["y"]
    right_delta = (b["x"] + b["width"]) - (a["x"] + a["width"])
    bottom_delta = (b["y"] + b["height"]) - (a["y"] + a["height"])
    translation_energy = math.hypot(dx, dy)
    size_change_energy = math.hypot(dw, dh) / 2
    relative_size_change = max(
        abs(dw) / max(abs(a["width"]), 1e-9),
        abs(dh) / max(abs(a["height"]), 1e-9),
    )
    opacity_delta = abs(float(b.get("opacity_proxy", 1.0)) - float(a.get("opacity_proxy", 1.0)))
    area_ratio = (b["width"] * b["height"]) / max(1e-9, a["width"] * a["height"])

    if translation_energy < 0.45 and relative_size_change < 0.01 and opacity_delta < 0.03:
        transform_class = "STATIC_OR_MICRO"
    elif (
        opacity_delta >= 0.12
        or (relative_size_change >= 0.08 and size_change_energy >= translation_energy * 0.90)
        or (area_ratio >= 1.50 and size_change_energy >= translation_energy * 0.75)
    ):
        transform_class = "SCALE_OR_REVEAL_DOMINANT"
    elif translation_energy >= size_change_energy * 1.75 and relative_size_change < 0.12:
        transform_class = "TRANSLATION_DOMINANT"
    else:
        transform_class = "MIXED_TRANSLATION_AND_SCALE"

    return {
        "centroid_delta_px": [dx, dy],
        "centroid_displacement_px": translation_energy,
        "size_delta_px": [dw, dh],
        "size_change_energy_px": size_change_energy,
        "relative_size_change": relative_size_change,
        "opacity_proxy_delta": opacity_delta,
        "area_scale_ratio": area_ratio,
        "edge_delta_px": {
            "left": left_delta,
            "top": top_delta,
            "right": right_delta,
            "bottom": bottom_delta,
        },
        "centroid_direction": _direction(dx, dy, area_ratio),
        "transform_class": transform_class,
    }


def _curve_proxy(speeds: list[float]) -> tuple[str, str]:
    if len(speeds) < 4:
        return "INSUFFICIENT_SAMPLES", "LOW"
    n = len(speeds)
    q = max(1, n // 4)
    a = statistics.fmean(speeds[:q])
    mid_lo = max(0, n // 2 - max(1, q // 2))
    mid_hi = min(n, n // 2 + max(1, q // 2))
    m = statistics.fmean(speeds[mid_lo:mid_hi])
    z = statistics.fmean(speeds[-q:])
    peak = max(speeds)
    eps = max(0.2, peak * 0.12)
    if peak < 0.45:
        return "HOLD_OR_MICRO_DRIFT", "HIGH"
    if a + eps < m and z + eps < m:
        return "EASE_IN_OUT_LIKE_SPEED_PROFILE", "MEDIUM"
    if a > m + eps and m > z + eps:
        return "DECELERATING_EASE_OUT_LIKE", "MEDIUM"
    if a + eps < m and m + eps < z:
        return "ACCELERATING_EASE_IN_LIKE", "MEDIUM"
    spread = statistics.pstdev(speeds) if len(speeds) > 1 else 0.0
    if spread <= max(0.25, statistics.fmean(speeds) * 0.12):
        return "CONSTANT_RATE_LIKE", "MEDIUM"
    return "PIECEWISE_OR_IRREGULAR", "LOW"


def _frame_in_ranges(frame: int, ranges: list[list[int]]) -> bool:
    return any(int(start) <= frame <= int(end) for start, end in ranges)


def _clip_flags(row: dict[str, float], clip_rect: list[float] | None) -> list[str]:
    if not clip_rect:
        return []
    left, top, right, bottom = map(float, clip_rect)
    eps = 0.25
    flags = []
    if row["x"] <= left + eps:
        flags.append("LEFT")
    if row["y"] <= top + eps:
        flags.append("TOP")
    if row["x"] + row["width"] >= right - eps:
        flags.append("RIGHT")
    if row["y"] + row["height"] >= bottom - eps:
        flags.append("BOTTOM")
    return flags


def _cap_confidence(confidence: str, ceiling: str) -> str:
    order = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
    return confidence if order[confidence] <= order[ceiling] else ceiling


def kinematics(
    rows: list[dict[str, float] | None],
    fps: float,
    authority: str,
    *,
    canvas: dict[str, float] | None = None,
    clip_rect: list[float] | None = None,
    projection_mode: str = "UNKNOWN",
    structural_exclude_ranges: list[list[int]] | None = None,
) -> dict[str, Any]:
    exclusions = structural_exclude_ranges or []
    if clip_rect is None and canvas:
        clip_rect = [0.0, 0.0, float(canvas["width"]), float(canvas["height"])]
    visible = [r for r in rows if r is not None]
    if not visible:
        return {"authority": authority, "visible": False}

    samples: list[dict[str, Any]] = []
    speeds: list[float] = []
    accels: list[float] = []
    scale_rates: list[float] = []
    active_frames: list[int] = []
    prev: dict[str, float] | None = None
    prev_speed: float | None = None
    boundary_clipped_samples = 0
    structural_excluded_samples = 0

    for row in visible:
        frame = int(row["frame"])
        cx = row["x"] + row["width"] / 2
        cy = row["y"] + row["height"] / 2
        clipping = _clip_flags(row, clip_rect)
        excluded = _frame_in_ranges(frame, exclusions)
        sample: dict[str, Any] = {
            "frame": frame,
            "centroid": [cx, cy],
            "bbox": [row["x"], row["y"], row["width"], row["height"]],
            "screen_clip_flags": clipping,
            "structural_template_eligible": not excluded,
        }
        if clipping:
            boundary_clipped_samples += 1
        if excluded:
            structural_excluded_samples += 1
        if "opacity_proxy" in row:
            sample["opacity_proxy"] = row["opacity_proxy"]

        consecutive = prev is not None and frame == int(prev["frame"]) + 1
        if consecutive:
            transform = _transform_components(prev, row)
            speed = float(transform["centroid_displacement_px"])
            log_scale_rate = math.log(max(1e-9, float(transform["area_scale_ratio"]))) / 2
            step_clipped = bool(clipping or _clip_flags(prev, clip_rect))
            step_excluded = excluded or _frame_in_ranges(int(prev["frame"]), exclusions)
            sample.update({
                "delta_px": transform["centroid_delta_px"],
                "speed_px_per_frame": speed,
                "speed_px_per_second": speed * fps,
                "log_scale_rate_per_frame": log_scale_rate,
                "direction": transform["centroid_direction"],
                "transform_class": transform["transform_class"],
                "size_delta_px": transform["size_delta_px"],
                "relative_size_change": transform["relative_size_change"],
                "edge_delta_px": transform["edge_delta_px"],
                "step_screen_clipped": step_clipped,
                "step_structural_template_eligible": not step_excluded,
            })
            speeds.append(speed)
            scale_rates.append(abs(log_scale_rate))
            if prev_speed is not None:
                accel = speed - prev_speed
                sample["acceleration_px_per_frame2"] = accel
                accels.append(accel)
            if speed > 0.45 or abs(log_scale_rate) > 0.004:
                active_frames.append(frame)
            prev_speed = speed
        else:
            prev_speed = None
        samples.append(sample)
        prev = row

    segments: list[list[int]] = []
    for frame in active_frames:
        if not segments or frame - segments[-1][-1] > 2:
            segments.append([frame])
        else:
            segments[-1].append(frame)

    segment_summaries = []
    by_frame = {int(r["frame"]): r for r in visible}
    sample_by_frame = {int(s["frame"]): s for s in samples}
    for seg in segments:
        start = max(int(visible[0]["frame"]), seg[0] - 1)
        end = seg[-1]
        a = by_frame.get(start) or by_frame[seg[0]]
        b = by_frame[end]
        transform = _transform_components(a, b)
        seg_samples = [sample_by_frame[f] for f in range(start, end + 1) if f in sample_by_frame]
        seg_speeds = [s["speed_px_per_frame"] for s in seg_samples if "speed_px_per_frame" in s]
        curve, confidence = _curve_proxy(seg_speeds)
        clipped = any(s.get("screen_clip_flags") or s.get("step_screen_clipped") for s in seg_samples)
        excluded = any(not s.get("structural_template_eligible", True) or not s.get("step_structural_template_eligible", True) for s in seg_samples)
        caveats: list[str] = []
        curve_authority = "EVIDENCE_BOUND_BEHAVIORAL_PROXY_NOT_ORIGINAL_GRAPH_EDITOR"
        if projection_mode.startswith("KEYFRAME_LINEAR"):
            confidence = _cap_confidence(confidence, "LOW")
            caveats.append("KEYFRAME_LINEAR_INTERPOLATION_CAN_SHAPE_SPEED_PROFILE")
            curve_authority = "RENDERER_PROJECTION_BEHAVIOR_PROXY_NOT_MEASURED_ORIGINAL_EASING"
        if clipped:
            confidence = _cap_confidence(confidence, "LOW")
            caveats.append("SCREEN_BOUNDARY_CLIPPING_DISTORTS_VISIBLE_BBOX_KINEMATICS")
            curve_authority = "VISIBLE_OUTPUT_CLIPPED_PROXY_NOT_HIDDEN_OBJECT_CURVE"
        if transform["transform_class"] in {"SCALE_OR_REVEAL_DOMINANT", "MIXED_TRANSLATION_AND_SCALE"}:
            confidence = _cap_confidence(confidence, "LOW")
            caveats.append("BBOX_SHAPE_CHANGE_CONFLATES_TRANSLATION_WITH_SCALE_OR_REVEAL")
            if not clipped:
                curve_authority = "BBOX_CENTROID_SPEED_PROXY_NOT_PURE_TRANSLATION_CURVE"
        if excluded:
            caveats.append("SOURCE_LOCK_RANGE_EXCLUDED_FROM_STRUCTURAL_MOTION_GRAMMAR")
        segment_summaries.append({
            "start_frame": start,
            "end_frame": end,
            "duration_frames": end - start + 1,
            "net_delta_px": transform["centroid_delta_px"],
            "centroid_direction": transform["centroid_direction"],
            "dominant_transform_class": transform["transform_class"],
            "area_scale_ratio": transform["area_scale_ratio"],
            "size_delta_px": transform["size_delta_px"],
            "edge_delta_px": transform["edge_delta_px"],
            "behavioral_curve_proxy": curve,
            "curve_basis": "BBOX_CENTROID_SPEED",
            "curve_proxy_confidence": confidence,
            "curve_authority": curve_authority,
            "screen_boundary_clipped": clipped,
            "structural_template_eligible": not excluded,
            "caveats": caveats,
        })

    return {
        "authority": authority,
        "projection_mode": projection_mode,
        "clip_rect": clip_rect,
        "visible": True,
        "first_visible_frame": int(visible[0]["frame"]),
        "last_visible_frame": int(visible[-1]["frame"]),
        "sample_count": len(visible),
        "boundary_clipped_sample_count": boundary_clipped_samples,
        "structural_excluded_sample_count": structural_excluded_samples,
        "structural_exclude_ranges": exclusions,
        "motion_segments": segment_summaries,
        "metrics": {
            "median_speed_px_per_frame": statistics.median(speeds) if speeds else 0.0,
            "p95_speed_px_per_frame": _percentile(speeds, 0.95),
            "max_speed_px_per_frame": max(speeds, default=0.0),
            "p95_abs_acceleration_px_per_frame2": _percentile([abs(x) for x in accels], 0.95),
            "max_abs_acceleration_px_per_frame2": max((abs(x) for x in accels), default=0.0),
            "p95_abs_log_scale_rate_per_frame": _percentile(scale_rates, 0.95),
        },
        "samples": samples,
    }


def compile_manifest(manifest: dict, root: Path) -> dict:
    if manifest.get("schema_version") != "motion-os.golden-motion-sources/v2":
        raise ValueError("unsupported motion source manifest")
    canvas = manifest.get("canvas")
    scenes_out: dict[str, Any] = {}
    for scene_id, spec in manifest["scenes"].items():
        path = root / spec["checkout_dir"] / spec["path"]
        text = path.read_text()
        entities: dict[str, Any] = {}
        for entity, array_name in spec["entities"].items():
            if spec["format"] == "ts_keyframed_boxes":
                rows = interpolate_keyframes(parse_keyframed_boxes(text, array_name))
            elif spec["format"] == "ts_indexed_tuple_boxes":
                rows = parse_indexed_tuples(text, array_name, array_name in set(spec.get("factor_arrays", [])))
            else:
                raise ValueError(f"unsupported format: {spec['format']}")
            entities[entity] = kinematics(
                rows,
                float(spec["fps"]),
                spec["authority"],
                canvas=canvas,
                clip_rect=spec.get("clip_rect"),
                projection_mode=spec.get("projection_mode", "UNKNOWN"),
                structural_exclude_ranges=spec.get("structural_exclude_ranges", []),
            )
        scenes_out[scene_id] = {
            "source_ref": spec["ref"],
            "source_path": spec["path"],
            "authority": spec["authority"],
            "projection_mode": spec.get("projection_mode", "UNKNOWN"),
            "clip_rect": spec.get("clip_rect"),
            "caveat": spec.get("caveat"),
            "entities": entities,
        }
    return {
        "schema_version": "motion-os.golden-motion-kinematics/v3",
        "authority": "DERIVED_FROM_PINNED_SOURCE_BOUND_TRACKS",
        "curve_authority": "BEHAVIORAL_PROXY_ONLY_NOT_ORIGINAL_AFTER_EFFECTS_GRAPH_EDITOR",
        "laws": manifest.get("laws", {}),
        "scenes": scenes_out,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = compile_manifest(json.loads(args.manifest.read_text()), args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "scene_count": len(result["scenes"]),
        "entity_count": sum(len(x["entities"]) for x in result["scenes"].values()),
        "out": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
