from pathlib import Path
import json
import shutil
import subprocess

import pytest
from PIL import Image, ImageDraw

from src.extraction.pipeline import AnalysisConfig, analyze_video
from src.extraction.benchmark import GroundTruth, benchmark_feature_pack


def _make_fixture(tmp_path: Path, fps: int = 30) -> tuple[Path, GroundTruth]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("FFmpeg capability unavailable on this runner")
    frames = tmp_path / "source_frames"
    frames.mkdir()
    colors = [(8,8,8), (242,242,238), (70,10,10)]
    for i in range(90):
        scene = min(2, i // 30)
        im = Image.new("RGB", (320, 180), colors[scene])
        d = ImageDraw.Draw(im)
        # deterministic moving geometry inside each shot ensures normal motion is separated from hard cuts
        x = 25 + (i % 30) * 3
        d.rectangle((x, 70, x + 34, 104), fill=(220,220,220) if scene != 1 else (25,25,25))
        im.save(frames / f"{i:05d}.png")
    video = tmp_path / "fixture.mp4"
    subprocess.run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-framerate", str(fps), "-i", str(frames / "%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "12", str(video)
    ], check=True)
    return video, GroundTruth(
        fps=float(fps), total_frames=90, shot_boundaries=(30,60),
        dominant_colors=("#080808", "#F2F2EE", "#460A0A"), text_strings=(), motion_direction="right"
    )


def test_real_mp4_to_remotion_pipeline(tmp_path: Path):
    video, truth = _make_fixture(tmp_path)
    out = tmp_path / "analysis"
    result = analyze_video(video, out, config=AnalysisConfig(analysis_width=320, ocr_every_n=30, optical_flow_stride=4, keep_frames=False))
    pack = result["feature_pack"]
    report = benchmark_feature_pack(pack, truth, tolerance_frames=2)
    assert report["shot_detection"]["recall"] == 1.0
    assert report["shot_detection"]["precision"] == 1.0
    assert report["shot_detection"]["max_boundary_error_frames"] <= 1
    assert len(pack["keyframes"]) >= 9
    assert (out / "feature_pack.json").exists()
    assert (out / "motionstyle2json.json").exists()
    assert (out / "remotion_scene_spec.json").exists()
    assert (out / "motionSpec.ts").exists()
    assert result["remotion"]["project"]["duration_frames"] == 90
    assert sum(s["durationInFrames"] for s in result["remotion"]["scenes"]) == 90
    manifest = json.loads((out / "analysis_manifest.json").read_text())
    assert manifest["authority"]["pixels"] == "measured"
    assert manifest["authority"]["style"] == "inferred_evidence_bound"
    assert manifest["counts"]["decoded_frames"] == 90
