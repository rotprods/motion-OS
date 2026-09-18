from __future__ import annotations

import math
import re
from typing import Any, Mapping


class FrameTimelineError(ValueError):
    pass


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _frame_index(raw: object, *, name: str) -> int:
    if isinstance(raw, bool):
        raise FrameTimelineError(f"{name} must be an integer frame index")
    try:
        numeric = float(raw)
    except (TypeError, ValueError) as exc:
        raise FrameTimelineError(f"{name} must be an integer frame index") from exc
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise FrameTimelineError(f"{name} must be an integer frame index")
    return int(numeric)


def _finite_measurement(raw: object, *, name: str, nonnegative: bool = False) -> float:
    if isinstance(raw, bool):
        raise FrameTimelineError(f"{name} must be a finite number")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise FrameTimelineError(f"{name} must be a finite number") from exc
    if not math.isfinite(value) or (nonnegative and value < 0):
        qualifier = "finite non-negative number" if nonnegative else "finite number"
        raise FrameTimelineError(f"{name} must be a {qualifier}")
    return value


def _strict_available(mapping: Mapping[str, Any], *, name: str) -> bool:
    raw = mapping.get("available", False)
    if type(raw) is not bool:
        raise FrameTimelineError(f"{name}.available must be a JSON boolean")
    return raw


def _validate_source_identity(pack: Mapping[str, Any]) -> None:
    raw = pack.get("video_meta", {}).get("source_sha256")
    if not isinstance(raw, str) or not SHA256_RE.fullmatch(raw):
        raise FrameTimelineError("source_sha256 must be a lowercase 64-character SHA-256")


def _total_frames(pack: Mapping[str, Any]) -> int:
    """Return authoritative decoded frame count; never derive it from duration.

    A timeline that claims every decoded frame must be anchored to an actual decode
    count. Duration×fps is an estimate and cannot satisfy frame-accurate authority.
    Approximate/template-only workflows must make approximation explicit upstream
    instead of laundering an estimate through this authoritative timeline builder.
    """
    meta = pack.get("video_meta", {})
    raw = meta.get("decoded_frame_count")
    if raw is None:
        raise FrameTimelineError("decoded_frame_count is required for frame-authoritative timeline")
    if isinstance(raw, bool):
        raise FrameTimelineError("decoded_frame_count must be an integer, not boolean")
    try:
        numeric = float(raw)
    except (TypeError, ValueError) as exc:
        raise FrameTimelineError("decoded_frame_count must be a positive integer") from exc
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise FrameTimelineError("decoded_frame_count must be a positive integer")
    total = int(numeric)
    if total <= 0:
        raise FrameTimelineError("decoded_frame_count must be positive")
    return total


def _fps(pack: Mapping[str, Any]) -> float:
    raw = pack.get("video_meta", {}).get("fps", 0.0)
    if isinstance(raw, bool):
        raise FrameTimelineError("fps must be a finite positive number")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise FrameTimelineError("fps must be a finite positive number") from exc
    if not math.isfinite(value) or value <= 0:
        raise FrameTimelineError("fps must be a finite positive number")
    return value


def _shot_index(pack: Mapping[str, Any], total_frames: int) -> list[str | None]:
    index: list[str | None] = [None] * total_frames
    shots = sorted(pack.get("shots", []), key=lambda x: _frame_index(x.get("start_frame", 0), name="shot.start_frame"))
    for shot in shots:
        start = _frame_index(shot.get("start_frame", 0), name="shot.start_frame")
        end = _frame_index(shot.get("end_frame", 0), name="shot.end_frame")
        shot_id = str(shot.get("id", ""))
        if not shot_id:
            raise FrameTimelineError("shot id is required")
        if not (0 <= start < end <= total_frames):
            raise FrameTimelineError(f"invalid shot coverage {shot.get('id')}: {start}:{end}/{total_frames}")
        for frame in range(start, end):
            if index[frame] is not None:
                raise FrameTimelineError(f"overlapping shot coverage at frame {frame}")
            index[frame] = shot_id
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

    _validate_source_identity(feature_pack)
    fps = _fps(feature_pack)
    total_frames = _total_frames(feature_pack)
    shot_ids = _shot_index(feature_pack, total_frames)

    shot_starts: dict[int, str] = {}
    shot_ends: dict[int, str] = {}
    for shot in feature_pack.get("shots", []):
        start = _frame_index(shot["start_frame"], name="shot.start_frame")
        end = _frame_index(shot["end_frame"], name="shot.end_frame")
        shot_starts[start] = str(shot["id"])
        shot_ends[end - 1] = str(shot["id"])

    motion_by_frame: dict[int, dict[str, Any]] = {}
    motion_stats = feature_pack.get("motion_stats", {})
    if isinstance(motion_stats, Mapping) and _strict_available(motion_stats, name="motion_stats"):
        tracks = motion_stats.get("tracks", [])
        if not isinstance(tracks, list):
            raise FrameTimelineError("motion_stats.tracks must be a list")
        for track in tracks:
            if not isinstance(track, Mapping):
                raise FrameTimelineError("motion track must be an object")
            frame = _frame_index(track.get("from_frame", -1), name="motion.from_frame")
            to_frame = _frame_index(track.get("to_frame", frame), name="motion.to_frame")
            if not (0 <= frame < total_frames):
                raise FrameTimelineError(f"motion.from_frame out of range: {frame}")
            if not (frame < to_frame <= total_frames):
                raise FrameTimelineError(f"motion.to_frame must advance within decoded frame bounds: {frame}->{to_frame}")
            if frame in motion_by_frame:
                raise FrameTimelineError(f"duplicate motion observation for frame {frame}")
            motion_by_frame[frame] = {
                "from_frame": frame,
                "to_frame": to_frame,
                "global_dx": _finite_measurement(track.get("global_dx", 0.0), name="motion.global_dx"),
                "global_dy": _finite_measurement(track.get("global_dy", 0.0), name="motion.global_dy"),
                "global_magnitude": _finite_measurement(track.get("global_magnitude", 0.0), name="motion.global_magnitude", nonnegative=True),
                "local_residual_median": _finite_measurement(track.get("local_residual_median", 0.0), name="motion.local_residual_median", nonnegative=True),
                "motion_median": _finite_measurement(track.get("motion_median", 0.0), name="motion.motion_median", nonnegative=True),
                "camera_likelihood": _finite_measurement(track.get("camera_likelihood", 0.0), name="motion.camera_likelihood", nonnegative=True),
                "authority": "measured",
                "method": str(motion_stats.get("method", "optical_flow")),
            }
            if motion_by_frame[frame]["camera_likelihood"] > 1.0:
                raise FrameTimelineError("motion.camera_likelihood must be between 0 and 1")

    text_by_frame: dict[int, list[dict[str, Any]]] = {}
    for item in feature_pack.get("ocr", []):
        if not isinstance(item, Mapping):
            raise FrameTimelineError("OCR observation must be an object")
        frame = _frame_index(item.get("frame", -1), name="ocr.frame")
        if not (0 <= frame < total_frames):
            raise FrameTimelineError(f"ocr.frame out of range: {frame}")
        confidence = item.get("confidence")
        if confidence is not None:
            confidence = _finite_measurement(confidence, name="ocr.confidence", nonnegative=True)
            if confidence > 1.0:
                raise FrameTimelineError("ocr.confidence must be between 0 and 1")
        text_by_frame.setdefault(frame, []).append(
            {
                "id": item.get("id"),
                "continuity_id": item.get("continuity_id"),
                "text": item.get("text"),
                "bbox": item.get("bbox"),
                "confidence": confidence,
                "method": item.get("method"),
                "evidence_refs": list(item.get("evidence_refs", [])),
                "authority": "measured",
            }
        )

    keyframes_by_frame: dict[int, list[str]] = {}
    for keyframe in feature_pack.get("keyframes", []):
        if not isinstance(keyframe, Mapping):
            raise FrameTimelineError("keyframe must be an object")
        frame = _frame_index(keyframe.get("frame", -1), name="keyframe.frame")
        if not (0 <= frame < total_frames):
            raise FrameTimelineError(f"keyframe.frame out of range: {frame}")
        keyframes_by_frame.setdefault(frame, []).append(str(keyframe.get("id", "")))

    audio_by_frame: dict[int, list[dict[str, Any]]] = {}
    audio = feature_pack.get("audio_stats", {})
    if isinstance(audio, Mapping) and _strict_available(audio, name="audio_stats"):
        onsets = audio.get("onsets_ms", [])
        if not isinstance(onsets, list):
            raise FrameTimelineError("audio_stats.onsets_ms must be a list")
        for index, onset in enumerate(onsets):
            onset_value = _finite_measurement(onset, name="audio.onset_ms", nonnegative=True)
            onset_ms = int(round(onset_value))
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
        shots = motionstyle.get("shots", [])
        if not isinstance(shots, list):
            raise FrameTimelineError("motionstyle.shots must be a list")
        for shot in shots:
            if not isinstance(shot, Mapping):
                raise FrameTimelineError("motionstyle shot must be an object")
            for step in shot.get("micro_choreography", []):
                if not isinstance(step, Mapping):
                    raise FrameTimelineError("micro_choreography step must be an object")
                if "at_frame" in step:
                    frame = _frame_index(step.get("at_frame"), name="micro_choreography.at_frame")
                else:
                    at_ms = _finite_measurement(step.get("at_ms", 0), name="micro_choreography.at_ms", nonnegative=True)
                    frame = int(round(at_ms * fps / 1000.0))
                if 0 <= frame < total_frames:
                    normalized = dict(step)
                    normalized["authority"] = "inferred"
                    choreography_by_frame.setdefault(frame, []).append(normalized)
            transition = shot.get("transition_spec", {})
            if transition:
                if not isinstance(transition, Mapping):
                    raise FrameTimelineError("transition_spec must be an object")
                at_ms = int(round(_finite_measurement(transition.get("at_ms_global", shot.get("end_ms", 0)), name="transition.at_ms", nonnegative=True)))
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
                    "frame_count": "decoded_frame_count",
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
