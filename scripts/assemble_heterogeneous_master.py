from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.renderers.assembly import (
    RenderArtifact,
    build_composite_plan,
    ffmpeg_assembly_argv,
)
from src.renderers.color_policy import (
    ArtifactColorBinding,
    BT709_SDR_LIMITED,
    ColorProfile,
    color_profile_from_probe,
    ffmpeg_color_filter,
    ffmpeg_output_color_args,
    pixel_family_from_probe,
)

OUT = ROOT / ".artifacts" / "heterogeneous-master"
OUT.mkdir(parents=True, exist_ok=True)
HF = ROOT / "runtime" / "hyperframes" / "out" / "runtime-local.mp4"
LOT = ROOT / "runtime" / "lottie" / "overlay-argb.mov"
AUDIO = OUT / "master-880hz.wav"
BASE = OUT / "base-bt709.mkv"
OVER = OUT / "overlay-bt709-alpha.mkv"
MASTER = OUT / "heterogeneous-master.mp4"
EVIDENCE = OUT / "heterogeneous_master_evidence.json"


def run(args: list[str]) -> None:
    subprocess.run(args, check=True, timeout=120)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return json.loads(completed.stdout)


def authoritative_frame_count(stream: dict) -> int:
    """Return fail-closed visual frame authority from ffprobe evidence.

    ``nb_read_frames`` is produced by ``ffprobe -count_frames`` and is preferred.
    ``nb_frames`` may be used as a corroborating/fallback container count when it is
    explicitly present. If both exist they must agree. Missing, N/A, malformed or
    non-positive counts can never be replaced by mux/container duration.
    """
    if not isinstance(stream, dict):
        raise ValueError("video stream evidence must be an object")

    parsed: dict[str, int] = {}
    for field in ("nb_read_frames", "nb_frames"):
        raw = stream.get(field)
        if raw in (None, "", "N/A"):
            continue
        if isinstance(raw, bool):
            raise ValueError(f"{field} must be a positive integer")
        try:
            value = int(raw)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{field} must be a positive integer") from exc
        if str(value) != str(raw).strip() and not isinstance(raw, int):
            raise ValueError(f"{field} must be an exact integer token")
        if value <= 0:
            raise ValueError(f"{field} must be positive")
        parsed[field] = value

    if not parsed:
        raise ValueError("counted visual frame evidence missing")
    if len(set(parsed.values())) != 1:
        raise ValueError("ffprobe frame-count evidence disagrees")
    return parsed.get("nb_read_frames", parsed["nb_frames"])


def probe_video(path: Path) -> dict:
    payload = probe(path)
    streams = [stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"]
    if len(streams) != 1:
        raise ValueError(f"expected_one_video_stream:{path.name}:{len(streams)}")
    return streams[0]


def lottie_source_profile(stream: dict) -> ColorProfile:
    """Bind browser screenshot semantics only after proving encoded RGB family.

    The PNG sequence is produced by lottie-web in Chrome and encoded losslessly as
    qtrle/ARGB. qtrle currently carries no color tags, so the browser sRGB
    declaration is evidence-bound to an RGB pixel family instead of being applied
    blindly to arbitrary renderer output.
    """
    family = pixel_family_from_probe("lottie-overlay", stream)
    if family != "rgb":
        raise ValueError(f"lottie_overlay_not_rgb:{family}")
    pix_fmt = str(stream.get("pix_fmt") or "").lower()
    if pix_fmt != "argb":
        raise ValueError(f"lottie_overlay_unqualified_pix_fmt:{pix_fmt or 'missing'}")

    color_keys = ("color_primaries", "color_transfer", "color_space", "color_range")
    present = {key: stream.get(key) for key in color_keys if stream.get(key)}
    if present:
        if len(present) != len(color_keys):
            raise ValueError("lottie_overlay_partial_color_metadata")
        observed = color_profile_from_probe(
            "lottie-overlay",
            stream,
            evidence_ref=f"ffprobe:qtrle-argb:{sha(LOT)}",
        )
        if observed.matrix != "gbr" or observed.range != "full":
            raise ValueError("lottie_overlay_observed_profile_not_rgb_full")
        return observed

    return ColorProfile(
        profile_id="declared:lottie-browser-srgb-full",
        primaries="bt709",
        transfer="iec61966-2-1",
        matrix="gbr",
        range="full",
        evidence=(
            "lottie-web@5.13.0:chrome-screenshot-sequence",
            f"ffprobe:qtrle:pix_fmt=argb:sha256:{sha(LOT)}",
        ),
    )


def normalize(
    source: Path,
    dest: Path,
    *,
    source_profile: ColorProfile,
    alpha: bool,
) -> str:
    binding = ArtifactColorBinding(source.stem, source_profile, preserve_alpha=alpha)
    graph = ffmpeg_color_filter(
        binding,
        BT709_SDR_LIMITED,
        input_label="0:v",
        output_label="norm",
    )
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-filter_complex",
            graph,
            "-map",
            "[norm]",
            "-c:v",
            "ffv1",
            "-level",
            "3",
            *ffmpeg_output_color_args(),
            str(dest),
        ]
    )
    return graph


def frame(path: Path, timestamp: float, out: Path) -> None:
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(path),
            "-frames:v",
            "1",
            str(out),
        ]
    )


def main() -> int:
    for physical_source in (HF, LOT):
        if not physical_source.exists():
            raise SystemExit(f"missing physical source: {physical_source}")

    hf_probe = probe_video(HF)
    lottie_probe = probe_video(LOT)

    hf_family = pixel_family_from_probe("hyperframes-base", hf_probe)
    if hf_family != "yuv":
        raise ValueError(f"hyperframes_base_expected_yuv:{hf_family}")
    hf_profile = color_profile_from_probe(
        "hyperframes-base",
        hf_probe,
        evidence_ref=f"ffprobe:sha256:{sha(HF)}",
    )
    lottie_profile = lottie_source_profile(lottie_probe)

    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=880:sample_rate=48000:duration=3",
            "-c:a",
            "pcm_s16le",
            str(AUDIO),
        ]
    )

    base_filter = normalize(HF, BASE, source_profile=hf_profile, alpha=False)
    overlay_filter = normalize(LOT, OVER, source_profile=lottie_profile, alpha=True)

    base = RenderArtifact(
        "hyperframes-base",
        "hyperframes",
        str(BASE),
        0,
        3000,
        640,
        360,
        30,
        False,
        (
            "PR#62@17da8a190a4492f1193716fa864bcd838bfcfd7b",
            f"sha256:{sha(BASE)}",
        ),
        0,
    )
    overlay = RenderArtifact(
        "lottie-overlay",
        "lottie",
        str(OVER),
        0,
        3000,
        640,
        360,
        30,
        True,
        (
            "PR#66@3513566b37fa6b8d15c357e78bb523c611669d0b",
            f"sha256:{sha(OVER)}",
        ),
        1,
    )
    plan = build_composite_plan(
        [base, overlay],
        width=640,
        height=360,
        fps=30,
        duration_ms=3000,
        audio_path=str(AUDIO),
    )
    argv = ffmpeg_assembly_argv(plan, str(MASTER), overwrite=True)
    argv[-1:-1] = ["-pix_fmt", "yuv420p", *ffmpeg_output_color_args()]
    run(argv)

    meta = probe(MASTER)
    streams = meta.get("streams", [])
    video = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio = [stream for stream in streams if stream.get("codec_type") == "audio"]
    errors: list[str] = []
    authoritative_frames: int | None = None
    if len(video) != 1:
        errors.append(f"video_stream_count:{len(video)}")
    if len(audio) != 1:
        errors.append(f"audio_stream_count:{len(audio)}")
    if video:
        stream = video[0]
        if (stream.get("width"), stream.get("height")) != (640, 360):
            errors.append("dimensions")
        if stream.get("avg_frame_rate") not in {"30/1", "30"}:
            errors.append(f"fps:{stream.get('avg_frame_rate')}")
        try:
            authoritative_frames = authoritative_frame_count(stream)
        except ValueError as exc:
            errors.append(f"frame_count:{exc}")
        else:
            if authoritative_frames != 90:
                errors.append(f"frames:{authoritative_frames}")
            # This is the canonical visual-duration check. Container/mux duration
            # below is only a secondary tail/integrity check and cannot replace it.
            if authoritative_frames / 30 != 3.0:
                errors.append(f"visual_duration:{authoritative_frames / 30}")
        expected = {
            "color_primaries": "bt709",
            "color_transfer": "bt709",
            "color_space": "bt709",
            "color_range": "tv",
        }
        for key, expected_value in expected.items():
            if stream.get(key) != expected_value:
                errors.append(f"{key}:{stream.get(key)}")

    duration = float(meta.get("format", {}).get("duration") or 0)
    if abs(duration - 3.0) > 0.08:
        errors.append(f"mux_duration:{duration}")

    base_png = OUT / "base-final-frame.png"
    master_png = OUT / "master-final-frame.png"
    frame(BASE, 2.90, base_png)
    frame(MASTER, 2.90, master_png)
    diff = ImageChops.difference(
        Image.open(base_png).convert("RGB"),
        Image.open(master_png).convert("RGB"),
    )
    mean = sum(ImageStat.Stat(diff).mean) / 3
    if mean < 0.15:
        errors.append(f"overlay_not_visibly_contributing:{mean}")

    lineage = json.loads(
        (ROOT / "integration" / "heterogeneous_master" / "SOURCE_LINEAGE.json").read_text()
    )
    payload = {
        "schema": "motion-os.heterogeneous-master-physical/v1",
        "authority": (
            "PHYSICAL_HETEROGENEOUS_MASTER_VERIFIED" if not errors else "EXECUTED_FAILED"
        ),
        "creative_authority": "none",
        "source_revision": subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "lineage": lineage,
        "pixel_families": {
            "hyperframes": hf_family,
            "lottie": pixel_family_from_probe("lottie-overlay", lottie_probe),
        },
        "source_probes": {
            "hyperframes": hf_probe,
            "lottie": lottie_probe,
        },
        "source_profiles": {
            "hyperframes": asdict(hf_profile),
            "lottie": asdict(lottie_profile),
        },
        "plan_hash": plan["plan_hash"],
        "filters": {"base": base_filter, "overlay": overlay_filter},
        "artifacts": {
            str(path.relative_to(ROOT)): {
                "sha256": sha(path),
                "bytes": path.stat().st_size,
            }
            for path in (HF, LOT, AUDIO, BASE, OVER, MASTER)
        },
        "probe": meta,
        "visual_frame_authority": {
            "frame_count": authoritative_frames,
            "fps": 30,
            "duration_seconds": (authoritative_frames / 30) if authoritative_frames is not None else None,
            "source": "ffprobe -count_frames / nb_read_frames with explicit nb_frames corroboration",
        },
        "mux_duration_seconds": duration,
        "overlay_visual_difference_mae": mean,
        "errors": errors,
        "ok": not errors,
    }
    EVIDENCE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
