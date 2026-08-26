from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict
from math import sqrt
from typing import Iterable, Sequence

RGB = tuple[int, int, int]
BBox = tuple[float, float, float, float]


def _clamp8(v: int) -> int:
    return max(0, min(255, int(v)))


def rgb_to_hex(rgb: RGB) -> str:
    return "#%02X%02X%02X" % tuple(_clamp8(v) for v in rgb)


def quantize_rgb(rgb: RGB, step: int = 32) -> RGB:
    if step <= 0:
        raise ValueError("step must be > 0")
    return tuple(_clamp8(round(c / step) * step) for c in rgb)  # type: ignore[return-value]


def dominant_palette(samples: Iterable[RGB], *, max_colors: int = 6, quant_step: int = 32) -> list[dict]:
    values = [quantize_rgb(s, quant_step) for s in samples]
    if not values:
        return []
    counts = Counter(values)
    total = sum(counts.values())
    return [
        {"hex": rgb_to_hex(rgb), "ratio": round(count / total, 4), "rgb": list(rgb)}
        for rgb, count in counts.most_common(max_colors)
    ]


def relative_luminance(rgb: RGB) -> float:
    def channel(c: int) -> float:
        x = c / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: RGB, b: RGB) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def gradient_candidate(start: RGB, end: RGB, *, axis: str = "linear", threshold: float = 28.0) -> dict:
    distance = sqrt(sum((a - b) ** 2 for a, b in zip(start, end)))
    return {
        "detected": distance >= threshold,
        "type": axis if distance >= threshold else None,
        "stops": [
            {"hex": rgb_to_hex(start), "pos": 0.0},
            {"hex": rgb_to_hex(end), "pos": 1.0},
        ] if distance >= threshold else [],
        "rgb_distance": round(distance, 3),
        "confidence": round(min(1.0, distance / 180.0), 3),
        "method": "endpoint_color_distance",
    }


def infer_layout(boxes: Sequence[BBox], *, tolerance: float = 0.025) -> dict:
    """Infer simple normalized layout signals from boxes in [0,1] coordinates."""
    if not boxes:
        return {"pattern": "empty", "anchors_x": [], "anchors_y": [], "safe_margin_pct": None, "confidence": 0.0}
    centers_x = [(x1 + x2) / 2 for x1, _, x2, _ in boxes]
    centers_y = [(y1 + y2) / 2 for _, y1, _, y2 in boxes]

    def cluster(vals: Sequence[float]) -> list[float]:
        out: list[list[float]] = []
        for value in sorted(vals):
            if not out or abs(value - sum(out[-1]) / len(out[-1])) > tolerance:
                out.append([value])
            else:
                out[-1].append(value)
        return [round(sum(g) / len(g), 4) for g in out]

    anchors_x, anchors_y = cluster(centers_x), cluster(centers_y)
    left = min(b[0] for b in boxes)
    right = 1 - max(b[2] for b in boxes)
    top = min(b[1] for b in boxes)
    bottom = 1 - max(b[3] for b in boxes)
    safe = max(0.0, min(left, right, top, bottom)) * 100
    centered = sum(abs(x - 0.5) <= 0.08 for x in centers_x) / len(centers_x)
    if centered >= 0.6:
        pattern = "centered_hero"
    elif len(anchors_x) == 2:
        pattern = "split"
    elif len(boxes) >= 3:
        pattern = "floating_cards"
    else:
        pattern = "other"
    return {
        "pattern": pattern,
        "anchors_x": anchors_x,
        "anchors_y": anchors_y,
        "safe_margin_pct": round(safe, 2),
        "confidence": round(max(0.45, centered), 3),
        "method": "bbox_anchor_clustering",
    }
