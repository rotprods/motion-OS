#!/usr/bin/env python3
from __future__ import annotations

import argparse
from array import array
from dataclasses import dataclass
from pathlib import Path
import colorsys
import json
import math
import statistics
import wave

from PIL import Image


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    width: float
    height: float

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)

    @property
    def cx(self) -> float:
        return self.x + self.width / 2.0

    @property
    def cy(self) -> float:
        return self.y + self.height / 2.0


def _load_baseline(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("schema_version") != "motion-os.s04-fidelity-baseline/v1":
        raise ValueError("unsupported baseline schema")
    return data


def _track_map(raw: dict) -> dict[int, Box]:
    out: dict[int, Box] = {}
    for item in raw["keyframes"]:
        out[int(item["frame"])] = Box(
            float(item["x"]),
            float(item["y"]),
            float(item["width"]),
            float(item["height"]),
        )
    return out


def _sample_track(track: dict[int, Box], frame: int) -> Box | None:
    keys = sorted(track)
    if frame < keys[0] or frame > keys[-1]:
        return None
    if frame in track:
        return track[frame]
    left = max(x for x in keys if x < frame)
    right = min(x for x in keys if x > frame)
    progress = (frame - left) / (right - left)
    a, b = track[left], track[right]
    return Box(
        a.x + (b.x - a.x) * progress,
        a.y + (b.y - a.y) * progress,
        a.width + (b.width - a.width) * progress,
        a.height + (b.height - a.height) * progress,
    )


def _overlay_path(directory: Path, frame: int) -> Path:
    candidates = [
        directory / f"element-{frame:02d}.png",
        directory / f"frame_{frame:03d}.png",
        directory / f"{frame:04d}.png",
        directory / f"{frame + 1:04d}.png",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"no overlay frame for {frame}: {candidates}")


def _source_path(directory: Path, frame: int) -> Path:
    candidates = [
        directory / f"frame_{frame:03d}.png",
        directory / f"{frame:04d}.png",
        directory / f"{frame + 1:04d}.png",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"no source frame for {frame}")


def _is_red(px: tuple[int, ...], has_alpha: bool) -> bool:
    r, g, b = px[:3]
    if has_alpha and len(px) >= 4 and px[3] <= 20:
        return False
    return r > 100 and r > g * 1.7 and r > b * 1.5 and (r - g) > 50


def _is_white(px: tuple[int, ...], has_alpha: bool) -> bool:
    r, g, b = px[:3]
    if has_alpha and len(px) >= 4 and px[3] <= 20:
        return False
    return r > 150 and g > 150 and b > 150 and max(r, g, b) - min(r, g, b) < 70


def _crop_bounds(box: Box, image_size: tuple[int, int], pad: int) -> tuple[int, int, int, int]:
    width, height = image_size
    x0 = max(0, math.floor(box.x - pad))
    y0 = max(0, math.floor(box.y - pad))
    x1 = min(width, math.ceil(box.x + box.width + pad))
    y1 = min(height, math.ceil(box.y + box.height + pad))
    return x0, y0, x1, y1


def _component_pixels_and_bbox(
    image: Image.Image,
    expected: Box,
    kind: str,
    *,
    pad: int,
) -> tuple[list[tuple[int, int, int]], Box | None]:
    rgba = image.convert("RGBA")
    x0, y0, x1, y1 = _crop_bounds(expected, rgba.size, pad)
    pix = rgba.load()
    coords: list[tuple[int, int]] = []
    colors: list[tuple[int, int, int]] = []
    classifier = _is_red if kind == "red" else _is_white
    for y in range(y0, y1):
        for x in range(x0, x1):
            value = pix[x, y]
            if classifier(value, True):
                coords.append((x, y))
                colors.append((value[0], value[1], value[2]))
    if not coords:
        return colors, None
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    return colors, Box(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def _visible_source_colors(image: Image.Image, expected: Box, kind: str) -> list[tuple[int, int, int]]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    x0 = max(0, math.floor(expected.x))
    y0 = max(0, math.floor(expected.y))
    x1 = min(width, math.ceil(expected.x + expected.width))
    y1 = min(height, math.ceil(expected.y + expected.height))
    pix = rgb.load()
    classifier = _is_red if kind == "red" else _is_white
    colors: list[tuple[int, int, int]] = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            value = pix[x, y]
            if classifier(value, False):
                colors.append(value)
    return colors


def _rect_iou(a: Box, b: Box) -> float:
    ix = max(0.0, min(a.x + a.width, b.x + b.width) - max(a.x, b.x))
    iy = max(0.0, min(a.y + a.height, b.y + b.height) - max(a.y, b.y))
    inter = ix * iy
    union = a.area + b.area - inter
    return inter / union if union > 0 else 0.0


def _median_rgb(colors: list[tuple[int, int, int]]) -> tuple[float, float, float] | None:
    if not colors:
        return None
    return tuple(float(statistics.median([c[i] for c in colors])) for i in range(3))


def _srgb_channel_to_linear(v: float) -> float:
    v /= 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def _rgb_to_lab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    r, g, b = [_srgb_channel_to_linear(v) for v in rgb]
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = (0.2126729 * r + 0.7151522 * g + 0.0721750 * b) / 1.00000
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    delta = 6 / 29
    def f(t: float) -> float:
        return t ** (1 / 3) if t > delta ** 3 else t / (3 * delta ** 2) + 4 / 29

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def _delta_e76(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    la, lb = _rgb_to_lab(a), _rgb_to_lab(b)
    return math.sqrt(sum((la[i] - lb[i]) ** 2 for i in range(3)))


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _transient_peak_wav(path: Path, block_ms: float = 5.0) -> dict:
    with wave.open(str(path), "rb") as w:
        if w.getsampwidth() != 2:
            raise ValueError("only PCM16 WAV is supported for transient proxy")
        sample_rate = w.getframerate()
        channels = w.getnchannels()
        frame_count = w.getnframes()
        raw = w.readframes(frame_count)
    samples = array("h")
    samples.frombytes(raw)
    if channels > 1:
        mono = []
        for i in range(0, len(samples), channels):
            mono.append(sum(samples[i:i + channels]) / channels)
    else:
        mono = list(samples)
    block = max(8, int(sample_rate * block_ms / 1000.0))
    best_index = 0
    best_score = -1.0
    for start in range(0, len(mono) - block + 1, block):
        segment = mono[start:start + block]
        if len(segment) < 2:
            continue
        sum_sq = 0.0
        for i in range(1, len(segment)):
            d = (segment[i] - segment[i - 1]) / 32768.0
            sum_sq += d * d
        score = math.sqrt(sum_sq / max(1, len(segment) - 1))
        if score > best_score:
            best_score = score
            best_index = start
    duration_s = len(mono) / sample_rate
    return {
        "peak_seconds": best_index / sample_rate,
        "duration_seconds": duration_s,
        "score": best_score,
    }


def _corr(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or len(a) < 2:
        raise ValueError("correlation requires equal non-trivial series")
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    da = [x - ma for x in a]
    db = [x - mb for x in b]
    denom = math.sqrt(sum(x * x for x in da) * sum(x * x for x in db))
    return sum(da[i] * db[i] for i in range(len(a))) / denom if denom else 0.0


def qualify(args: argparse.Namespace) -> dict:
    baseline = _load_baseline(args.baseline)
    fps = float(baseline["source"]["fps"])
    width = int(baseline["source"]["width"])
    height = int(baseline["source"]["height"])

    tracks = {name: _track_map(raw) for name, raw in baseline["tracks"].items()}
    kinds = {name: raw["kind"] for name, raw in baseline["tracks"].items()}

    component_metrics: dict[str, dict] = {}
    per_frame: dict[str, list[dict]] = {}
    for name, track in tracks.items():
        first, last = min(track), max(track)
        records = []
        overlay_visible = []
        source_colors_all: list[tuple[int, int, int]] = []
        overlay_colors_all: list[tuple[int, int, int]] = []
        for frame in range(first, last + 1):
            expected = _sample_track(track, frame)
            if expected is None:
                continue
            overlay = Image.open(_overlay_path(args.overlay_dir, frame))
            if overlay.size != (width, height):
                raise ValueError(f"overlay frame {frame} size mismatch: {overlay.size}")
            colors, observed = _component_pixels_and_bbox(
                overlay,
                expected,
                kinds[name],
                pad=28 if name == "hero" else 22,
            )
            if observed is not None:
                overlay_visible.append(frame)
                overlay_colors_all.extend(colors)
                records.append({
                    "frame": frame,
                    "expected": expected.__dict__,
                    "observed": observed.__dict__,
                    "iou": _rect_iou(expected, observed),
                    "centroid_error_px": math.hypot(observed.cx - expected.cx, observed.cy - expected.cy),
                    "area_error_pct": abs(observed.area - expected.area) / expected.area * 100.0 if expected.area else 0.0,
                    "dx": observed.x - expected.x,
                    "dy": observed.y - expected.y,
                    "dw": observed.width - expected.width,
                    "dh": observed.height - expected.height,
                })

            if args.source_dir:
                source = Image.open(_source_path(args.source_dir, frame))
                if source.size != (width, height):
                    raise ValueError(f"source frame {frame} size mismatch: {source.size}")
                source_colors_all.extend(_visible_source_colors(source, expected, kinds[name]))

        if not records:
            raise ValueError(f"no overlay observations for {name}")
        source_first, source_last = first, last
        overlay_first, overlay_last = min(overlay_visible), max(overlay_visible)
        metric = {
            "source_first_visible": source_first,
            "source_last_visible": source_last,
            "overlay_first_visible": overlay_first,
            "overlay_last_visible": overlay_last,
            "temporal_visibility_exact": source_first == overlay_first and source_last == overlay_last,
            "mean_bbox_iou": _mean([r["iou"] for r in records]),
            "min_bbox_iou": min(r["iou"] for r in records),
            "mean_centroid_error_px": _mean([r["centroid_error_px"] for r in records]),
            "max_centroid_error_px": max(r["centroid_error_px"] for r in records),
            "mean_area_error_pct": _mean([r["area_error_pct"] for r in records]),
            "mean_dx_px": _mean([r["dx"] for r in records]),
            "mean_dy_px": _mean([r["dy"] for r in records]),
            "mean_dw_px": _mean([r["dw"] for r in records]),
            "mean_dh_px": _mean([r["dh"] for r in records]),
        }
        source_median = _median_rgb(source_colors_all)
        overlay_median = _median_rgb(overlay_colors_all)
        if source_median is not None and overlay_median is not None:
            metric["visible_color_proxy"] = {
                "source_median_rgb": source_median,
                "overlay_median_rgb": overlay_median,
                "deltaE76": _delta_e76(source_median, overlay_median),
                "authority": "VISIBLE_OUTPUT_PROXY_NOT_ORIGINAL_FILL_TOKEN",
            }
        component_metrics[name] = metric
        per_frame[name] = records

    setup, hero, tail = tracks["setup"], tracks["hero"], tracks["tail"]
    frames_sh = range(max(min(setup), min(hero), 11), min(max(setup), max(hero)) + 1)
    sw = [_sample_track(setup, f).width for f in frames_sh]
    hw = [_sample_track(hero, f).width for f in frames_sh]
    sw_norm = [x / sw[0] for x in sw]
    hw_norm = [x / hw[0] for x in hw]
    sh_corr = _corr(sw_norm, hw_norm)
    sh_rmse = math.sqrt(statistics.fmean([(sw_norm[i] - hw_norm[i]) ** 2 for i in range(len(sw_norm))]))

    frames_sht = range(max(min(tail), 38), min(max(setup), max(hero), max(tail)) + 1)
    series = {}
    for name, track in (("setup", setup), ("hero", hero), ("tail", tail)):
        values = [_sample_track(track, f).width for f in frames_sht]
        series[name] = [x / values[0] for x in values]

    shared_parent = {
        "setup_hero_width_scale_correlation": sh_corr,
        "setup_hero_normalized_rmse": sh_rmse,
        "setup_tail_width_scale_correlation": _corr(series["setup"], series["tail"]),
        "hero_tail_width_scale_correlation": _corr(series["hero"], series["tail"]),
        "inference": (
            "After independent hero entrance, caption width trajectories strongly support a shared "
            "screen-space parent/reframe transform. This does not prove the original AE parenting graph."
        ),
        "authority": "EVIDENCE_BOUND_INFERENCE",
    }

    audio = {"authority": "NOT_MEASURED_THIS_RUN"}
    if args.source_audio and args.render_audio:
        source_peak = _transient_peak_wav(args.source_audio)
        render_peak = _transient_peak_wav(args.render_audio)
        source_frame = source_peak["peak_seconds"] * fps
        render_frame = render_peak["peak_seconds"] * fps
        audio = {
            "source_transient_proxy": source_peak,
            "render_transient_proxy": render_peak,
            "source_local_frame": source_frame,
            "render_local_frame": render_frame,
            "render_minus_source_frames": render_frame - source_frame,
            "absolute_error_frames": abs(render_frame - source_frame),
            "class_authority": "ONSET_MEASURED_SFX_CLASS_INFERRED_FROM_MIX",
        }

    thresholds = baseline["thresholds"]
    defects = []
    for name, metric in component_metrics.items():
        if not metric["temporal_visibility_exact"]:
            defects.append({
                "id": f"S04-DEF-TIMING-{name.upper()}",
                "severity": "P1",
                "domain": "typography",
                "condition": "visibility interval mismatch",
                "root_cause_family": "CAPTION_TEMPORAL_BINDING",
            })
        if (
            metric["mean_bbox_iou"] < thresholds["mean_bbox_iou_min"]
            or metric["mean_centroid_error_px"] > thresholds["mean_centroid_error_px_max"]
            or metric["mean_area_error_pct"] > thresholds["mean_area_error_pct_max"]
        ):
            defects.append({
                "id": f"S04-DEF-GEOMETRY-{name.upper()}",
                "severity": "P1",
                "domain": "typography",
                "condition": {
                    "mean_bbox_iou": metric["mean_bbox_iou"],
                    "mean_centroid_error_px": metric["mean_centroid_error_px"],
                    "mean_area_error_pct": metric["mean_area_error_pct"],
                },
                "root_cause_family": "SVG_FONT_METRICS_NOT_CALIBRATED_TO_SOURCE_VISIBLE_BOUNDS",
            })
        color = metric.get("visible_color_proxy")
        if color and color["deltaE76"] > thresholds["visible_color_deltaE76_warn"]:
            defects.append({
                "id": f"S04-DEF-COLOR-{name.upper()}",
                "severity": "P2",
                "domain": "color",
                "condition": {"visible_deltaE76": color["deltaE76"]},
                "root_cause_family": "VISIBLE_COLOR_TOKEN_OR_COMPOSITING_NOT_CALIBRATED",
                "authority_note": "proxy only; original fill token is unknown",
            })

    if audio.get("absolute_error_frames") is not None and audio["absolute_error_frames"] > thresholds["primary_audio_onset_error_frames_max"]:
        defects.append({
            "id": "S04-DEF-AUDIO-ONSET",
            "severity": "P1",
            "domain": "audio",
            "condition": {
                "onset_error_frames": audio["absolute_error_frames"],
                "render_minus_source_frames": audio["render_minus_source_frames"],
            },
            "root_cause_family": "SYNTHETIC_IMPACT_ANCHORED_TO_HISTORICAL_INFERENCE_NOT_MEASURED_ONSET",
        })

    unresolved_p0_p1 = [d for d in defects if d["severity"] in {"P0", "P1"}]
    return {
        "schema_version": "motion-os.s04-fidelity-qualification/v1",
        "scene_id": baseline["scene_id"],
        "source": baseline["source"],
        "component_metrics": component_metrics,
        "shared_parent_hypothesis": shared_parent,
        "audio": audio,
        "defects": defects,
        "qualification": {
            "state": "DEFECTS_FOUND_REPAIR_REQUIRED" if unresolved_p0_p1 else "SOURCE_BOUND_METRICS_PASS_PENDING_HUMAN_REVIEW",
            "unresolved_p0_p1_count": len(unresolved_p0_p1),
            "fidelity_validated": False,
            "authority": "MEASURED_SOURCE_BOUND_LOCAL_RUN",
            "blocked_dimensions": [
                "exact font identity",
                "original AE layer/effect graph",
                "isolated original SFX stem",
                "full composite camera/depth fidelity unless private clean plate is used",
            ],
        },
        "per_frame": per_frame if args.include_per_frame else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--overlay-dir", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--source-audio", type=Path)
    parser.add_argument("--render-audio", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--include-per-frame", action="store_true")
    args = parser.parse_args()
    result = qualify(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result["qualification"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
