#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
_HASH_CHUNK_BYTES = 1024 * 1024
_SENTINEL = "MOTION.OS PIXEL SENSITIVITY 7F2A"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def mutate_typography_spec(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    mutated = deepcopy(spec)
    scenes = mutated.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("runtime spec must contain scenes")
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        layers = scene.get("layers")
        if not isinstance(layers, list):
            continue
        for layer in layers:
            if not isinstance(layer, dict) or layer.get("layerClass") != "TYPOGRAPHY":
                continue
            data = layer.get("data")
            if not isinstance(data, dict):
                continue
            text = data.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            changed = f"{text.strip()} · {_SENTINEL}"
            data["text"] = changed
            start = scene.get("from")
            duration = scene.get("durationInFrames")
            if not isinstance(start, int) or isinstance(start, bool):
                raise ValueError("scene.from must be an integer")
            if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
                raise ValueError("scene.durationInFrames must be a positive integer")
            frame_index = start + min(duration - 1, max(1, duration // 2))
            return mutated, {
                "scene_id": scene.get("id"),
                "layer_id": layer.get("id"),
                "frame_index": frame_index,
                "original_text_sha256": _sha256_bytes(text.encode("utf-8")),
                "mutated_text_sha256": _sha256_bytes(changed.encode("utf-8")),
                "original_text_length": len(text),
                "mutated_text_length": len(changed),
            }
    raise ValueError("no non-empty TYPOGRAPHY layer text found for sensitivity probe")


def compare_frame_bytes(baseline: bytes, variant: bytes) -> dict[str, Any]:
    if not baseline or not variant:
        raise ValueError("raw frame bytes must be non-empty")
    if len(baseline) != len(variant):
        raise ValueError("raw frame byte lengths differ")
    changed = sum(left != right for left, right in zip(baseline, variant))
    return {
        "baseline_frame_sha256": _sha256_bytes(baseline),
        "variant_frame_sha256": _sha256_bytes(variant),
        "raw_frame_bytes": len(baseline),
        "changed_rgb_bytes": changed,
        "changed_ratio": changed / len(baseline),
    }


def _raw_frame(path: Path, *, frame_index: int, width: int, height: int) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg unavailable")
    command = [
        ffmpeg,
        "-v",
        "error",
        "-i",
        str(path),
        "-map",
        "0:v:0",
        "-vf",
        f"select=eq(n\\,{frame_index})",
        "-frames:v",
        "1",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "pipe:1",
    ]
    cp = subprocess.run(command, capture_output=True, check=False, timeout=60, shell=False)
    if cp.returncode != 0:
        raise RuntimeError("ffmpeg frame extraction failed")
    expected = width * height * 3
    if len(cp.stdout) != expected:
        raise RuntimeError(f"unexpected raw frame bytes: {len(cp.stdout)} != {expected}")
    return cp.stdout


def _render_variant(runtime_dir: Path, output: Path) -> None:
    npx = shutil.which("npx")
    if not npx:
        raise RuntimeError("npx unavailable")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    cp = subprocess.run(
        [
            npx,
            "--no-install",
            "remotion",
            "render",
            "src/index.ts",
            "MotionOSRuntime",
            str(output.relative_to(runtime_dir)),
            "--codec=h264",
            "--log=error",
        ],
        cwd=runtime_dir,
        text=True,
        shell=False,
        timeout=180,
    )
    if cp.returncode != 0:
        raise RuntimeError("sensitivity variant render failed")
    if not output.is_file() or output.stat().st_size <= 0:
        raise RuntimeError("sensitivity variant render missing")


def _atomic_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".sensitivity-",
            delete=False,
        ) as stream:
            temp_name = stream.name
            json.dump(document, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)


def verify_input_sensitivity(
    *,
    spec_path: Path,
    baseline_video: Path,
    evidence_path: Path,
    variant_video: Path,
) -> dict[str, Any]:
    if not spec_path.is_file() or not baseline_video.is_file() or not evidence_path.is_file():
        raise ValueError("spec, baseline video and runtime evidence must exist")
    original_bytes = spec_path.read_bytes()
    original_sha = _sha256_bytes(original_bytes)
    spec = json.loads(original_bytes.decode("utf-8"))
    if not isinstance(spec, dict):
        raise ValueError("runtime spec must be an object")
    project = spec.get("project")
    if not isinstance(project, dict):
        raise ValueError("runtime spec project missing")
    width = project.get("width")
    height = project.get("height")
    if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
        raise ValueError("project.width must be positive integer")
    if not isinstance(height, int) or isinstance(height, bool) or height <= 0:
        raise ValueError("project.height must be positive integer")

    mutated, mutation = mutate_typography_spec(spec)
    mutated_bytes = (json.dumps(mutated, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    if _sha256_bytes(mutated_bytes) == original_sha:
        raise AssertionError("sensitivity mutation did not change runtime spec")

    restored = False
    try:
        spec_path.write_bytes(mutated_bytes)
        _render_variant(spec_path.parents[1], variant_video)
    finally:
        spec_path.write_bytes(original_bytes)
        restored = _sha256_file(spec_path) == original_sha
    if not restored:
        raise AssertionError("runtime spec was not restored byte-for-byte")

    frame_index = int(mutation["frame_index"])
    baseline_frame = _raw_frame(baseline_video, frame_index=frame_index, width=width, height=height)
    variant_frame = _raw_frame(variant_video, frame_index=frame_index, width=width, height=height)
    frame_diff = compare_frame_bytes(baseline_frame, variant_frame)
    if frame_diff["changed_rgb_bytes"] < 100:
        raise AssertionError(
            f"Studio typography mutation was not materially visible: {frame_diff['changed_rgb_bytes']} RGB bytes changed"
        )

    report = {
        "schema": "motion-os.remotion-input-sensitivity/v1",
        "gate": "PASS",
        "mutation": mutation,
        "spec_original_sha256": original_sha,
        "spec_mutated_sha256": _sha256_bytes(mutated_bytes),
        "spec_restored_byte_exact": restored,
        "baseline_video_sha256": _sha256_file(baseline_video),
        "variant_video_sha256": _sha256_file(variant_video),
        "baseline_video_bytes": baseline_video.stat().st_size,
        "variant_video_bytes": variant_video.stat().st_size,
        **frame_diff,
        "authority": "technical_input_to_pixel_causality",
        "creative_authority": "none",
    }

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise ValueError("runtime evidence must be an object")
    evidence["input_sensitivity"] = report
    _atomic_json(evidence_path, evidence)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Prove Studio layer text causally changes rendered pixels")
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--baseline-video", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--variant-video", required=True, type=Path)
    args = parser.parse_args()
    report = verify_input_sensitivity(
        spec_path=args.spec,
        baseline_video=args.baseline_video,
        evidence_path=args.evidence,
        variant_video=args.variant_video,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
