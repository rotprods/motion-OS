from __future__ import annotations

from typing import Any, Mapping


class FrameTimelineError(ValueError):
    pass


def _total_frames(pack: Mapping[str, Any]) -> int:
    meta = pack.get("video_meta", {})
    raw = meta.get("decoded_frame_count", meta.get("frame_count"))
    if raw is None:
        fps = float(meta.get("fps", 0.0))
        duration_ms = int(meta.get("duration_ms", 0))
        raw = round(duration_ms * fps / 1000.0)
    total = int(raw)
    if total <= 0:
        raise FrameTimelineError("decoded/derived frame count must be positive")
    return total


def _fps(pack: Mapping[str, Any]) -> float:
    value = float(pack.get("video_meta", {}).get("fps", 0.0))
    if value <= 0:
        raise FrameTimelineError("fps must be positive")
    return value


def _shot_index(pack: Mapping[str, Any], total_frames: int) -> list[str | None]:
    index: list[str | None] = [None] * total_frames
    shots = sorted(pack.get("shots", []), key=lambda x: int(x.get("start_frame", 0)))
    for shot in shots:
        start = int(shot.get("start_frame", 0))
        end = int(shot.get("end_frame", 0))
        if not (0 <= start < end <= total_frames):
            raise FrameTimelineError(f"invalid shot coverage {shot.get('id')}: {start}:{end}/{total_frames}")
        for frame in range(start, end):
            if index[frame] is not None:
                raise FrameTimelineError(f"overlapping shot coverage at frame {frame}")
            index[frame] = str(shot.get("id", ""))
    missing = [i for i, shot_id in enumerate(index) if shot_id is None]
    if missing:
        raise FrameTimelineError(f"shot coverage missing {len(missing)} frames; first={missing[0]}")
    return index


def compile_frame_timeline(
    feature_pack: Mapping[str, Any],
    motionstyle: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Create one source-bound record for every decoded frame.

    The function indexes evidence; it does not interpolate missing OCR/flow observations.
    Optical-flow records remain attached only to their measured source frame and retain
    the measured target frame so downstream consumers can decide whether interpolation
    is appropriate for their own, explicitly named, inference method.
    """

    fps = _fps(feature_pack)
    total_frames = _total_frames(feature_pack)
    shot_ids = _shot_index(feature_pack, total_frames)

    shot_starts: dict[int, str] = {}
    shot_ends: dict[int, str] = {}
    for shot in feature_pack.get("shots", []):
        start = int(shot["start_frame"])
        end = int(shot["end_frame"])
        shot_starts[start] = str(shot["id"])
        shot_ends[end - 1] = str(shot["id"])

    motion_by_frame: dict[int, dict[str, Any]] = {}
    motion_stats = feature_pack.get("motion_stats", {})
    if isinstance(motion_stats, Mapping) and motion_stats.get("available"):
        for track in motion_stats.get("tracks", []):
            frame = int(track.get("from_frame", -1))
            if 0 <= frame < total_frames:
                motion_by_frame[frame] = {
                    "from_frame": frame,
                    "to_frame": int(track.get("to_frame", frame)),
                    "global_dx": float(track.get("global_dx", 0.0)),
                    "global_dy": float(track.get("global_dy", 0.0)),
                    "global_magnitude": float(track.get("global_magnitude", 0.0)),
                    "local_residual_median": float(track.get("local_residual_median", 0.0)),
                    "motion_median": float(track.get("motion_median", 0.0)),
                    "camera_likelihood": float(track.get("camera_likelihood", 0.0)),
                    "authority": "measured",
                    "method": str(motion_stats.get("method", "optical_flow")),
                }

    text_by_frame: dict[int, list[dict[str, Any]]] = {}
    for item in feature_pack.get("ocr", []):
        frame = int(item.get("frame", -1))
        if 0 <= frame < total_frames:
            text_by_frame.setdefault(frame, []).append(
                {
                    "id": item.get("id"),
                    "continuity_id": item.get("continuity_id"),
                    "text": item.get("text"),
                    "bbox": item.get("bbox"),
                    "confidence": item.get("confidence"),
                    "method": item.get("method"),
                    "evidence_refs": list(item.get("evidence_refs", [])),
                    "authority": "measured",
                }
            )

    keyframes_by_frame: dict[int, list[str]] = {}
    for keyframe in feature_pack.get("keyframes", []):
        frame = int(keyframe.get("frame", -1))
        if 0 <= frame < total_frames:
            keyframes_by_frame.setdefault(frame, []).append(str(keyframe.get("id", "")))

    audio_by_frame: dict[int, list[dict[str, Any]]] = {}
    audio = feature_pack.get("audio_stats", {})
    if isinstance(audio, Mapping) and audio.get("available"):
        for index, onset in enumerate(audio.get("onsets_ms", [])):
            onset_ms = int(round(float(onset)))
            frame = int(round(onset_ms * fps / 1000.0))
            if 0 <= frame < total_frames:
                audio_by_frame.setdefault(frame, []).append(
                    {
                        "id": f"onset_{index:04d}",
                        "type": "onset_candidate",
                        "at_ms": onset_ms,
                        "authority": "measured",
                        "method": str(audio.get("method", "audio_envelope")),
                    }
                )

    choreography_by_frame: dict[int, list[dict[str, Any]]] = {}
    transition_by_frame: dict[int, list[dict[str, Any]]] = {}
    if motionstyle:
        for shot in motionstyle.get("shots", []):
            for step in shot.get("micro_choreography", []):
                frame = int(step.get("at_frame", round(int(step.get("at_ms", 0)) * fps / 1000.0)))
                if 0 <= frame < total_frames:
                    normalized = dict(step)
                    normalized.setdefault("authority", "inferred")
                    choreography_by_frame.setdefault(frame, []).append(normalized)
            transition = shot.get("transition_spec", {})
            if transition:
                at_ms = int(transition.get("at_ms_global", shot.get("end_ms", 0)))
                frame = min(total_frames - 1, max(0, int(round(at_ms * fps / 1000.0))))
                transition_by_frame.setdefault(frame, []).append(
                    {
                        "type": transition.get("type", "unknown"),
                        "at_ms": at_ms,
                        "supporting_fx": list(transition.get("supporting_fx", [])),
                        "authority": "inferred",
                    }
                )

    timeline: list[dict[str, Any]] = []
    for frame in range(total_frames):
        boundary: str | None = None
        if frame in shot_starts:
            boundary = "start"
        if frame in shot_ends:
            boundary = "end" if boundary is None else "single_frame_shot"
        timeline.append(
            {
                "frame": frame,
                "at_ms": int(round(frame * 1000.0 / fps)),
                "shot_id": shot_ids[frame],
                "shot_boundary": boundary,
                "motion_observation": motion_by_frame.get(frame),
                "text_observations": sorted(text_by_frame.get(frame, []), key=lambda x: str(x.get("id"))),
                "audio_events": audio_by_frame.get(frame, []),
                "keyframe_refs": sorted(keyframes_by_frame.get(frame, [])),
                "choreography_events": choreography_by_frame.get(frame, []),
                "transition_events": transition_by_frame.get(frame, []),
                "authority": {
                    "frame_index": "measured_decode",
                    "motion": "measured" if frame in motion_by_frame else "unavailable_at_frame",
                    "text": "measured" if frame in text_by_frame else "unavailable_at_frame",
                    "audio": "measured" if frame in audio_by_frame else "no_onset_observed_at_frame",
                },
            }
        )
    validate_frame_timeline(timeline, total_frames=total_frames)
    return timeline


def validate_frame_timeline(timeline: list[Mapping[str, Any]], *, total_frames: int) -> None:
    if len(timeline) != total_frames:
        raise FrameTimelineError(f"timeline length {len(timeline)} != total_frames {total_frames}")
    frames = [int(item.get("frame", -1)) for item in timeline]
    expected = list(range(total_frames))
    if frames != expected:
        raise FrameTimelineError("frame timeline must cover every decoded frame exactly once and in order")
    if any(item.get("shot_id") in {None, ""} for item in timeline):
        raise FrameTimelineError("every frame must resolve to a shot")
