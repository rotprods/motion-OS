from __future__ import annotations

from bisect import bisect_left
from statistics import mean
from typing import Iterable, Sequence


def nearest_event_delta_ms(at_ms: int, events_ms: Sequence[int]) -> int | None:
    if not events_ms:
        return None
    events = sorted(events_ms)
    i = bisect_left(events, at_ms)
    candidates = []
    if i < len(events):
        candidates.append(events[i])
    if i > 0:
        candidates.append(events[i-1])
    return min((abs(at_ms - e) for e in candidates), default=None)


def av_sync_metrics(visual_events_ms: Sequence[int], audio_events_ms: Sequence[int], *, tolerance_ms: int = 90) -> dict:
    deltas = [nearest_event_delta_ms(v, audio_events_ms) for v in visual_events_ms]
    valid = [d for d in deltas if d is not None]
    if not visual_events_ms:
        return {"coverage": 0.0, "hit_rate": 0.0, "mean_abs_delta_ms": None, "p95_abs_delta_ms": None, "method": "nearest_event"}
    ordered = sorted(valid)
    p95 = ordered[min(len(ordered)-1, max(0, round(0.95*(len(ordered)-1))))] if ordered else None
    return {
        "coverage": round(len(valid) / len(visual_events_ms), 4),
        "hit_rate": round(sum(d <= tolerance_ms for d in valid) / len(visual_events_ms), 4),
        "mean_abs_delta_ms": round(mean(valid), 3) if valid else None,
        "p95_abs_delta_ms": p95,
        "tolerance_ms": tolerance_ms,
        "method": "nearest_event",
    }


def coarse_audio_density(events_ms: Sequence[int], duration_ms: int) -> float:
    if duration_ms <= 0:
        return 0.0
    return round(len(events_ms) / (duration_ms / 1000.0), 4)


def transcript_coverage(segments: Iterable[dict], duration_ms: int) -> dict:
    spans = []
    for segment in segments:
        start = max(0, int(segment.get("start_ms", 0)))
        end = min(duration_ms, int(segment.get("end_ms", 0)))
        if end > start:
            spans.append((start, end))
    if duration_ms <= 0:
        return {"covered_ms": 0, "ratio": 0.0}
    spans.sort()
    merged = []
    for start, end in spans:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    covered = sum(end-start for start,end in merged)
    return {"covered_ms": covered, "ratio": round(covered/duration_ms, 4)}
