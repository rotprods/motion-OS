#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from src.benchmarks.fixtures import fixture_by_id, fixture_manifest, smoke_fixtures

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SPEC = ROOT / "runtime" / "remotion" / "src" / "runtimeSpec.json"
RUNTIME_DIR = ROOT / "runtime" / "remotion"
OUT_ROOT = ROOT / ".artifacts" / "benchmark-smoke"


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def generate() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "fixture_manifest.json").write_text(
        json.dumps(fixture_manifest(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def render_one(brief_id: str) -> dict:
    fixture = fixture_by_id(brief_id)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    backup = OUT_ROOT / "runtimeSpec.original.json"
    if not backup.exists():
        shutil.copy2(RUNTIME_SPEC, backup)
    RUNTIME_SPEC.write_text(json.dumps(fixture.runtime_spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_dir = RUNTIME_DIR / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    runtime_out = out_dir / "runtime.mp4"
    subprocess.run(["npm", "run", "render"], cwd=RUNTIME_DIR, check=True)
    if not runtime_out.exists() or runtime_out.stat().st_size <= 0:
        raise RuntimeError("Remotion produced no benchmark artifact")
    artifact = OUT_ROOT / f"{brief_id}.mp4"
    shutil.copy2(runtime_out, artifact)
    probe_raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-count_frames", "-show_entries", "stream=width,height,avg_frame_rate,nb_read_frames",
        "-of", "json", str(artifact),
    ], text=True)
    probe = json.loads(probe_raw)["streams"][0]
    num, den = probe["avg_frame_rate"].split("/")
    fps = float(num) / float(den)
    frame_count = int(probe["nb_read_frames"])
    visual_duration = frame_count / fps
    mechanical_pass = bool(
        probe["width"] == 640
        and probe["height"] == 360
        and frame_count == 90
        and abs(fps - 30.0) < 1e-9
        and abs(visual_duration - 3.0) < 1e-9
    )
    evidence = {
        "brief_id": fixture.brief_id,
        "style_family": fixture.style_family,
        "brief_sha256": fixture.brief_sha256(),
        "runtime_spec_sha256": fixture.spec_sha256(),
        "artifact_sha256": _sha(artifact),
        "artifact_path": str(artifact.relative_to(ROOT)),
        "frame_count": frame_count,
        "fps": fps,
        "visual_duration_seconds": visual_duration,
        "mechanical_pass": mechanical_pass,
        "creative_authority": "BLOCKED",
        "creative_blocker": "authoritative creative review not executed",
    }
    (OUT_ROOT / f"{brief_id}.evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not mechanical_pass:
        raise RuntimeError(f"mechanical benchmark verification failed for {brief_id}")
    return evidence


def restore() -> None:
    backup = OUT_ROOT / "runtimeSpec.original.json"
    if backup.exists():
        shutil.copy2(backup, RUNTIME_SPEC)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate")
    one = sub.add_parser("render-one")
    one.add_argument("brief_id")
    sub.add_parser("restore")
    args = parser.parse_args()
    if args.command == "generate":
        generate()
    elif args.command == "render-one":
        render_one(args.brief_id)
    elif args.command == "restore":
        restore()


if __name__ == "__main__":
    main()
