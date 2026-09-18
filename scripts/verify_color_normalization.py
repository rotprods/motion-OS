from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageStat

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.renderers.color_policy import (
    ArtifactColorBinding,
    BT709_SDR_LIMITED,
    SRGB_FULL,
    ffmpeg_color_filter,
    ffmpeg_output_color_args,
)


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_reference(path: Path) -> None:
    image = Image.new("RGB", (256, 256), (18, 18, 18))
    draw = ImageDraw.Draw(image)
    patches = [
        ((0, 0, 128, 128), (235, 32, 48)),
        ((128, 0, 256, 128), (28, 210, 96)),
        ((0, 128, 128, 256), (35, 92, 235)),
        ((128, 128, 256, 256), (210, 180, 42)),
    ]
    for box, color in patches:
        draw.rectangle(box, fill=color)
    image.save(path)


def probe(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=pix_fmt,color_space,color_transfer,color_primaries,color_range,width,height",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    streams = json.loads(completed.stdout).get("streams", [])
    if len(streams) != 1:
        raise RuntimeError("expected exactly one video stream")
    return streams[0]


def image_error(a: Path, b: Path) -> dict:
    left = Image.open(a).convert("RGB")
    right = Image.open(b).convert("RGB")
    if left.size != right.size:
        raise RuntimeError("comparison dimensions differ")
    diff = Image.new("RGB", left.size)
    lp = left.load(); rp = right.load(); dp = diff.load()
    max_error = 0
    total = 0
    count = left.size[0] * left.size[1] * 3
    for y in range(left.size[1]):
        for x in range(left.size[0]):
            channels = tuple(abs(lp[x, y][c] - rp[x, y][c]) for c in range(3))
            dp[x, y] = channels
            max_error = max(max_error, *channels)
            total += sum(channels)
    return {"mae_rgb_8bit": total / count, "max_channel_error": max_error}


def render_normalized(source: Path, output: Path, binding: ArtifactColorBinding) -> str:
    filter_graph = ffmpeg_color_filter(binding, BT709_SDR_LIMITED, input_label="0:v", output_label="norm")
    run([
        "ffmpeg", "-v", "error", "-y", "-i", str(source),
        "-filter_complex", filter_graph,
        "-map", "[norm]", "-frames:v", "1", "-c:v", "ffv1", "-level", "3",
        *ffmpeg_output_color_args(BT709_SDR_LIMITED), str(output),
    ])
    return filter_graph


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / ".artifacts" / "color-normalization")
    parser.add_argument("--mae-limit", type=float, default=2.0)
    parser.add_argument("--max-error-limit", type=int, default=10)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    reference = args.out / "reference_srgb.png"
    srgb_normalized = args.out / "srgb_to_bt709.mkv"
    bt709_source = args.out / "bt709_source.mkv"
    bt709_normalized = args.out / "bt709_to_bt709.mkv"
    srgb_png = args.out / "srgb_normalized.png"
    bt709_png = args.out / "bt709_normalized.png"
    evidence_path = args.out / "color_normalization_evidence.json"
    build_reference(reference)

    srgb_binding = ArtifactColorBinding("srgb", SRGB_FULL)
    srgb_filter = render_normalized(reference, srgb_normalized, srgb_binding)

    # The first normalized artifact is a physically generated BT.709 limited source.
    # Feed that independent media artifact through the same policy as a second renderer family.
    run(["ffmpeg", "-v", "error", "-y", "-i", str(srgb_normalized), "-c:v", "copy", str(bt709_source)])
    bt709_binding = ArtifactColorBinding("bt709", BT709_SDR_LIMITED)
    bt709_filter = render_normalized(bt709_source, bt709_normalized, bt709_binding)

    run(["ffmpeg", "-v", "error", "-y", "-i", str(srgb_normalized), "-frames:v", "1", str(srgb_png)])
    run(["ffmpeg", "-v", "error", "-y", "-i", str(bt709_normalized), "-frames:v", "1", str(bt709_png)])

    error = image_error(srgb_png, bt709_png)
    first_probe = probe(srgb_normalized)
    second_probe = probe(bt709_normalized)
    expected_metadata = {
        "color_primaries": "bt709",
        "color_transfer": "bt709",
        "color_space": "bt709",
        "color_range": "tv",
    }
    errors: list[str] = []
    for label, observed in (("srgb", first_probe), ("bt709", second_probe)):
        for key, expected in expected_metadata.items():
            if observed.get(key) != expected:
                errors.append(f"{label}_{key}_mismatch:{observed.get(key)}")
    if error["mae_rgb_8bit"] > args.mae_limit:
        errors.append("normalized_mae_exceeds_limit")
    if error["max_channel_error"] > args.max_error_limit:
        errors.append("normalized_max_channel_error_exceeds_limit")

    payload = {
        "schema": "motion-os.color-normalization-physical/v1",
        "working_space": "bt709_sdr_limited",
        "sources": ["srgb_full", "bt709_sdr_limited"],
        "filters": {"srgb": srgb_filter, "bt709": bt709_filter},
        "probes": {"srgb_normalized": first_probe, "bt709_normalized": second_probe},
        "perceptual_proxy": {
            **error,
            "mae_limit": args.mae_limit,
            "max_error_limit": args.max_error_limit,
            "method": "8-bit RGB pixel absolute error after lossless normalized outputs",
        },
        "artifacts": {
            p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size}
            for p in (reference, srgb_normalized, bt709_source, bt709_normalized, srgb_png, bt709_png)
        },
        "errors": errors,
        "ok": not errors,
        "authority": "PHYSICAL_COLOR_NORMALIZATION_VERIFIED" if not errors else "EXECUTED_FAILED",
        "creative_authority": "none",
    }
    evidence_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
