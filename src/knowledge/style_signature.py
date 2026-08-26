from __future__ import annotations

from typing import Any, Mapping, Sequence
import math


def _hex_rgb(value: str) -> tuple[float, float, float]:
    h = value.lstrip("#")
    if len(h) != 6:
        return (0.0, 0.0, 0.0)
    try:
        return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return (0.0, 0.0, 0.0)


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def feature_pack_style_vector(pack: Mapping[str, Any]) -> list[float]:
    """Stable low-dimensional vector derived from measured evidence only.

    It is intentionally not a CLIP replacement. Its job is to make v1 retrieval inspectable and to
    avoid hiding a semantic embedding behind an opaque score before the corpus benchmark exists.
    """
    palette = list(pack.get("color_stats", {}).get("palette", []))
    top = palette[:3]
    rgbs = [_hex_rgb(str(x.get("hex", "#000000"))) for x in top]
    while len(rgbs) < 3:
        rgbs.append((0.0, 0.0, 0.0))
    palette_ratios = [float(x.get("ratio", 0.0)) for x in top]
    while len(palette_ratios) < 3:
        palette_ratios.append(0.0)

    motion = pack.get("motion_stats", {})
    tracks = list(motion.get("tracks", [])) if isinstance(motion, Mapping) else []
    motion_medians = [float(x.get("motion_median", 0.0)) for x in tracks]
    camera = [float(x.get("camera_likelihood", 0.0)) for x in tracks]
    global_mag = [float(x.get("global_magnitude", 0.0)) for x in tracks]
    local_mag = [float(x.get("local_residual_median", 0.0)) for x in tracks]

    fx = pack.get("fx_stats", {})
    measurements = list(fx.get("measurements", [])) if isinstance(fx, Mapping) else []
    contrast = [float(x.get("contrast", 0.0)) / 128.0 for x in measurements]
    blur = [float(x.get("blur_proxy", 0.0)) for x in measurements]
    highlight = [float(x.get("highlight_ratio", 0.0)) for x in measurements]

    shots = list(pack.get("shots", []))
    video = pack.get("video_meta", {})
    duration_ms = max(1.0, float(video.get("duration_ms", 1.0)))
    shot_rate = len(shots) / max(0.001, duration_ms / 1000.0)

    layout = pack.get("layout_stats", {})
    safe_margin = float(layout.get("safe_margin_pct") or 0.0) / 100.0 if isinstance(layout, Mapping) else 0.0
    anchor_x_count = min(12.0, float(len(layout.get("anchors_x", [])))) / 12.0 if isinstance(layout, Mapping) else 0.0
    anchor_y_count = min(12.0, float(len(layout.get("anchors_y", [])))) / 12.0 if isinstance(layout, Mapping) else 0.0

    audio = pack.get("audio_stats", {})
    onset_count = len(audio.get("onsets_ms", [])) if isinstance(audio, Mapping) else 0
    onset_rate = onset_count / max(0.001, duration_ms / 1000.0)

    vec: list[float] = []
    for rgb in rgbs:
        vec.extend(rgb)
    vec.extend(palette_ratios)
    vec.extend([
        min(1.0, _mean(motion_medians) / 8.0),
        _mean(camera),
        min(1.0, _mean(global_mag) / 8.0),
        min(1.0, _mean(local_mag) / 8.0),
        min(1.0, _mean(contrast)),
        _mean(blur),
        min(1.0, _mean(highlight) * 5.0),
        min(1.0, shot_rate / 4.0),
        safe_margin,
        anchor_x_count,
        anchor_y_count,
        min(1.0, onset_rate / 8.0),
    ])
    return [round(float(x), 6) for x in vec]


def evidence_coverage(pack: Mapping[str, Any]) -> float:
    domains = [
        bool(pack.get("shots")),
        bool(pack.get("keyframes")),
        bool(pack.get("color_stats", {}).get("palette", [])),
        bool(pack.get("layout_stats")),
        bool(pack.get("motion_stats", {}).get("tracks", [])),
        bool(pack.get("fx_stats", {}).get("measurements", [])),
        pack.get("audio_stats", {}).get("authority") in {"measured", "measured_model", "not_present"},
    ]
    # OCR is a valid unavailable domain and should not make a no-text/no-provider corpus appear fabricated.
    ocr_valid = bool(pack.get("ocr")) or any(str(w).startswith("provider_unavailable:ocr") for w in pack.get("warnings", []))
    domains.append(ocr_valid)
    return round(sum(bool(x) for x in domains) / len(domains), 6)


def canonical_style_family(motionstyle: Mapping[str, Any]) -> str:
    labels = list(motionstyle.get("style_system", {}).get("style_family", []))
    if not labels:
        return "other"
    labels.sort(key=lambda x: float(x.get("confidence", 0.0)), reverse=True)
    return str(labels[0].get("id", "other"))
