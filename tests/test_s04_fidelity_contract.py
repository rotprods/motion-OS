from __future__ import annotations

from argparse import Namespace
from importlib import util
import json
from pathlib import Path
import sys
import wave

from PIL import Image, ImageDraw


def _module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "qualify_s04_fidelity.py"
    spec = util.spec_from_file_location("qualify_s04_fidelity", path)
    assert spec and spec.loader
    mod = util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _baseline(path: Path) -> None:
    def kfs(start: int, end: int, x: int, y: int, w: int, h: int):
        return [
            {"frame": start, "x": x, "y": y, "width": w, "height": h, "opacity": 1.0},
            {"frame": end, "x": x, "y": y, "width": w, "height": h, "opacity": 1.0},
        ]
    data = {
        "schema_version": "motion-os.s04-fidelity-baseline/v1",
        "scene_id": "S04_CIENTIFICAMENTE",
        "source": {
            "video_id": "fixture",
            "sha256": "a" * 64,
            "fps": 30,
            "width": 64,
            "height": 64,
            "start_frame": 145,
            "frame_count": 71,
        },
        "tracks": {
            "setup": {"kind": "white", "keyframes": kfs(0, 68, 5, 5, 12, 5)},
            "hero": {"kind": "red", "keyframes": kfs(10, 68, 8, 25, 30, 8)},
            "tail": {"kind": "white", "keyframes": kfs(38, 68, 40, 48, 14, 5)},
        },
        "audio": {
            "source_primary_emphasis_onset_local_frame": 9,
            "source_primary_emphasis_onset_authority": "MEASURED",
            "sfx_class_authority": "INFERRED",
        },
        "thresholds": {
            "temporal_visibility_exact": True,
            "mean_bbox_iou_min": 0.90,
            "mean_centroid_error_px_max": 3.0,
            "mean_area_error_pct_max": 8.0,
            "visible_color_deltaE76_warn": 8.0,
            "primary_audio_onset_error_frames_max": 1.5,
        },
        "authority_notes": [],
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def _frames(root: Path, *, shift_hero_x: int = 0) -> tuple[Path, Path]:
    source = root / "source"
    overlay = root / "overlay"
    source.mkdir()
    overlay.mkdir()
    for frame in range(71):
        src = Image.new("RGB", (64, 64), (0, 0, 0))
        ov = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        ds = ImageDraw.Draw(src)
        do = ImageDraw.Draw(ov)
        if frame <= 68:
            ds.rectangle((5, 5, 16, 9), fill=(230, 230, 230))
            do.rectangle((5, 5, 16, 9), fill=(230, 230, 230, 255))
        if 10 <= frame <= 68:
            ds.rectangle((8, 25, 37, 32), fill=(160, 0, 0))
            do.rectangle((8 + shift_hero_x, 25, 37 + shift_hero_x, 32), fill=(160, 0, 0, 255))
        if 38 <= frame <= 68:
            ds.rectangle((40, 48, 53, 52), fill=(220, 220, 220))
            do.rectangle((40, 48, 53, 52), fill=(220, 220, 220, 255))
        src.save(source / f"frame_{frame:03d}.png")
        ov.save(overlay / f"element-{frame:02d}.png")
    return source, overlay


def test_exact_synthetic_geometry_passes(tmp_path: Path) -> None:
    mod = _module()
    baseline = tmp_path / "baseline.json"
    _baseline(baseline)
    source, overlay = _frames(tmp_path)
    result = mod.qualify(
        Namespace(
            baseline=baseline,
            source_dir=source,
            overlay_dir=overlay,
            source_audio=None,
            render_audio=None,
            include_per_frame=False,
        )
    )
    assert result["qualification"]["unresolved_p0_p1_count"] == 0
    assert result["component_metrics"]["hero"]["mean_bbox_iou"] == 1.0
    assert result["component_metrics"]["setup"]["temporal_visibility_exact"] is True


def test_shifted_hero_becomes_p1_geometry_defect(tmp_path: Path) -> None:
    mod = _module()
    baseline = tmp_path / "baseline.json"
    _baseline(baseline)
    source, overlay = _frames(tmp_path, shift_hero_x=7)
    result = mod.qualify(
        Namespace(
            baseline=baseline,
            source_dir=source,
            overlay_dir=overlay,
            source_audio=None,
            render_audio=None,
            include_per_frame=False,
        )
    )
    ids = {item["id"] for item in result["defects"]}
    assert "S04-DEF-GEOMETRY-HERO" in ids
    assert result["qualification"]["state"] == "DEFECTS_FOUND_REPAIR_REQUIRED"


def test_transient_proxy_detects_impulse_location(tmp_path: Path) -> None:
    mod = _module()
    path = tmp_path / "impulse.wav"
    sr = 48000
    duration = 1.0
    samples = [0] * int(sr * duration)
    center = int(sr * 0.300)
    for i in range(center, center + 100):
        samples[i] = 28000 if i % 2 == 0 else -28000
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        import struct
        w.writeframes(b"".join(struct.pack("<h", x) for x in samples))
    peak = mod._transient_peak_wav(path)
    assert abs(peak["peak_seconds"] - 0.300) <= 0.010
