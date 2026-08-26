from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Shot:
    shot_id: str
    start_frame: int
    end_frame: int
    start_ms: int
    end_ms: int
    confidence: float
    method: str

    def to_dict(self):
        return asdict(self)


def _frame_to_ms(frame: int, fps: float) -> int:
    if fps <= 0:
        raise ValueError("fps must be > 0")
    return round(frame * 1000.0 / fps)


def detect_shots_from_change_scores(
    change_scores: Sequence[float],
    *,
    fps: float,
    threshold: float = 0.42,
    min_shot_frames: int = 4,
    method: str = "histogram_delta",
) -> list[Shot]:
    """Turn deterministic adjacent-frame change scores into complete non-overlapping shots.

    change_scores[i] represents the boundary strength between frame i and i+1.
    The returned end_frame is exclusive.
    """
    if fps <= 0:
        raise ValueError("fps must be > 0")
    if min_shot_frames < 1:
        raise ValueError("min_shot_frames must be >= 1")
    total_frames = len(change_scores) + 1
    if total_frames <= 0:
        return []

    raw_boundaries = [i + 1 for i, score in enumerate(change_scores) if score >= threshold]
    accepted: list[int] = []
    last = 0
    for boundary in raw_boundaries:
        if boundary - last >= min_shot_frames:
            accepted.append(boundary)
            last = boundary
    if accepted and total_frames - accepted[-1] < min_shot_frames:
        accepted.pop()

    boundaries = [0, *accepted, total_frames]
    shots: list[Shot] = []
    for idx, (start, end) in enumerate(zip(boundaries, boundaries[1:]), start=1):
        left_score = change_scores[start - 1] if start > 0 else 1.0
        confidence = 1.0 if start == 0 else max(0.0, min(1.0, float(left_score)))
        shots.append(
            Shot(
                shot_id=f"S{idx:02d}",
                start_frame=start,
                end_frame=end,
                start_ms=_frame_to_ms(start, fps),
                end_ms=_frame_to_ms(end, fps),
                confidence=confidence,
                method=method,
            )
        )
    return shots


def validate_shot_coverage(shots: Sequence[Shot], total_frames: int) -> list[str]:
    errors: list[str] = []
    if not shots:
        return ["no_shots"] if total_frames else []
    if shots[0].start_frame != 0:
        errors.append("timeline_does_not_start_at_zero")
    if shots[-1].end_frame != total_frames:
        errors.append("timeline_not_fully_covered")
    for prev, cur in zip(shots, shots[1:]):
        if prev.end_frame != cur.start_frame:
            errors.append(f"gap_or_overlap:{prev.shot_id}->{cur.shot_id}")
    for shot in shots:
        if shot.end_frame <= shot.start_frame:
            errors.append(f"invalid_range:{shot.shot_id}")
    return errors


def plan_keyframes(shot: Shot, *, include_adaptive: bool = False, motion_peak_frame: int | None = None) -> list[int]:
    """Stable start/mid/end keyframe plan using inclusive image frame indices."""
    last = max(shot.start_frame, shot.end_frame - 1)
    mid = (shot.start_frame + last) // 2
    frames = {shot.start_frame, mid, last}
    if include_adaptive and motion_peak_frame is not None and shot.start_frame <= motion_peak_frame < shot.end_frame:
        frames.add(motion_peak_frame)
    return sorted(frames)
