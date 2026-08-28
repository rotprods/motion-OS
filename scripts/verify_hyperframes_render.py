from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VIDEO = ROOT / "runtime" / "hyperframes" / "out" / "runtime-local.mp4"
DEFAULT_EVIDENCE = ROOT / "runtime" / "hyperframes" / "render_evidence.local.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,r_frame_rate,nb_frames,nb_read_frames:format=duration",
            "-of", "json", str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    payload = json.loads(result.stdout)
    if not payload.get("streams"):
        raise ValueError("render has no video stream")
    stream = payload["streams"][0]
    frame_raw = stream.get("nb_read_frames") or stream.get("nb_frames")
    if frame_raw in (None, "N/A", "0", 0):
        raise ValueError("frame count unavailable; visual duration authority cannot be established")
    fps = Fraction(stream["r_frame_rate"])
    frames = int(frame_raw)
    return {
        "codec": stream.get("codec_name"),
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "fps_fraction": stream["r_frame_rate"],
        "fps": float(fps),
        "frames": frames,
        "visual_duration_s": frames / float(fps),
        "container_duration_s": float(payload.get("format", {}).get("duration") or 0.0),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def evaluate_probe(
    media: dict,
    *,
    expected_width: int,
    expected_height: int,
    expected_fps: int,
    expected_frames: int,
    mux_tail_tolerance_s: float = 0.10,
) -> dict:
    errors: list[str] = []
    if media["width"] != expected_width or media["height"] != expected_height:
        errors.append("resolution_mismatch")
    if abs(float(media["fps"]) - expected_fps) > 1e-9:
        errors.append("fps_mismatch")
    if int(media["frames"]) != expected_frames:
        errors.append("frame_count_mismatch")

    expected_visual = expected_frames / expected_fps
    if abs(float(media["visual_duration_s"]) - expected_visual) > 1e-9:
        errors.append("visual_duration_mismatch")

    mux_tail = float(media["container_duration_s"]) - float(media["visual_duration_s"])
    if abs(mux_tail) > mux_tail_tolerance_s:
        errors.append("mux_tail_out_of_bounds")

    return {
        "ok": not errors,
        "errors": errors,
        "visual_duration_authority": "frame_count/fps",
        "expected_frames": expected_frames,
        "expected_visual_duration_s": expected_visual,
        "mux_tail_seconds": mux_tail,
        "mux_tail_tolerance_s": mux_tail_tolerance_s,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", nargs="?", type=Path, default=DEFAULT_VIDEO)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--frames", type=int, default=90)
    args = parser.parse_args()

    media = probe(args.video)
    verdict = evaluate_probe(
        media,
        expected_width=args.width,
        expected_height=args.height,
        expected_fps=args.fps,
        expected_frames=args.frames,
    )
    evidence = {
        "schema": "motion-os.hyperframes-physical-runtime/v1",
        "renderer": "hyperframes",
        "artifact": media,
        "verification": verdict,
        "authority": "VERIFIED" if verdict["ok"] else "EXECUTED",
        "creative_authority": "none",
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if verdict["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
