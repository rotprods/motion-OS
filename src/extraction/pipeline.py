from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable
import json
import math
import tempfile

from PIL import Image

from .audio_provider import analyze_audio_envelope, transcribe_whisper_optional
from .feature_pack import assemble_feature_pack, validate_feature_pack
from .ingest import probe_video
from .providers import (
    capability_registry,
    change_scores_from_records,
    extract_frames_ffmpeg,
    fx_material_heuristics,
    ocr_tesseract,
    optical_flow_opencv,
    track_ocr_blocks,
)
from .segmentation import detect_shots_from_change_scores, plan_keyframes
from .visual import dominant_palette, gradient_candidate, infer_layout
from src.normalization.motionstyle import normalize_feature_pack, validate_motionstyle
from src.compilers.remotion import compile_remotion_scene_spec, validate_scene_coverage, emit_remotion_typescript


@dataclass(frozen=True)
class AnalysisConfig:
    shot_threshold: float | None = None
    min_shot_frames: int = 4
    analysis_width: int = 640
    ocr_every_n: int = 15
    optical_flow_stride: int = 2
    transcript_provider: str = "none"  # none|whisper
    whisper_model: str = "tiny"
    keep_frames: bool = False


def _robust_threshold(scores: list[float]) -> float:
    if not scores:
        return 1.0
    ordered = sorted(scores)
    med = ordered[len(ordered) // 2]
    deviations = sorted(abs(x - med) for x in scores)
    mad = deviations[len(deviations) // 2]
    # Structural cuts need to be well above normal motion, but retain a floor for low-motion design pieces.
    return round(max(0.16, min(0.72, med + max(0.10, 6.0 * mad))), 6)


def _sample_pixels(paths: Iterable[str], *, per_frame: int = 900) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for path in paths:
        with Image.open(path) as im:
            rgb = im.convert("RGB")
            w, h = rgb.size
            total = w * h
            stride = max(1, int(math.sqrt(total / max(1, per_frame))))
            for y in range(stride // 2, h, stride):
                for x in range(stride // 2, w, stride):
                    out.append(rgb.getpixel((x, y)))
    return out


def _measure_color(keyframes: list[dict[str, Any]]) -> dict[str, Any]:
    paths = [str(k["artifact_ref"]) for k in keyframes if k.get("artifact_ref")]
    samples = _sample_pixels(paths)
    palette = dominant_palette(samples, max_colors=8, quant_step=24)
    gradient = {"detected": False, "stops": []}
    if paths:
        with Image.open(paths[0]) as im:
            rgb = im.convert("RGB").resize((32, 18), Image.Resampling.BILINEAR)
            left = tuple(sum(rgb.getpixel((1, y))[c] for y in range(18)) // 18 for c in range(3))
            right = tuple(sum(rgb.getpixel((30, y))[c] for y in range(18)) // 18 for c in range(3))
            gradient = gradient_candidate(left, right)
    return {"palette": palette, "gradients": [gradient] if gradient.get("detected") else [], "authority": "measured_pixels"}


def _assign_ocr_to_shots(ocr: list[dict[str, Any]], shots: list[Any]) -> list[dict[str, Any]]:
    for item in ocr:
        f = int(item.get("frame", -1))
        shot = next((s for s in shots if s.start_frame <= f < s.end_frame), None)
        if shot is not None:
            item["shot_id"] = shot.shot_id
    return ocr


def _layout_from_ocr(ocr: list[dict[str, Any]]) -> dict[str, Any]:
    boxes = []
    for x in ocr:
        b = x.get("bbox")
        if not b or len(b) != 4:
            continue
        bx, by, bw, bh = [float(v) for v in b]
        boxes.append((bx, by, bx + bw, by + bh))
    layout = infer_layout(boxes)
    layout["evidence_kind"] = "ocr_boxes" if boxes else "none"
    return layout


def _keyframe_records(records: list[dict[str, Any]], shots: list[Any], fps: float) -> list[dict[str, Any]]:
    by_frame = {int(r["frame"]): r for r in records}
    result: list[dict[str, Any]] = []
    for shot in shots:
        for frame in plan_keyframes(shot):
            rec = by_frame.get(frame)
            if rec is None:
                continue
            result.append({
                "id": f"KF_{shot.shot_id}_{frame:06d}",
                "shot_id": shot.shot_id,
                "frame": frame,
                "at_ms": round(frame * 1000 / fps),
                "sha256": rec["sha256"],
                "artifact_ref": rec["path"],
            })
    return result


def analyze_video(video_path: str | Path, output_dir: str | Path, *, config: AnalysisConfig | None = None) -> dict[str, Any]:
    """Execute the measurement → FeaturePack → MotionStyle2JSON → Remotion chain.

    The output manifest distinguishes measured, inferred and unavailable providers. Missing optional providers
    create warnings/capability states; they never emit fabricated observations.
    """
    cfg = config or AnalysisConfig()
    video_path = Path(video_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    frames_dir = out / "frames"
    meta = probe_video(video_path)
    records = extract_frames_ffmpeg(video_path, frames_dir, scale_width=cfg.analysis_width)
    # Decoded frame count is authoritative for the analysis copy. Source metadata is retained separately.
    scores = change_scores_from_records(records)
    threshold = cfg.shot_threshold if cfg.shot_threshold is not None else _robust_threshold(scores)
    shots = detect_shots_from_change_scores(scores, fps=meta.fps, threshold=threshold, min_shot_frames=cfg.min_shot_frames, method="decoded_frame_delta_v1")
    keyframes = _keyframe_records(records, shots, meta.fps)

    ocr_result = ocr_tesseract(records, every_n=cfg.ocr_every_n)
    ocr = track_ocr_blocks(list(ocr_result.get("blocks", []))) if ocr_result.get("available") else []
    ocr = _assign_ocr_to_shots(ocr, shots)
    color_stats = _measure_color(keyframes)
    layout_stats = _layout_from_ocr(ocr)
    motion_stats = optical_flow_opencv(records, sample_stride=cfg.optical_flow_stride)
    if motion_stats.get("available"):
        tracks = motion_stats.get("tracks", [])
        magnitudes = [float(t.get("motion_median", 0.0)) for t in tracks]
        mean_mag = sum(magnitudes) / len(magnitudes) if magnitudes else 0.0
        motion_stats["energy"] = "high" if mean_mag > 3.0 else "medium" if mean_mag > 0.8 else "low"
    fx_stats, asset_stats = fx_material_heuristics(records)
    audio_stats = analyze_audio_envelope(video_path) if meta.audio_tracks else {"available": False, "authority": "not_present", "onsets_ms": [], "transcript": []}
    if cfg.transcript_provider == "whisper" and meta.audio_tracks:
        transcript = transcribe_whisper_optional(video_path, model_name=cfg.whisper_model)
        audio_stats["transcript_provider"] = transcript
        if transcript.get("available"):
            audio_stats["transcript"] = transcript.get("segments", [])

    warnings: list[str] = []
    for name, result in (("ocr", ocr_result), ("optical_flow", motion_stats), ("audio", audio_stats)):
        if not result.get("available") and result.get("authority") != "not_present":
            warnings.append(f"provider_unavailable:{name}:{result.get('reason','unspecified')}")
    if meta.frame_count is not None and abs(meta.frame_count - len(records)) > 1:
        warnings.append(f"decoded_frame_count_differs:probe={meta.frame_count}:decoded={len(records)}")

    provenance = [
        {"module": "video_meta", "method": "ffprobe", "version": "v1", "parameters": {}},
        {"module": "frame_decode", "method": "ffmpeg_png", "version": "v1", "parameters": {"analysis_width": cfg.analysis_width}},
        {"module": "shot_detection", "method": "decoded_frame_delta_v1", "version": "v1", "parameters": {"threshold": threshold, "min_shot_frames": cfg.min_shot_frames}},
        {"module": "color", "method": "pixel_quantization", "version": "v1", "parameters": {}},
        {"module": "ocr", "method": str(ocr_result.get("method", "unavailable")), "version": "v1", "parameters": {"every_n": cfg.ocr_every_n}},
        {"module": "motion", "method": str(motion_stats.get("method", "unavailable")), "version": "v1", "parameters": {"stride": cfg.optical_flow_stride}},
        {"module": "audio", "method": str(audio_stats.get("method", "unavailable")), "version": "v1", "parameters": {}},
    ]
    pack = assemble_feature_pack(
        video_meta=meta, shots=shots, keyframes=keyframes, ocr=ocr,
        color_stats=color_stats, layout_stats=layout_stats, motion_stats=motion_stats,
        fx_stats=fx_stats, asset_stats=asset_stats, audio_stats=audio_stats,
        extraction_provenance=provenance, warnings=warnings,
    )
    # The source may expose a misleading nb_frames; coverage must represent the physical analysis decode.
    pack["video_meta"]["decoded_frame_count"] = len(records)
    validate_feature_pack(pack)
    motionstyle = normalize_feature_pack(pack)
    validate_motionstyle(motionstyle)
    remotion = compile_remotion_scene_spec(motionstyle)
    coverage_errors = validate_scene_coverage(remotion)
    if coverage_errors:
        raise RuntimeError(f"compiler scene coverage failed: {coverage_errors}")

    (out / "feature_pack.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "motionstyle2json.json").write_text(json.dumps(motionstyle, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "remotion_scene_spec.json").write_text(json.dumps(remotion, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "motionSpec.ts").write_text(emit_remotion_typescript(motionstyle), encoding="utf-8")
    manifest = {
        "source": str(video_path),
        "config": asdict(cfg),
        "capabilities": capability_registry(),
        "thresholds": {"shot_change": threshold},
        "counts": {"decoded_frames": len(records), "shots": len(shots), "keyframes": len(keyframes), "ocr_blocks": len(ocr)},
        "artifacts": {"feature_pack": "feature_pack.json", "motionstyle": "motionstyle2json.json", "remotion": "remotion_scene_spec.json", "typescript": "motionSpec.ts"},
        "warnings": warnings,
        "authority": {"pixels": "measured", "shots": "measured_heuristic", "style": "inferred_evidence_bound", "compiler": "deterministic"},
    }
    (out / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if not cfg.keep_frames:
        # Keep keyframes as evidence; delete non-keyframes to control artifact growth.
        keep = {str(Path(k["artifact_ref"]).resolve()) for k in keyframes if k.get("artifact_ref")}
        for rec in records:
            p = Path(rec["path"])
            if str(p.resolve()) not in keep:
                p.unlink(missing_ok=True)
    return {"manifest": manifest, "feature_pack": pack, "motionstyle": motionstyle, "remotion": remotion}
