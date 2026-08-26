from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Sequence
import hashlib
import json
import math
import shutil
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageFilter, ImageStat


@dataclass(frozen=True)
class ProviderStatus:
    name: str
    available: bool
    authority: str
    version: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _binary_version(binary: str) -> str | None:
    path = shutil.which(binary)
    if not path:
        return None
    try:
        cp = subprocess.run([path, "-version"], capture_output=True, text=True, timeout=5, check=False)
        line = (cp.stdout or cp.stderr).splitlines()[0] if (cp.stdout or cp.stderr) else ""
        return line.strip() or None
    except Exception:
        return None


def capability_registry() -> dict[str, dict[str, Any]]:
    ffmpeg = _binary_version("ffmpeg")
    ffprobe = _binary_version("ffprobe")
    try:
        import cv2  # type: ignore
        cv = ProviderStatus("opencv_optical_flow", True, "measured", getattr(cv2, "__version__", None))
    except Exception as exc:
        cv = ProviderStatus("opencv_optical_flow", False, "unavailable", reason=type(exc).__name__)
    try:
        import pytesseract  # type: ignore
        tess_bin = shutil.which("tesseract")
        ocr = ProviderStatus("tesseract_ocr", bool(tess_bin), "measured" if tess_bin else "unavailable", getattr(pytesseract, "__version__", None), None if tess_bin else "tesseract binary missing")
    except Exception as exc:
        ocr = ProviderStatus("tesseract_ocr", False, "unavailable", reason=type(exc).__name__)
    return {
        "ffmpeg": ProviderStatus("ffmpeg", bool(ffmpeg), "measured" if ffmpeg else "unavailable", ffmpeg).to_dict(),
        "ffprobe": ProviderStatus("ffprobe", bool(ffprobe), "measured" if ffprobe else "unavailable", ffprobe).to_dict(),
        "opencv": cv.to_dict(),
        "ocr": ocr.to_dict(),
    }


def require_binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"required binary unavailable: {name}")
    return path


def extract_frames_ffmpeg(video_path: str | Path, output_dir: str | Path, *, fps: float | None = None, scale_width: int | None = None) -> list[dict[str, Any]]:
    """Decode physical frames with FFmpeg. Output refs are content-addressed by SHA256."""
    ffmpeg = require_binary("ffmpeg")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    pattern = out / "%08d.png"
    filters: list[str] = []
    if fps:
        filters.append(f"fps={fps:.8f}")
    if scale_width:
        filters.append(f"scale={scale_width}:-2:flags=lanczos")
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(video_path)]
    if filters:
        cmd += ["-vf", ",".join(filters)]
    cmd += [str(pattern)]
    subprocess.run(cmd, check=True)
    records: list[dict[str, Any]] = []
    for idx, path in enumerate(sorted(out.glob("*.png"))):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append({"frame": idx, "path": str(path), "sha256": digest})
    if not records:
        raise RuntimeError("ffmpeg decoded zero frames")
    return records


def frame_change_score(a: Image.Image, b: Image.Image) -> float:
    """Deterministic perceptual cut score in [0,1] using small grayscale frame differences."""
    aa = a.convert("L").resize((160, 90), Image.Resampling.BILINEAR)
    bb = b.convert("L").resize((160, 90), Image.Resampling.BILINEAR)
    diff = ImageChops.difference(aa, bb)
    mean = ImageStat.Stat(diff).mean[0] / 255.0
    # add edge-structure change so typography/layout cuts are not missed
    ea = aa.filter(ImageFilter.FIND_EDGES)
    eb = bb.filter(ImageFilter.FIND_EDGES)
    edge = ImageStat.Stat(ImageChops.difference(ea, eb)).mean[0] / 255.0
    return max(0.0, min(1.0, 0.72 * mean + 0.28 * edge))


def change_scores_from_records(records: Sequence[dict[str, Any]]) -> list[float]:
    scores: list[float] = []
    prev: Image.Image | None = None
    for rec in records:
        with Image.open(rec["path"]) as src:
            current = src.convert("RGB")
        if prev is not None:
            scores.append(frame_change_score(prev, current))
        prev = current
    return scores


def optical_flow_opencv(records: Sequence[dict[str, Any]], *, sample_stride: int = 1) -> dict[str, Any]:
    """Measured dense Farneback flow. Returns robust global/local statistics, never fabricated fallback values."""
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception as exc:
        return {"available": False, "authority": "unavailable", "reason": f"opencv:{type(exc).__name__}", "tracks": []}
    tracks: list[dict[str, Any]] = []
    for i in range(0, max(0, len(records) - sample_stride), sample_stride):
        p0, p1 = records[i]["path"], records[i + sample_stride]["path"]
        a = cv2.imread(str(p0), cv2.IMREAD_GRAYSCALE)
        b = cv2.imread(str(p1), cv2.IMREAD_GRAYSCALE)
        if a is None or b is None:
            continue
        if a.shape != b.shape:
            b = cv2.resize(b, (a.shape[1], a.shape[0]))
        # downscale for predictable cost while preserving global motion
        max_w = 640
        if a.shape[1] > max_w:
            s = max_w / a.shape[1]
            size = (max_w, max(2, int(a.shape[0] * s)))
            a, b = cv2.resize(a, size), cv2.resize(b, size)
        flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        fx, fy = flow[..., 0], flow[..., 1]
        mag = np.sqrt(fx * fx + fy * fy)
        med_x, med_y = float(np.median(fx)), float(np.median(fy))
        residual = np.sqrt((fx - med_x) ** 2 + (fy - med_y) ** 2)
        global_mag = math.hypot(med_x, med_y)
        local_mag = float(np.median(residual))
        tracks.append({
            "from_frame": int(records[i]["frame"]),
            "to_frame": int(records[i + sample_stride]["frame"]),
            "global_dx": med_x,
            "global_dy": med_y,
            "global_magnitude": global_mag,
            "local_residual_median": local_mag,
            "motion_median": float(np.median(mag)),
            "camera_likelihood": round(global_mag / max(global_mag + local_mag, 1e-9), 6),
        })
    if not tracks:
        return {"available": True, "authority": "measured", "tracks": [], "warning": "no usable frame pairs"}
    mean_cam = sum(t["camera_likelihood"] for t in tracks) / len(tracks)
    return {
        "available": True,
        "authority": "measured",
        "method": "opencv_farneback_dense_v1",
        "tracks": tracks,
        "camera_motion": {"classification": "camera_dominant" if mean_cam >= 0.62 else "local_or_mixed", "mean_likelihood": round(mean_cam, 6)},
    }


def ocr_tesseract(records: Sequence[dict[str, Any]], *, every_n: int = 15) -> dict[str, Any]:
    try:
        import pytesseract  # type: ignore
        from pytesseract import Output  # type: ignore
    except Exception as exc:
        return {"available": False, "authority": "unavailable", "reason": f"pytesseract:{type(exc).__name__}", "blocks": []}
    if not shutil.which("tesseract"):
        return {"available": False, "authority": "unavailable", "reason": "tesseract binary missing", "blocks": []}
    blocks: list[dict[str, Any]] = []
    for rec in records[::max(1, every_n)]:
        with Image.open(rec["path"]) as im:
            data = pytesseract.image_to_data(im, output_type=Output.DICT)
            w, h = im.size
        for i, raw in enumerate(data.get("text", [])):
            text = str(raw).strip()
            try:
                conf = float(data["conf"][i]) / 100.0
            except Exception:
                conf = 0.0
            if not text or conf < 0.35:
                continue
            x, y, bw, bh = (int(data[k][i]) for k in ("left", "top", "width", "height"))
            ident = f"ocr_f{rec['frame']}_{i}"
            blocks.append({"id": ident, "frame": rec["frame"], "text": text, "bbox": [x / w, y / h, bw / w, bh / h], "confidence": round(conf, 4), "method": "tesseract", "evidence_refs": [f"frame:{rec['frame']}"]})
    return {"available": True, "authority": "measured", "method": "tesseract", "blocks": blocks}


def track_ocr_blocks(blocks: Sequence[dict[str, Any]], *, max_frame_gap: int = 45) -> list[dict[str, Any]]:
    """Simple deterministic continuity tracker: exact normalized text + nearest bbox center."""
    active: dict[str, list[dict[str, Any]]] = {}
    for item in sorted(blocks, key=lambda x: (int(x.get("frame", 0)), str(x.get("text", "")))):
        key = str(item.get("text", "")).casefold()
        candidates = active.setdefault(key, [])
        best: dict[str, Any] | None = None
        best_d = 9e9
        x, y, w, h = item.get("bbox", [0, 0, 0, 0])
        cx, cy = x + w / 2, y + h / 2
        for cand in candidates:
            if int(item["frame"]) - int(cand["last_frame"]) > max_frame_gap:
                continue
            px, py = cand["center"]
            d = math.hypot(cx - px, cy - py)
            if d < best_d:
                best, best_d = cand, d
        if best is None or best_d > 0.12:
            cid = f"text_{len(candidates)+1}_{hashlib.sha1(key.encode()).hexdigest()[:8]}"
            best = {"continuity_id": cid, "last_frame": item["frame"], "center": (cx, cy)}
            candidates.append(best)
        else:
            best["last_frame"], best["center"] = item["frame"], (cx, cy)
        item["continuity_id"] = best["continuity_id"]
    return [dict(x) for x in blocks]


def fx_material_heuristics(records: Sequence[dict[str, Any]], *, sample_count: int = 12) -> tuple[dict[str, Any], dict[str, Any]]:
    if not records:
        return ({"labels": [], "measurements": []}, {"materials": []})
    step = max(1, len(records) // sample_count)
    measures = []
    for rec in records[::step][:sample_count]:
        with Image.open(rec["path"]) as im:
            rgb = im.convert("RGB").resize((240, 135), Image.Resampling.BILINEAR)
        gray = rgb.convert("L")
        contrast = ImageStat.Stat(gray).stddev[0]
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_mean = ImageStat.Stat(edges).mean[0]
        blur_proxy = max(0.0, min(1.0, 1.0 - edge_mean / 35.0))
        highlights = sum(1 for v in gray.getdata() if v >= 235) / (240 * 135)
        measures.append({"frame": rec["frame"], "contrast": round(contrast, 4), "blur_proxy": round(blur_proxy, 4), "highlight_ratio": round(highlights, 6)})
    mean_blur = sum(x["blur_proxy"] for x in measures) / len(measures)
    mean_hi = sum(x["highlight_ratio"] for x in measures) / len(measures)
    labels = []
    if mean_blur > 0.72:
        labels.append("blur")
    if mean_hi > 0.08:
        labels.append("bloom_candidate")
    materials = []
    if mean_hi > 0.06:
        materials.append({"label": "glass_or_polished_candidate", "confidence": round(min(0.72, 0.35 + mean_hi * 2.5), 4), "evidence_refs": [f"frame:{m['frame']}" for m in measures[:4]]})
    return ({"labels": labels, "measurements": measures, "authority": "measured_heuristic"}, {"materials": materials, "authority": "inferred_from_measured_pixels"})
