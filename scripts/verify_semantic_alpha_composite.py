from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.renderers.runtime_verifier import probe_media


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rgb_error(observed: tuple[int, int, int], expected: tuple[int, int, int]) -> int:
    return max(abs(int(a) - int(b)) for a, b in zip(observed, expected))


def classify_semantic_pixels(
    transparent_region_rgb: tuple[int, int, int],
    opaque_region_rgb: tuple[int, int, int],
    *,
    base_rgb: tuple[int, int, int] = (0, 0, 255),
    overlay_rgb: tuple[int, int, int] = (255, 0, 0),
    tolerance: int = 12,
) -> dict:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    transparent_error = _rgb_error(transparent_region_rgb, base_rgb)
    opaque_error = _rgb_error(opaque_region_rgb, overlay_rgb)
    errors: list[str] = []
    if transparent_error > tolerance:
        errors.append("transparent_region_did_not_preserve_base")
    if opaque_error > tolerance:
        errors.append("opaque_region_did_not_apply_overlay")
    return {
        "ok": not errors,
        "errors": errors,
        "transparent_region_rgb": list(transparent_region_rgb),
        "opaque_region_rgb": list(opaque_region_rgb),
        "expected_base_rgb": list(base_rgb),
        "expected_overlay_rgb": list(overlay_rgb),
        "transparent_region_max_channel_error": transparent_error,
        "opaque_region_max_channel_error": opaque_error,
        "tolerance": tolerance,
    }


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)


def build_fixture(out: Path) -> dict[str, Path]:
    out.mkdir(parents=True, exist_ok=True)
    base_png = out / "base.png"
    overlay_png = out / "overlay.png"
    overlay_mov = out / "overlay-alpha.mov"
    composite_png = out / "composite.png"

    base = Image.new("RGB", (64, 64), (0, 0, 255))
    base.save(base_png)

    overlay = Image.new("RGBA", (64, 64), (255, 0, 0, 0))
    for x in range(32, 64):
        for y in range(64):
            overlay.putpixel((x, y), (255, 0, 0, 255))
    overlay.save(overlay_png)

    run([
        "ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(overlay_png),
        "-t", "1", "-r", "30", "-c:v", "qtrle", "-pix_fmt", "argb", str(overlay_mov),
    ])
    run([
        "ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(base_png), "-i", str(overlay_mov),
        "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto:shortest=1",
        "-frames:v", "1", str(composite_png),
    ])
    return {
        "base_png": base_png,
        "overlay_png": overlay_png,
        "overlay_mov": overlay_mov,
        "composite_png": composite_png,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / ".artifacts" / "semantic-alpha")
    parser.add_argument("--evidence", type=Path, default=None)
    args = parser.parse_args()
    evidence_path = args.evidence or args.out / "semantic_alpha_evidence.json"

    files = build_fixture(args.out)
    overlay_media = probe_media(files["overlay_mov"])
    composite = Image.open(files["composite_png"]).convert("RGB")
    transparent_rgb = tuple(composite.getpixel((16, 32)))
    opaque_rgb = tuple(composite.getpixel((48, 32)))
    semantic = classify_semantic_pixels(transparent_rgb, opaque_rgb)

    errors = list(semantic["errors"])
    if not overlay_media.get("has_alpha"):
        errors.append("source_overlay_missing_physical_alpha")
    if overlay_media.get("pix_fmt") not in {"argb", "rgba", "abgr", "bgra"} and not str(overlay_media.get("pix_fmt", "")).startswith(("yuva", "gbrap")):
        errors.append("source_overlay_pixel_format_not_alpha_qualified")

    payload = {
        "schema": "motion-os.semantic-alpha-composite/v1",
        "fixture": {
            "geometry": "64x64",
            "base": "opaque blue",
            "overlay": "left half fully transparent red; right half fully opaque red",
            "semantic_expectation": "left output remains base blue; right output becomes overlay red",
        },
        "overlay_media": overlay_media,
        "semantic_pixels": semantic,
        "artifacts": {
            name: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for name, path in files.items()
        },
        "errors": errors,
        "ok": not errors,
        "authority": "PHYSICAL_SEMANTIC_ALPHA_VERIFIED" if not errors else "EXECUTED_FAILED",
        "creative_authority": "none",
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
