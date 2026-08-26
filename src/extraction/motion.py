from __future__ import annotations

from dataclasses import dataclass, asdict
from math import hypot
from statistics import mean
from typing import Sequence

Point = tuple[float, float]


@dataclass(frozen=True)
class MotionTrack:
    direction: str
    displacement: float
    mean_speed: float
    acceleration_sign_changes: int
    easing_guess: str
    confidence: float
    method: str = "trajectory_heuristic"

    def to_dict(self):
        return asdict(self)


def _deltas(points: Sequence[Point]) -> list[Point]:
    return [(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])]


def dominant_direction(dx: float, dy: float, deadzone: float = 1e-6) -> str:
    if abs(dx) < deadzone and abs(dy) < deadzone:
        return "static"
    if abs(dx) >= abs(dy):
        return "left_to_right" if dx > 0 else "right_to_left"
    return "top_to_down" if dy > 0 else "bottom_to_up"


def classify_easing(speeds: Sequence[float]) -> tuple[str, float]:
    if len(speeds) < 3 or max(speeds, default=0) <= 1e-9:
        return "linear", 0.25
    peak = max(speeds)
    norm = [s / peak for s in speeds]
    first, last = norm[0], norm[-1]
    mid = mean(norm[max(0, len(norm)//3): max(1, 2*len(norm)//3)])
    variance = mean(abs(x - mean(norm)) for x in norm)
    if variance < 0.08:
        return "linear", 0.75
    if first < mid and last < mid:
        return "ease_in_out", min(0.92, 0.55 + variance)
    if first >= mid and last < mid:
        return "ease_out", min(0.9, 0.5 + variance)
    if first < mid and last >= mid:
        return "ease_in", min(0.9, 0.5 + variance)
    return "other", 0.45


def analyze_trajectory(points: Sequence[Point], *, fps: float) -> MotionTrack:
    if fps <= 0:
        raise ValueError("fps must be > 0")
    if len(points) < 2:
        return MotionTrack("static", 0.0, 0.0, 0, "linear", 0.0)
    deltas = _deltas(points)
    speeds = [hypot(dx, dy) * fps for dx, dy in deltas]
    acc = [b - a for a, b in zip(speeds, speeds[1:])]
    sign_changes = sum(1 for a, b in zip(acc, acc[1:]) if a * b < 0)
    total_dx = points[-1][0] - points[0][0]
    total_dy = points[-1][1] - points[0][1]
    easing, ease_conf = classify_easing(speeds)
    displacement = hypot(total_dx, total_dy)
    coherence = displacement / max(1e-9, sum(hypot(dx, dy) for dx, dy in deltas))
    return MotionTrack(
        direction=dominant_direction(total_dx, total_dy),
        displacement=round(displacement, 6),
        mean_speed=round(mean(speeds), 6),
        acceleration_sign_changes=sign_changes,
        easing_guess=easing,
        confidence=round(min(1.0, 0.45 * coherence + 0.55 * ease_conf), 3),
    )


def separate_camera_local_motion(global_vectors: Sequence[Point], local_vectors: Sequence[Point], *, ratio: float = 1.8) -> dict:
    """Coarse camera/local-motion attribution from median-like mean vector magnitudes."""
    g = mean(hypot(*v) for v in global_vectors) if global_vectors else 0.0
    l = mean(hypot(*v) for v in local_vectors) if local_vectors else 0.0
    if g > l * ratio:
        label = "camera_dominant"
    elif l > g * ratio:
        label = "object_dominant"
    elif g <= 1e-8 and l <= 1e-8:
        label = "static"
    else:
        label = "mixed"
    return {"classification": label, "global_magnitude": round(g,6), "local_magnitude": round(l,6), "method": "flow_magnitude_ratio"}
