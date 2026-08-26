from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path


def ffprobe(path: Path) -> dict:
    exe = shutil.which("ffprobe")
    if not exe:
        raise RuntimeError("ffprobe unavailable")
    cp = subprocess.run([
        exe, "-v", "error", "-count_frames",
        "-show_entries", "stream=codec_type,width,height,r_frame_rate,avg_frame_rate,nb_frames,nb_read_frames:format=duration,size",
        "-of", "json", str(path)
    ], capture_output=True, text=True, check=True)
    return json.loads(cp.stdout)


def _fps(value: str) -> float:
    return float(Fraction(value)) if value and value != "0/0" else 0.0


def verify(spec_path: Path, video_path: Path) -> dict:
    if not video_path.exists() or video_path.stat().st_size <= 0:
        raise AssertionError("rendered MP4 missing or empty")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    probe = ffprobe(video_path)
    streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
    if len(streams) != 1:
        raise AssertionError(f"expected exactly one video stream, got {len(streams)}")
    stream = streams[0]
    project = spec["project"]
    expected_fps = float(project["fps"])
    actual_fps = _fps(stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0/1")
    duration = float(probe["format"]["duration"])
    expected_duration = float(project["duration_frames"]) / expected_fps
    frame_count_raw = stream.get("nb_read_frames") or stream.get("nb_frames")
    frame_count = int(frame_count_raw) if frame_count_raw not in (None, "N/A") else None
    errors = []
    if int(stream.get("width", 0)) != int(project["width"]):
        errors.append(f"width:{stream.get('width')}!={project['width']}")
    if int(stream.get("height", 0)) != int(project["height"]):
        errors.append(f"height:{stream.get('height')}!={project['height']}")
    if abs(actual_fps - expected_fps) > 1e-6:
        errors.append(f"fps:{actual_fps}!={expected_fps}")
    if frame_count is not None and frame_count != int(project["duration_frames"]):
        errors.append(f"frames:{frame_count}!={project['duration_frames']}")
    tolerance = max(0.002, 0.5 / expected_fps)
    if abs(duration - expected_duration) > tolerance:
        errors.append(f"duration:{duration}!={expected_duration}:tol={tolerance}")
    digest = hashlib.sha256(video_path.read_bytes()).hexdigest()
    report = {
        "schema": "motion-os.remotion-runtime-evidence/v1",
        "runtime": "Remotion/Chromium",
        "spec_path": str(spec_path),
        "video_path": str(video_path),
        "video_sha256": digest,
        "video_bytes": video_path.stat().st_size,
        "expected": {
            "width": project["width"],
            "height": project["height"],
            "fps": expected_fps,
            "duration_frames": project["duration_frames"],
            "duration_s": expected_duration,
        },
        "observed": {
            "width": int(stream["width"]),
            "height": int(stream["height"]),
            "fps": actual_fps,
            "duration_frames": frame_count,
            "duration_s": duration,
        },
        "errors": errors,
        "technical_runtime_gate": "PASS" if not errors else "FAIL",
        "creative_authority": "none",
        "temporal_critic_authority": "none",
    }
    if errors:
        raise AssertionError(json.dumps(report, indent=2))
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--spec", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    report = verify(Path(args.spec), Path(args.video))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
