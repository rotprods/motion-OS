from __future__ import annotations

from dataclasses import dataclass, asdict
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping
import hashlib
import json
import subprocess


@dataclass(frozen=True)
class VideoMeta:
    duration_ms: int
    fps_num: int
    fps_den: int
    fps: float
    width: int
    height: int
    aspect_ratio: str
    codec: str | None
    bitrate: int | None
    frame_count: int | None
    audio_tracks: int
    source_sha256: str | None = None
    probe_method: str = "ffprobe"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_fraction(value: str | None) -> Fraction:
    if not value or value in {"0/0", "N/A"}:
        return Fraction(0, 1)
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError):
        return Fraction(0, 1)


def _aspect_ratio(width: int, height: int) -> str:
    if width <= 0 or height <= 0:
        return "unknown"
    from math import gcd
    g = gcd(width, height)
    return f"{width // g}:{height // g}"


def normalize_ffprobe(payload: Mapping[str, Any], *, source_sha256: str | None = None) -> VideoMeta:
    streams = list(payload.get("streams") or [])
    fmt = dict(payload.get("format") or {})
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("ffprobe payload has no video stream")
    fps_q = _parse_fraction(video.get("avg_frame_rate") or video.get("r_frame_rate"))
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    duration_s = float(video.get("duration") or fmt.get("duration") or 0.0)
    bitrate_raw = video.get("bit_rate") or fmt.get("bit_rate")
    frames_raw = video.get("nb_frames")
    return VideoMeta(
        duration_ms=round(duration_s * 1000),
        fps_num=fps_q.numerator,
        fps_den=fps_q.denominator,
        fps=float(fps_q),
        width=width,
        height=height,
        aspect_ratio=_aspect_ratio(width, height),
        codec=video.get("codec_name"),
        bitrate=int(bitrate_raw) if bitrate_raw not in (None, "N/A") else None,
        frame_count=int(frames_raw) if frames_raw not in (None, "N/A") else None,
        audio_tracks=sum(1 for s in streams if s.get("codec_type") == "audio"),
        source_sha256=source_sha256,
    )


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def probe_video(path: str | Path, *, hash_source: bool = True, ffprobe_bin: str = "ffprobe") -> VideoMeta:
    path = Path(path)
    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-show_streams",
        "-show_format",
        "-of", "json",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(proc.stdout)
    digest = sha256_file(path) if hash_source else None
    return normalize_ffprobe(payload, source_sha256=digest)
