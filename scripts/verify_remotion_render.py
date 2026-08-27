from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path


_HASH_CHUNK_BYTES = 1024 * 1024


def ffprobe(path: Path) -> dict:
    exe = shutil.which("ffprobe")
    if not exe:
        raise RuntimeError("ffprobe unavailable")
    cp = subprocess.run(
        [
            exe,
            "-v",
            "error",
            "-count_frames",
            "-show_entries",
            "stream=codec_type,width,height,r_frame_rate,avg_frame_rate,nb_frames,nb_read_frames:format=duration,size",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return json.loads(cp.stdout)


def _fps(value: str) -> float:
    return float(Fraction(value)) if value and value != "0/0" else 0.0


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(_HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def verify_probe(spec: dict, probe: dict, *, video_bytes: int, video_sha256: str) -> dict:
    video_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
    audio_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]
    if len(video_streams) != 1:
        raise AssertionError(f"expected exactly one video stream, got {len(video_streams)}")

    stream = video_streams[0]
    project = spec["project"]
    expected_fps = float(project["fps"])
    if expected_fps <= 0:
        raise AssertionError("expected fps must be positive")

    actual_fps = _fps(stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0/1")
    expected_frames = int(project["duration_frames"])
    expected_visual_duration = expected_frames / expected_fps
    container_duration = float(probe["format"]["duration"])
    frame_count_raw = stream.get("nb_read_frames") or stream.get("nb_frames")
    frame_count = int(frame_count_raw) if frame_count_raw not in (None, "N/A") else None

    errors: list[str] = []
    if int(stream.get("width", 0)) != int(project["width"]):
        errors.append(f"width:{stream.get('width')}!={project['width']}")
    if int(stream.get("height", 0)) != int(project["height"]):
        errors.append(f"height:{stream.get('height')}!={project['height']}")
    if abs(actual_fps - expected_fps) > 1e-6:
        errors.append(f"fps:{actual_fps}!={expected_fps}")
    if frame_count is None:
        errors.append("frames:unavailable")
    elif frame_count != expected_frames:
        errors.append(f"frames:{frame_count}!={expected_frames}")

    observed_visual_duration = frame_count / actual_fps if frame_count is not None and actual_fps > 0 else None
    frame_tolerance = 0.5 / expected_fps
    if observed_visual_duration is not None and abs(observed_visual_duration - expected_visual_duration) > frame_tolerance:
        errors.append(
            f"visual_duration:{observed_visual_duration}!={expected_visual_duration}:tol={frame_tolerance}"
        )

    # MP4 container duration may be slightly longer than the visual timeline after
    # muxing an AAC track. Treat the frame-count/fps pair as visual authority and
    # bound the mux tail independently rather than weakening the visual contract.
    mux_tail_padding = container_duration - expected_visual_duration
    mux_tail_limit = max(0.100, 3.0 / expected_fps)
    if container_duration < expected_visual_duration - frame_tolerance:
        errors.append(
            f"container_truncation:{container_duration}<{expected_visual_duration}:tol={frame_tolerance}"
        )
    elif mux_tail_padding > mux_tail_limit:
        errors.append(f"mux_tail_padding:{mux_tail_padding}>limit={mux_tail_limit}")

    return {
        "schema": "motion-os.remotion-runtime-evidence/v2",
        "runtime": "Remotion/Chromium",
        "video_sha256": video_sha256,
        "video_bytes": video_bytes,
        "expected": {
            "width": project["width"],
            "height": project["height"],
            "fps": expected_fps,
            "duration_frames": expected_frames,
            "visual_duration_s": expected_visual_duration,
        },
        "observed": {
            "width": int(stream["width"]),
            "height": int(stream["height"]),
            "fps": actual_fps,
            "duration_frames": frame_count,
            "visual_duration_s": observed_visual_duration,
            "container_duration_s": container_duration,
            "mux_tail_padding_s": mux_tail_padding,
            "audio_stream_count": len(audio_streams),
        },
        "errors": errors,
        "technical_runtime_gate": "PASS" if not errors else "FAIL",
        "creative_authority": "none",
        "temporal_critic_authority": "none",
    }


def verify(spec_path: Path, video_path: Path) -> dict:
    if not video_path.exists() or video_path.stat().st_size <= 0:
        raise AssertionError("rendered MP4 missing or empty")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    probe = ffprobe(video_path)
    report = verify_probe(
        spec,
        probe,
        video_bytes=video_path.stat().st_size,
        video_sha256=_sha256_file(video_path),
    )
    report["spec_path"] = str(spec_path)
    report["video_path"] = str(video_path)
    if report["errors"]:
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
