from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import math


@dataclass(frozen=True)
class GroundTruth:
    fps: float
    total_frames: int
    shot_boundaries: tuple[int, ...]
    dominant_colors: tuple[str, ...] = ()
    text_strings: tuple[str, ...] = ()
    motion_direction: str | None = None


def _nearest_error(expected: int, actual: Sequence[int]) -> int | None:
    if not actual:
        return None
    return min(abs(expected - x) for x in actual)


def shot_boundary_metrics(expected: Sequence[int], actual: Sequence[int], *, tolerance_frames: int = 2) -> dict[str, Any]:
    expected = list(expected)
    actual = list(actual)
    matched_expected: set[int] = set()
    matched_actual: set[int] = set()
    errors: list[int] = []
    for ei, e in enumerate(expected):
        candidates = [(abs(e - a), ai) for ai, a in enumerate(actual) if ai not in matched_actual and abs(e - a) <= tolerance_frames]
        if not candidates:
            continue
        err, ai = min(candidates)
        matched_expected.add(ei)
        matched_actual.add(ai)
        errors.append(err)
    tp = len(matched_expected)
    precision = tp / len(actual) if actual else (1.0 if not expected else 0.0)
    recall = tp / len(expected) if expected else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "expected": expected,
        "actual": actual,
        "tolerance_frames": tolerance_frames,
        "tp": tp,
        "fp": len(actual) - tp,
        "fn": len(expected) - tp,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "mean_abs_boundary_error_frames": round(sum(errors) / len(errors), 6) if errors else None,
        "max_boundary_error_frames": max(errors) if errors else None,
    }


def text_metrics(expected: Sequence[str], ocr_blocks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected_norm = [x.strip().casefold() for x in expected if x.strip()]
    actual = [str(x.get("text", "")).strip().casefold() for x in ocr_blocks if str(x.get("text", "")).strip()]
    hits = sum(1 for text in expected_norm if any(text == a or text in a or a in text for a in actual))
    return {"expected_count": len(expected_norm), "detected_count": len(actual), "exact_or_containment_recall": round(hits / len(expected_norm), 6) if expected_norm else 1.0}


def color_metrics(expected_hex: Sequence[str], palette: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    def rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    actual = [str(x.get("hex")) for x in palette if x.get("hex")]
    distances: list[float] = []
    for e in expected_hex:
        er = rgb(e)
        if actual:
            distances.append(min(math.sqrt(sum((a-b)**2 for a,b in zip(er, rgb(x)))) for x in actual))
    return {"expected": list(expected_hex), "actual": actual, "mean_rgb_distance": round(sum(distances)/len(distances), 4) if distances else None, "max_rgb_distance": round(max(distances), 4) if distances else None}


def benchmark_feature_pack(pack: Mapping[str, Any], truth: GroundTruth, *, tolerance_frames: int = 2) -> dict[str, Any]:
    actual_boundaries = [int(s["start_frame"]) for s in pack.get("shots", [])[1:]]
    report = {
        "ground_truth": asdict(truth),
        "shot_detection": shot_boundary_metrics(truth.shot_boundaries, actual_boundaries, tolerance_frames=tolerance_frames),
        "colors": color_metrics(truth.dominant_colors, pack.get("color_stats", {}).get("palette", [])),
        "ocr": text_metrics(truth.text_strings, pack.get("ocr", [])),
        "evidence": {
            "keyframes": len(pack.get("keyframes", [])),
            "warnings": list(pack.get("warnings", [])),
        },
    }
    # Do not collapse incomparable verticals into a fake single quality score.
    report["promotion_authority"] = "ground_truth_measurement"
    return report


def save_benchmark(report: Mapping[str, Any], path: str | Path) -> None:
    Path(path).write_text(json.dumps(dict(report), indent=2, ensure_ascii=False), encoding="utf-8")
