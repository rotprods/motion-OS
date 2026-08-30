from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable, Mapping
import json
import math

from .frame_timeline import compile_frame_timeline, validate_frame_timeline


SCHEMA_VERSION = "1.0.0"
REPLICATION_MODES = {"RECONSTRUCT_EXACT", "STRUCTURAL_TEMPLATE", "STYLE_TRANSFER"}


class EditingTemplateError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _histogram(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(str(v) for v in values if str(v)).items()))


def _round(value: float, digits: int = 6) -> float:
    if not math.isfinite(value):
        return 0.0
    return round(float(value), digits)


def _source_meta(pack: Mapping[str, Any]) -> dict[str, Any]:
    meta = pack.get("video_meta", {})
    source_sha = str(meta.get("source_sha256", ""))
    if len(source_sha) != 64:
        raise EditingTemplateError("FeaturePack must carry a 64-character source_sha256")
    fps = float(meta.get("fps", 0.0))
    if fps <= 0:
        raise EditingTemplateError("FeaturePack fps must be positive")
    resolution = dict(meta.get("resolution", {}))
    if int(resolution.get("w", 0)) <= 0 or int(resolution.get("h", 0)) <= 0:
        raise EditingTemplateError("FeaturePack resolution must be positive")
    duration_ms = int(meta.get("duration_ms", 0))
    total_frames = int(meta.get("decoded_frame_count", meta.get("frame_count", round(duration_ms * fps / 1000.0))))
    if total_frames <= 0:
        raise EditingTemplateError("FeaturePack frame count must be positive")
    return {
        "sha256": source_sha,
        "duration_ms": duration_ms,
        "fps": fps,
        "resolution": {"w": int(resolution["w"]), "h": int(resolution["h"])},
        "aspect_ratio": str(meta.get("aspect_ratio", f"{resolution['w']}:{resolution['h']}")),
        "total_frames": total_frames,
    }


def _shot_durations(pack: Mapping[str, Any]) -> list[int]:
    return [max(0, int(s.get("end_ms", 0)) - int(s.get("start_ms", 0))) for s in pack.get("shots", [])]


def _cadence_class(median_ms: float) -> str:
    if median_ms <= 900:
        return "hyper"
    if median_ms <= 1600:
        return "fast"
    if median_ms <= 3200:
        return "medium"
    return "slow"


def _nearest_distance(value: int, candidates: list[int]) -> int | None:
    if not candidates:
        return None
    return min(abs(value - candidate) for candidate in candidates)


def build_editing_signature(feature_pack: Mapping[str, Any], motionstyle: Mapping[str, Any]) -> dict[str, Any]:
    source = _source_meta(feature_pack)
    shots = list(feature_pack.get("shots", []))
    durations = _shot_durations(feature_pack)
    duration_s = max(0.001, source["duration_ms"] / 1000.0)
    mean_ms = mean(durations) if durations else source["duration_ms"]
    median_ms = median(durations) if durations else source["duration_ms"]
    variance = mean((x - mean_ms) ** 2 for x in durations) if durations else 0.0
    cv = math.sqrt(variance) / max(1.0, mean_ms)

    motion_stats = feature_pack.get("motion_stats", {})
    motion_tracks = list(motion_stats.get("tracks", [])) if isinstance(motion_stats, Mapping) else []
    motion_values = [float(x.get("motion_median", 0.0)) for x in motion_tracks]
    camera_values = [float(x.get("camera_likelihood", 0.0)) for x in motion_tracks]
    global_values = [float(x.get("global_magnitude", 0.0)) for x in motion_tracks]
    local_values = [float(x.get("local_residual_median", 0.0)) for x in motion_tracks]

    ms_shots = list(motionstyle.get("shots", []))
    transitions = [str(s.get("transition_spec", {}).get("type", "unknown")) for s in ms_shots]
    cameras = [str(s.get("camera_plan", {}).get("motion", "unknown")) for s in ms_shots]
    rigs = [str(s.get("camera_plan", {}).get("rig_id", "unknown")) for s in ms_shots]
    framings = [str(s.get("camera_plan", {}).get("framing", "other")) for s in ms_shots]

    ocr = list(feature_pack.get("ocr", []))
    continuity = {str(x.get("continuity_id")) for x in ocr if x.get("continuity_id")}
    occupancy: list[float] = []
    for item in ocr:
        bbox = item.get("bbox")
        if isinstance(bbox, list) and len(bbox) == 4:
            occupancy.append(max(0.0, float(bbox[2]) * float(bbox[3])))

    audio = feature_pack.get("audio_stats", {})
    audio_available = bool(isinstance(audio, Mapping) and audio.get("available"))
    onsets = sorted(int(round(float(x))) for x in audio.get("onsets_ms", [])) if audio_available else []
    cut_times = [int(s.get("end_ms", 0)) for s in shots[:-1]]
    tolerance = 90
    distances = [d for cut in cut_times if (d := _nearest_distance(cut, onsets)) is not None]
    sync_ratio = sum(d <= tolerance for d in distances) / len(cut_times) if cut_times else 0.0

    color_stats = feature_pack.get("color_stats", {})
    layout_stats = feature_pack.get("layout_stats", {})
    fx_stats = feature_pack.get("fx_stats", {})
    asset_stats = feature_pack.get("asset_stats", {})

    return {
        "temporal": {
            "shot_count": len(shots),
            "mean_shot_ms": _round(mean_ms, 3),
            "median_shot_ms": _round(median_ms, 3),
            "min_shot_ms": min(durations, default=source["duration_ms"]),
            "max_shot_ms": max(durations, default=source["duration_ms"]),
            "cut_rate_per_sec": _round(max(0, len(shots) - 1) / duration_s),
            "cuts_per_minute": _round(max(0, len(shots) - 1) * 60.0 / duration_s, 3),
            "shot_duration_cv": _round(cv),
            "cadence_class": _cadence_class(median_ms),
        },
        "motion": {
            "provider_available": bool(motion_stats.get("available")) if isinstance(motion_stats, Mapping) else False,
            "mean_motion_median": _round(mean(motion_values) if motion_values else 0.0),
            "peak_motion_median": _round(max(motion_values, default=0.0)),
            "mean_global_magnitude": _round(mean(global_values) if global_values else 0.0),
            "mean_local_residual": _round(mean(local_values) if local_values else 0.0),
            "mean_camera_likelihood": _round(mean(camera_values) if camera_values else 0.0),
            "track_count": len(motion_tracks),
            "authority": str(motion_stats.get("authority", "unavailable")) if isinstance(motion_stats, Mapping) else "unavailable",
        },
        "transitions": {
            "histogram": _histogram(transitions),
            "sequence": transitions,
            "authority": "inferred_evidence_bound",
        },
        "camera": {
            "motion_histogram": _histogram(cameras),
            "rig_histogram": _histogram(rigs),
            "framing_histogram": _histogram(framings),
            "mean_camera_likelihood": _round(mean(camera_values) if camera_values else 0.0),
        },
        "typography": {
            "ocr_observations": len(ocr),
            "continuity_tracks": len(continuity),
            "observations_per_sec": _round(len(ocr) / duration_s),
            "mean_observed_bbox_area": _round(mean(occupancy) if occupancy else 0.0),
            "authority": "measured" if ocr else "unavailable_or_no_text_observed",
        },
        "audio": {
            "available": audio_available,
            "onset_count": len(onsets),
            "onset_rate_per_sec": _round(len(onsets) / duration_s),
            "cut_onset_sync_ratio": _round(sync_ratio),
            "sync_tolerance_ms": tolerance,
            "mean_cut_to_nearest_onset_ms": _round(mean(distances), 3) if distances else None,
            "authority": str(audio.get("authority", "unavailable")) if isinstance(audio, Mapping) else "unavailable",
        },
        "visual": {
            "palette": list(color_stats.get("palette", [])) if isinstance(color_stats, Mapping) else [],
            "gradients": list(color_stats.get("gradients", [])) if isinstance(color_stats, Mapping) else [],
            "layout": dict(layout_stats) if isinstance(layout_stats, Mapping) else {},
            "fx_labels": list(fx_stats.get("labels", [])) if isinstance(fx_stats, Mapping) else [],
            "materials": list(asset_stats.get("materials", [])) if isinstance(asset_stats, Mapping) else [],
            "style_families": list(motionstyle.get("style_system", {}).get("style_family", [])),
        },
    }


def _evidence_refs_for_shots(feature_pack: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for shot in feature_pack.get("shots", []):
        refs.append(f"shot:{shot.get('id')}")
    return refs


def _invariants(
    feature_pack: Mapping[str, Any],
    motionstyle: Mapping[str, Any],
    signature: Mapping[str, Any],
    mode: str,
) -> list[dict[str, Any]]:
    shot_refs = _evidence_refs_for_shots(feature_pack)
    invariants: list[dict[str, Any]] = []

    temporal_class = "HARD_INVARIANT" if mode in {"RECONSTRUCT_EXACT", "STRUCTURAL_TEMPLATE"} else "SOFT_INVARIANT"
    invariants.append({
        "id": "inv_temporal_cadence",
        "class": temporal_class,
        "domain": "temporal",
        "value": dict(signature["temporal"]),
        "authority": "measured_heuristic",
        "confidence": 1.0,
        "evidence_refs": shot_refs,
    })

    motion = signature["motion"]
    if motion.get("provider_available"):
        invariants.append({
            "id": "inv_motion_energy",
            "class": "HARD_INVARIANT" if mode == "RECONSTRUCT_EXACT" else "SOFT_INVARIANT",
            "domain": "motion",
            "value": {
                "mean_motion_median": motion.get("mean_motion_median"),
                "peak_motion_median": motion.get("peak_motion_median"),
                "mean_camera_likelihood": motion.get("mean_camera_likelihood"),
            },
            "authority": "measured",
            "confidence": 0.95,
            "evidence_refs": ["feature_pack:motion_stats"],
        })

    transitions = signature["transitions"]
    if transitions.get("histogram"):
        invariants.append({
            "id": "inv_transition_grammar",
            "class": "HARD_INVARIANT" if mode in {"RECONSTRUCT_EXACT", "STRUCTURAL_TEMPLATE"} else "SOFT_INVARIANT",
            "domain": "transition",
            "value": {"histogram": transitions["histogram"]},
            "authority": "inferred",
            "confidence": 0.82,
            "evidence_refs": [f"motionstyle:shot:{s.get('id')}" for s in motionstyle.get("shots", [])],
        })

    camera = signature["camera"]
    invariants.append({
        "id": "inv_camera_grammar",
        "class": "SOFT_INVARIANT" if mode == "STYLE_TRANSFER" else "HARD_INVARIANT",
        "domain": "camera",
        "value": dict(camera),
        "authority": "inferred",
        "confidence": 0.8,
        "evidence_refs": [f"motionstyle:camera:{s.get('id')}" for s in motionstyle.get("shots", [])],
    })

    visual = signature["visual"]
    palette = visual.get("palette", [])
    if palette:
        invariants.append({
            "id": "inv_palette_behavior",
            "class": "SOURCE_LOCK" if mode == "RECONSTRUCT_EXACT" else "SOFT_INVARIANT",
            "domain": "visual",
            "value": palette,
            "authority": "measured",
            "confidence": 0.95,
            "evidence_refs": ["feature_pack:color_stats"],
        })

    layout = visual.get("layout", {})
    if layout:
        invariants.append({
            "id": "inv_layout_behavior",
            "class": "HARD_INVARIANT" if mode == "STRUCTURAL_TEMPLATE" else "SOFT_INVARIANT",
            "domain": "layout",
            "value": layout,
            "authority": "measured_heuristic",
            "confidence": 0.72,
            "evidence_refs": ["feature_pack:layout_stats"],
        })

    typography = signature["typography"]
    if typography.get("ocr_observations", 0):
        invariants.append({
            "id": "inv_typography_rhythm",
            "class": "HARD_INVARIANT" if mode == "STRUCTURAL_TEMPLATE" else "SOFT_INVARIANT",
            "domain": "typography",
            "value": dict(typography),
            "authority": "measured",
            "confidence": 0.9,
            "evidence_refs": ["feature_pack:ocr"],
        })

    audio = signature["audio"]
    if audio.get("available"):
        invariants.append({
            "id": "inv_audio_edit_relationship",
            "class": "SOFT_INVARIANT" if mode == "STYLE_TRANSFER" else "HARD_INVARIANT",
            "domain": "audio",
            "value": {
                "onset_rate_per_sec": audio.get("onset_rate_per_sec"),
                "cut_onset_sync_ratio": audio.get("cut_onset_sync_ratio"),
                "sync_tolerance_ms": audio.get("sync_tolerance_ms"),
            },
            "authority": "measured_heuristic",
            "confidence": 0.88,
            "evidence_refs": ["feature_pack:audio_stats", "feature_pack:shots"],
        })

    style_families = visual.get("style_families", [])
    if style_families:
        invariants.append({
            "id": "inv_style_family",
            "class": "SOFT_INVARIANT",
            "domain": "visual",
            "value": style_families,
            "authority": "inferred",
            "confidence": max(float(x.get("confidence", 0.0)) for x in style_families),
            "evidence_refs": sorted({str(ref) for item in style_families for ref in item.get("evidence_refs", [])}),
        })

    if mode == "RECONSTRUCT_EXACT":
        invariants.append({
            "id": "source_lock_identity",
            "class": "SOURCE_LOCK",
            "domain": "brand",
            "value": {"source_sha256": feature_pack.get("video_meta", {}).get("source_sha256")},
            "authority": "measured",
            "confidence": 1.0,
            "evidence_refs": ["feature_pack:video_meta:source_sha256"],
        })

    return invariants


def _text_tracks(feature_pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for item in feature_pack.get("ocr", []):
        continuity_id = str(item.get("continuity_id") or item.get("id") or "text_unknown")
        groups.setdefault(continuity_id, []).append(item)
    result: list[dict[str, Any]] = []
    for continuity_id, items in sorted(groups.items()):
        ordered = sorted(items, key=lambda x: int(x.get("frame", 0)))
        texts = [str(x.get("text", "")) for x in ordered if str(x.get("text", ""))]
        lengths = [len(x) for x in texts]
        bboxes = [x.get("bbox") for x in ordered if isinstance(x.get("bbox"), list) and len(x.get("bbox")) == 4]
        result.append({
            "continuity_id": continuity_id,
            "observed_texts": texts,
            "min_chars": min(lengths, default=0),
            "max_chars": max(lengths, default=0),
            "first_frame": int(ordered[0].get("frame", 0)),
            "last_frame": int(ordered[-1].get("frame", 0)),
            "representative_bbox": bboxes[len(bboxes) // 2] if bboxes else None,
            "evidence_refs": sorted({str(ref) for item in ordered for ref in item.get("evidence_refs", [])}),
        })
    return result


def _slots(feature_pack: Mapping[str, Any], mode: str) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = [
        {
            "slot_id": "PRIMARY_HERO",
            "role": "PRIMARY_HERO",
            "media_type": "generic",
            "required": True,
            "constraints": {"function": "dominant attention target; replace with project-specific hero content"},
            "source_binding": None,
        }
    ]
    tracks = _text_tracks(feature_pack)
    if mode == "STYLE_TRANSFER":
        if tracks:
            slots.append({
                "slot_id": "PRIMARY_COPY",
                "role": "PRIMARY_COPY",
                "media_type": "text",
                "required": True,
                "constraints": {
                    "track_count_reference": len(tracks),
                    "char_length_reference": [min((x["min_chars"] for x in tracks), default=0), max((x["max_chars"] for x in tracks), default=0)],
                    "literal_source_copy_forbidden": True,
                },
                "source_binding": None,
            })
        return slots

    for index, track in enumerate(tracks, 1):
        slot = {
            "slot_id": f"TEXT_{index:02d}",
            "role": "PRIMARY_COPY" if index == 1 else "SECONDARY_COPY",
            "media_type": "text",
            "required": index == 1,
            "constraints": {
                "min_chars": track["min_chars"],
                "max_chars": track["max_chars"],
                "reference_bbox": track["representative_bbox"],
                "first_frame": track["first_frame"],
                "last_frame": track["last_frame"],
                "literal_source_copy_forbidden": mode != "RECONSTRUCT_EXACT",
            },
            "source_binding": None,
        }
        if mode == "RECONSTRUCT_EXACT":
            slot["source_binding"] = {
                "continuity_id": track["continuity_id"],
                "observed_texts": track["observed_texts"],
                "evidence_refs": track["evidence_refs"],
            }
        slots.append(slot)
    return slots


def _role(index: int, count: int) -> str:
    if count <= 1:
        return "hero"
    if index == 0:
        return "hook"
    if index == count - 1:
        return "resolve"
    ratio = index / max(1, count - 1)
    if ratio < 0.45:
        return "development"
    if ratio < 0.8:
        return "escalation"
    return "payoff"


def _timeline(feature_pack: Mapping[str, Any], motionstyle: Mapping[str, Any], slots: list[Mapping[str, Any]]) -> dict[str, Any]:
    shots = list(feature_pack.get("shots", []))
    ms_by_id = {str(s.get("id")): s for s in motionstyle.get("shots", [])}
    text_slots = [str(s["slot_id"]) for s in slots if s.get("media_type") == "text"]
    beats: list[dict[str, Any]] = []
    previous_transition: str | None = None
    for index, shot in enumerate(shots):
        shot_id = str(shot.get("id", f"shot_{index:03d}"))
        ms_shot = ms_by_id.get(shot_id, {})
        transition = str(ms_shot.get("transition_spec", {}).get("type", "unknown"))
        beat = {
            "id": f"beat_{index + 1:03d}",
            "source_shot_id": shot_id,
            "start_ms": int(shot.get("start_ms", 0)),
            "end_ms": int(shot.get("end_ms", 0)),
            "from_frame": int(shot.get("start_frame", 0)),
            "to_frame": max(int(shot.get("start_frame", 0)), int(shot.get("end_frame", 0)) - 1),
            "role": _role(index, len(shots)),
            "slot_refs": (["PRIMARY_HERO"] + text_slots[:1]) if index == 0 else ["PRIMARY_HERO"],
            "transition_in": previous_transition,
            "transition_out": transition,
            "camera": dict(ms_shot.get("camera_plan", {})),
            "composition_tokens": list(ms_shot.get("composition_tokens", [])),
        }
        beats.append(beat)
        previous_transition = transition
    return {"beats": beats, "coverage": "contiguous_full_duration"}


def _motion_grammar(motionstyle: Mapping[str, Any], mode: str) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    for shot in motionstyle.get("shots", []):
        for raw in shot.get("micro_choreography", []):
            step = dict(raw)
            if mode != "RECONSTRUCT_EXACT":
                # Keep behavior/timing but prevent a source-specific layer name from becoming a hard dependency.
                step["target"] = "TEMPLATE_TARGET"
            steps.append(step)
    verbs = sorted({str(x.get("action", "other")) for x in steps})
    easing = sorted({str(x.get("ease", "linear")) for x in steps})
    camera_motions = sorted({str(s.get("camera_plan", {}).get("motion", "unknown")) for s in motionstyle.get("shots", [])})
    transitions = sorted({str(s.get("transition_spec", {}).get("type", "unknown")) for s in motionstyle.get("shots", [])})
    return {
        "verbs": verbs,
        "easing": easing,
        "camera_motions": camera_motions,
        "transition_families": transitions,
        "micro_choreography": steps,
    }


def _visual_grammar(feature_pack: Mapping[str, Any], motionstyle: Mapping[str, Any], mode: str) -> dict[str, Any]:
    style = motionstyle.get("style_system", {})
    color = feature_pack.get("color_stats", {})
    layout = feature_pack.get("layout_stats", {})
    asset = feature_pack.get("asset_stats", {})
    fx = feature_pack.get("fx_stats", {})
    return {
        "style_families": list(style.get("style_family", [])),
        "palette": list(color.get("palette", [])) if isinstance(color, Mapping) else [],
        "gradients": list(color.get("gradients", [])) if isinstance(color, Mapping) else [],
        "layout": dict(layout) if isinstance(layout, Mapping) else {},
        "materials": list(asset.get("materials", [])) if isinstance(asset, Mapping) else [],
        "fx": list(fx.get("labels", [])) if isinstance(fx, Mapping) else [],
        "source_palette_policy": "locked" if mode == "RECONSTRUCT_EXACT" else "replaceable_or_soft",
    }


def _audio_grammar(signature: Mapping[str, Any]) -> dict[str, Any]:
    audio = dict(signature["audio"])
    return {
        "available": bool(audio.get("available")),
        "onset_rate_per_sec": float(audio.get("onset_rate_per_sec", 0.0)),
        "cut_onset_sync_ratio": float(audio.get("cut_onset_sync_ratio", 0.0)),
        "sync_tolerance_ms": int(audio.get("sync_tolerance_ms", 90)),
        "mean_cut_to_nearest_onset_ms": audio.get("mean_cut_to_nearest_onset_ms"),
        "authority": audio.get("authority"),
        "semantic_beat_claim": False,
    }


def _compiler_targets(
    feature_pack: Mapping[str, Any],
    motionstyle: Mapping[str, Any],
    timeline: Mapping[str, Any],
    slots: list[Mapping[str, Any]],
    motion_grammar: Mapping[str, Any],
    mode: str,
) -> dict[str, Any]:
    project = dict(motionstyle.get("compiler_targets", {}).get("remotion", {}).get("project", {}))
    ae_events: list[dict[str, Any]] = []
    for step in motion_grammar.get("micro_choreography", []):
        ae_events.append({
            "at_ms": int(step.get("at_ms", 0)),
            "at_frame": int(step.get("at_frame", 0)),
            "target": step.get("target"),
            "action": step.get("action"),
            "channels": list(step.get("channels", [])),
            "from": step.get("from"),
            "to": step.get("to"),
            "duration_ms": int(step.get("duration_ms", 0)),
            "ease": str(step.get("ease", "linear")),
        })
    keyframes = []
    for kf in feature_pack.get("keyframes", []):
        item = {"frame": int(kf.get("frame", 0)), "at_ms": int(kf.get("at_ms", 0)), "shot_id": str(kf.get("shot_id", ""))}
        if mode == "RECONSTRUCT_EXACT":
            item["artifact_ref"] = kf.get("artifact_ref")
            item["sha256"] = kf.get("sha256")
        keyframes.append(item)

    return {
        "remotion": {
            "project": project,
            "beat_boundaries": list(timeline.get("beats", [])),
            "slots": [dict(s) for s in slots],
            "duration_policy": "exact_source" if mode != "STYLE_TRANSFER" else "rescalable_distribution",
        },
        "after_effects_event_map": {
            "events": ae_events,
            "timebase": "source_frames",
        },
        "generative_video": {
            "replication_mode": mode,
            "image_first_recommended": bool(feature_pack.get("ocr")),
            "preserve": ["cadence", "transition_grammar", "camera_grammar", "motion_hierarchy"],
            "content_policy": "source_bound" if mode == "RECONSTRUCT_EXACT" else "slot_driven",
            "instruction": "Animate from evidence-bound key states. Do not redesign text, logos, UI or source-locked geometry. Motion must follow the template timeline and grammar.",
        },
        "storyboard": {
            "required_keyframes": keyframes,
            "slot_driven": mode != "RECONSTRUCT_EXACT",
        },
    }


def _literal_copy_leakage(template: Mapping[str, Any], source_texts: list[str], mode: str) -> bool:
    if mode == "RECONSTRUCT_EXACT":
        return False
    haystack = _canonical_json({
        "invariants": template.get("invariants"),
        "slots": template.get("slots"),
        "timeline": template.get("timeline"),
        "motion_grammar": template.get("motion_grammar"),
        "compiler_targets": template.get("compiler_targets"),
    }).casefold()
    candidates = {text.strip().casefold() for text in source_texts if len(text.strip()) >= 3}
    return any(text in haystack for text in candidates)


def compile_editing_template(
    feature_pack: Mapping[str, Any],
    motionstyle: Mapping[str, Any],
    *,
    replication_mode: str = "STRUCTURAL_TEMPLATE",
    template_id: str | None = None,
    frame_timeline_ref: str = "frame_timeline.json",
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    mode = str(replication_mode).upper()
    if mode not in REPLICATION_MODES:
        raise EditingTemplateError(f"unsupported replication mode: {replication_mode}")

    source = _source_meta(feature_pack)
    frame_timeline = compile_frame_timeline(feature_pack, motionstyle)
    validate_frame_timeline(frame_timeline, total_frames=source["total_frames"])
    signature = build_editing_signature(feature_pack, motionstyle)
    slots = _slots(feature_pack, mode)
    timeline = _timeline(feature_pack, motionstyle, slots)
    motion_grammar = _motion_grammar(motionstyle, mode)
    visual_grammar = _visual_grammar(feature_pack, motionstyle, mode)
    audio_grammar = _audio_grammar(signature)
    invariants = _invariants(feature_pack, motionstyle, signature, mode)
    compiler_targets = _compiler_targets(feature_pack, motionstyle, timeline, slots, motion_grammar, mode)

    observed_texts = [str(x.get("text", "")) for x in feature_pack.get("ocr", [])]
    stable_id = template_id or f"editing-template-{source['sha256'][:12]}-{mode.lower()}"
    draft: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "template_id": stable_id,
        "replication_mode": mode,
        "source": {
            "sha256": source["sha256"],
            "duration_ms": source["duration_ms"],
            "fps": source["fps"],
            "resolution": source["resolution"],
            "aspect_ratio": source["aspect_ratio"],
        },
        "frame_contract": {
            "fps": source["fps"],
            "total_frames": source["total_frames"],
            "duration_ms": source["duration_ms"],
            "frame_timeline_ref": frame_timeline_ref,
            "coverage": "every_decoded_frame",
        },
        "editing_signature": signature,
        "invariants": invariants,
        "slots": slots,
        "timeline": timeline,
        "motion_grammar": motion_grammar,
        "visual_grammar": visual_grammar,
        "audio_grammar": audio_grammar,
        "evidence": {
            "claims": list(motionstyle.get("evidence", {}).get("claims", [])),
            "warnings": sorted(set(str(x) for x in feature_pack.get("warnings", [])) | set(str(x) for x in motionstyle.get("quality", {}).get("warnings", []))),
        },
        "compiler_targets": compiler_targets,
        "qa": {
            "promotion_state": "DRAFT_EXTRACTED",
            "frame_coverage": 1.0,
            "literal_copy_leakage": False,
            "warnings": [],
            "dimensions_required": [
                "temporal_fidelity",
                "transition_fidelity",
                "motion_fidelity",
                "typography_layout_fidelity",
                "color_material_fidelity",
                "audio_alignment",
                "narrative_structure",
                "content_independence",
            ],
        },
        "provenance": {
            "generator": "MOTION.OS reverse_engineering.template_compiler v1",
            "source_refs": [
                f"sha256:{source['sha256']}",
                "schemas/feature_pack.schema.json",
                "schemas/motionstyle2json.schema.json",
                "schemas/editing_template.schema.json",
            ],
        },
        "content_hash": "",
    }

    leakage = _literal_copy_leakage(draft, observed_texts, mode)
    draft["qa"]["literal_copy_leakage"] = leakage
    if leakage:
        draft["qa"]["warnings"].append("literal_source_copy_detected_in_generalizable_template")
        raise EditingTemplateError("literal source copy leaked into a generalizable template")

    hard_missing = [
        item["id"] for item in invariants
        if item["class"] == "HARD_INVARIANT" and not item.get("evidence_refs")
    ]
    if hard_missing:
        raise EditingTemplateError(f"hard invariants missing evidence: {hard_missing}")

    draft["content_hash"] = sha256(_canonical_json({**draft, "content_hash": ""}).encode("utf-8")).hexdigest()
    return draft, frame_timeline


def validate_editing_template(template: Mapping[str, Any], schema_path: str | Path = "schemas/editing_template.schema.json") -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("jsonschema is required to validate EditingTemplate") from exc
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    jsonschema.validate(instance=dict(template), schema=schema)
    expected = sha256(_canonical_json({**dict(template), "content_hash": ""}).encode("utf-8")).hexdigest()
    if template.get("content_hash") != expected:
        raise EditingTemplateError("editing template content_hash mismatch")


def write_reverse_engineering_bundle(
    output_dir: str | Path,
    template: Mapping[str, Any],
    frame_timeline: list[Mapping[str, Any]],
) -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    template_path = out / "editing_template.json"
    timeline_path = out / "frame_timeline.json"
    template_path.write_text(json.dumps(template, indent=2, ensure_ascii=False), encoding="utf-8")
    timeline_path.write_text(json.dumps(frame_timeline, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"editing_template": str(template_path), "frame_timeline": str(timeline_path)}
