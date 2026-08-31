from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "runtime" / "hyperframes"
DEFAULT_VIDEO = RUNTIME_DIR / "out" / "runtime-local.mp4"
DEFAULT_EVIDENCE = RUNTIME_DIR / "render_evidence.local.json"
DEFAULT_COMPILER_EVIDENCE = RUNTIME_DIR / "compiler_evidence.json"
EXPECTED_HYPERFRAMES_VERSION = "0.8.17"


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


def verify_compiler_provenance(
    compiler_evidence_path: Path,
    *,
    project_dir: Path,
    runtime_version: str,
    run_id: str | None,
    source_revision: str | None,
) -> dict:
    """Verify the physical render's upstream compiler/project identity.

    Compiler evidence is only useful if every emitted file still matches its recorded
    digest. Runtime and CI identities are transport/runtime observations and become part
    of the final evidence chain; absence prevents VERIFIED authority rather than being
    silently invented.
    """
    errors: list[str] = []
    if not compiler_evidence_path.is_file():
        return {"ok": False, "errors": ["compiler_evidence_missing"]}
    try:
        compiler = json.loads(compiler_evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"ok": False, "errors": ["compiler_evidence_invalid"]}

    spec_sha = str(compiler.get("spec_sha256", "")).lower()
    if len(spec_sha) != 64 or any(c not in "0123456789abcdef" for c in spec_sha):
        errors.append("compiler_spec_sha_invalid")

    emitted = compiler.get("emitted_sha256")
    verified_files: dict[str, str] = {}
    if not isinstance(emitted, dict) or not emitted:
        errors.append("compiler_emitted_hashes_missing")
    else:
        for name, expected in sorted(emitted.items()):
            if not isinstance(name, str) or Path(name).name != name:
                errors.append("unsafe_emitted_file_name")
                continue
            expected = str(expected).lower()
            path = project_dir / name
            if not path.is_file():
                errors.append(f"emitted_file_missing:{name}")
                continue
            observed = sha256_file(path)
            verified_files[name] = observed
            if observed != expected:
                errors.append(f"emitted_file_hash_mismatch:{name}")

    if runtime_version != EXPECTED_HYPERFRAMES_VERSION:
        errors.append("hyperframes_version_mismatch")
    if not run_id or not str(run_id).strip():
        errors.append("runtime_run_id_missing")
    revision = str(source_revision or "").strip().lower()
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        errors.append("source_revision_missing_or_invalid")

    return {
        "ok": not errors,
        "errors": errors,
        "compiler_evidence_sha256": sha256_file(compiler_evidence_path),
        "spec_sha256": spec_sha,
        "verified_emitted_sha256": verified_files,
        "hyperframes_version": runtime_version,
        "runtime_run_id": str(run_id or ""),
        "source_revision": revision,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", nargs="?", type=Path, default=DEFAULT_VIDEO)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--compiler-evidence", type=Path, default=DEFAULT_COMPILER_EVIDENCE)
    parser.add_argument("--project-dir", type=Path, default=RUNTIME_DIR)
    parser.add_argument("--hyperframes-version", default=EXPECTED_HYPERFRAMES_VERSION)
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID"))
    parser.add_argument("--source-revision", default=os.environ.get("GITHUB_SHA"))
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
    provenance = verify_compiler_provenance(
        args.compiler_evidence,
        project_dir=args.project_dir,
        runtime_version=args.hyperframes_version,
        run_id=args.run_id,
        source_revision=args.source_revision,
    )
    overall_ok = bool(verdict["ok"] and provenance["ok"])
    evidence = {
        "schema": "motion-os.hyperframes-physical-runtime/v2",
        "renderer": "hyperframes",
        "artifact": media,
        "verification": verdict,
        "provenance": provenance,
        "artifact_binding": {
            "media_sha256": media["sha256"],
            "compiler_evidence_sha256": provenance.get("compiler_evidence_sha256"),
            "spec_sha256": provenance.get("spec_sha256"),
            "runtime_run_id": provenance.get("runtime_run_id"),
            "source_revision": provenance.get("source_revision"),
            "hyperframes_version": provenance.get("hyperframes_version"),
        },
        "authority": "VERIFIED" if overall_ok else "EXECUTED",
        "creative_authority": "none",
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
