#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image

EXPECTED = {
    "scene_id": "S04_CIENTIFICAMENTE",
    "composition_id": "GoldenS04Cientificamente",
    "frame_count": 71,
    "fps": 30.0,
    "width": 512,
    "height": 1108,
}
SAMPLE_FRAMES = (0, 5, 10, 11, 15, 20, 38, 43, 50, 60, 65, 70)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def parse_rate(value: str) -> float:
    numerator, denominator = value.split("/", 1)
    den = float(denominator)
    if den == 0:
        raise ValueError(f"invalid rate: {value}")
    return float(numerator) / den


def extract_samples(video: Path, output: Path) -> list[dict[str, Any]]:
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for frame in SAMPLE_FRAMES:
        target = output / f"frame_{frame:03d}.png"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(video), "-vf", f"select=eq(n\\,{frame})", "-vsync", "0", str(target),
            ],
            check=True,
        )
        with Image.open(target) as image:
            results.append({
                "frame": frame,
                "sha256": sha256(target),
                "width": image.width,
                "height": image.height,
            })
    return results


def region_ratios(path: Path) -> dict[str, float]:
    with Image.open(path).convert("RGB") as image:
        pixels = image.load()
        red_count = white_count = tail_white = 0
        hero_total = (496 - 42) * (735 - 555)
        tail_total = (505 - 270) * (752 - 650)
        for y in range(555, 735):
            for x in range(42, 496):
                r, g, b = pixels[x, y]
                if r > 105 and r - g > 45 and r - b > 35:
                    red_count += 1
                if r > 185 and g > 185 and b > 185 and max(r, g, b) - min(r, g, b) < 42:
                    white_count += 1
        for y in range(650, 752):
            for x in range(270, 505):
                r, g, b = pixels[x, y]
                if r > 185 and g > 185 and b > 185 and max(r, g, b) - min(r, g, b) < 42:
                    tail_white += 1
        return {
            "hero_red_ratio": red_count / hero_total,
            "caption_white_ratio": white_count / hero_total,
            "tail_white_ratio": tail_white / tail_total,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify physical S04 Remotion golden-scene render")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--samples-dir", type=Path)
    parser.add_argument("--plate-mode", choices=["procedural", "image-sequence"], default="procedural")
    args = parser.parse_args()

    video = args.video.resolve()
    samples_dir = (args.samples_dir or args.out.with_suffix("").with_name(args.out.stem + "_frames")).resolve()
    probe = run_json([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)
    ])
    video_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
    audio_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]
    if len(video_streams) != 1:
        raise SystemExit(f"expected one video stream, got {len(video_streams)}")
    stream = video_streams[0]
    fps = parse_rate(str(stream.get("avg_frame_rate", "0/0")))
    frame_count = int(stream.get("nb_frames") or 0)
    width, height = int(stream.get("width", 0)), int(stream.get("height", 0))

    failures: list[str] = []
    if frame_count != EXPECTED["frame_count"]:
        failures.append(f"frame_count:{frame_count}!={EXPECTED['frame_count']}")
    if not math.isclose(fps, EXPECTED["fps"], rel_tol=0, abs_tol=1e-6):
        failures.append(f"fps:{fps}!={EXPECTED['fps']}")
    if (width, height) != (EXPECTED["width"], EXPECTED["height"]):
        failures.append(f"dimensions:{width}x{height}!={EXPECTED['width']}x{EXPECTED['height']}")
    if not audio_streams:
        failures.append("audio_stream:missing")

    samples = extract_samples(video, samples_dir)
    ratios = {sample["frame"]: region_ratios(samples_dir / f"frame_{sample['frame']:03d}.png") for sample in samples}

    if ratios[10]["hero_red_ratio"] > 0.018:
        failures.append("hero_visible_before_contract_start")
    if ratios[15]["hero_red_ratio"] < 0.018:
        failures.append("hero_red_impact_missing_at_frame_15")
    if ratios[20]["hero_red_ratio"] < 0.018:
        failures.append("hero_red_settle_missing_at_frame_20")
    if ratios[43]["tail_white_ratio"] < 0.003:
        failures.append("tail_caption_missing_at_frame_43")

    evidence = {
        "schema": "motion-os.golden-s04-render-evidence/v1",
        "scene_id": EXPECTED["scene_id"],
        "composition_id": EXPECTED["composition_id"],
        "artifact": {
            "path": str(video),
            "sha256": sha256(video),
            "bytes": video.stat().st_size,
            "frame_count": frame_count,
            "fps": fps,
            "width": width,
            "height": height,
            "visual_duration_s": frame_count / fps if fps else None,
            "container_duration_s": float(probe.get("format", {}).get("duration", 0.0)),
            "audio_stream_count": len(audio_streams),
        },
        "plate_mode": args.plate_mode,
        "samples": [{**sample, "ratios": ratios[sample["frame"]]} for sample in samples],
        "checks": {
            "mechanical": "PASS" if not [x for x in failures if x.startswith(("frame_count", "fps", "dimensions", "audio_stream"))] else "FAIL",
            "structural": "PASS" if not [x for x in failures if not x.startswith(("frame_count", "fps", "dimensions", "audio_stream"))] else "FAIL",
            "failures": failures,
        },
        "authority": {
            "render_execution": "STRUCTURAL_RENDER_EXECUTED" if not failures else "FAILED",
            "source_fidelity": "BLOCKED_NOT_MEASURED",
            "creative_quality": "NOT_CLAIMED",
            "audio_fidelity": "BLOCKED_SYNTHETIC_SFX_OR_EXTERNAL_MIX_REQUIRED",
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
