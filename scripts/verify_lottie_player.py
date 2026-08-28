from __future__ import annotations

import argparse
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import threading
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "runtime" / "lottie"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG screenshot: {path}")
    return struct.unpack(">II", data[16:24])


def _attr(dom: str, name: str) -> str | None:
    match = re.search(rf'data-{re.escape(name)}="([^"]*)"', dom)
    return match.group(1) if match else None


def _chrome_command(chrome: str, *, url: str, profile: Path, screenshot: Path | None = None) -> list[str]:
    command = [
        chrome,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--window-size=640,360",
        "--virtual-time-budget=1800",
        f"--user-data-dir={profile}",
    ]
    if screenshot is None:
        command.append("--dump-dom")
    else:
        command.append(f"--screenshot={screenshot}")
    command.append(url)
    return command


def _run(command: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=True)


def verify(
    *,
    root: Path,
    chrome: str,
    player_version: str,
    frames: tuple[int, ...] = (0, 30, 59),
) -> dict[str, Any]:
    animation_path = root / "animation.json"
    contract_path = root / "player_contract.json"
    bundle_path = root / "lottie.min.js"
    integrity_path = root / "npm_integrity.txt"
    for required in (animation_path, contract_path, bundle_path, integrity_path, root / "index.html"):
        if not required.exists():
            raise FileNotFoundError(required)

    document = json.loads(animation_path.read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    canonical_hash = canonical_json_hash(document)
    if canonical_hash != contract.get("document_sha256"):
        raise ValueError("player contract document hash does not match animation.json")
    expected_frames = int(contract.get("expected_frame_count", 0))
    if expected_frames <= 0:
        raise ValueError("player contract frame count missing")
    if any(frame < 0 or frame >= expected_frames for frame in frames):
        raise ValueError("requested verification frame outside animation range")

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    handler = partial(QuietHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    screenshots = root / "screenshots"
    screenshots.mkdir(exist_ok=True)
    frame_evidence: list[dict[str, Any]] = []
    try:
        port = server.server_address[1]
        for frame in frames:
            url = f"http://127.0.0.1:{port}/index.html?frame={frame}"
            with tempfile.TemporaryDirectory(prefix=f"motion-lottie-dom-{frame}-") as profile:
                dom_result = _run(_chrome_command(chrome, url=url, profile=Path(profile)))
            dom = dom_result.stdout
            if _attr(dom, "ready") != "true":
                raise RuntimeError(f"lottie player did not reach DOMLoaded-ready state at frame {frame}")
            current = int(float(_attr(dom, "current-frame") or "-1"))
            total = int(float(_attr(dom, "total-frames") or "-1"))
            svg_count = int(_attr(dom, "svg-count") or "0")
            requested = int(float(_attr(dom, "requested-frame") or "-1"))
            if requested != frame or current != frame:
                raise RuntimeError(f"lottie frame seek mismatch requested={frame} current={current}")
            if total != expected_frames:
                raise RuntimeError(f"lottie totalFrames mismatch {total}!={expected_frames}")
            if svg_count != 1:
                raise RuntimeError(f"expected exactly one SVG player surface, observed {svg_count}")

            screenshot = screenshots / f"frame_{frame:04d}.png"
            with tempfile.TemporaryDirectory(prefix=f"motion-lottie-shot-{frame}-") as profile:
                _run(_chrome_command(chrome, url=url, profile=Path(profile), screenshot=screenshot))
            width, height = png_dimensions(screenshot)
            if (width, height) != (640, 360):
                raise RuntimeError(f"screenshot dimensions mismatch {(width, height)}")
            frame_evidence.append({
                "frame": frame,
                "current_frame": current,
                "total_frames": total,
                "svg_count": svg_count,
                "png_sha256": sha256_file(screenshot),
                "png_bytes": screenshot.stat().st_size,
            })
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    unique_frame_hashes = {row["png_sha256"] for row in frame_evidence}
    if len(unique_frame_hashes) < 2:
        raise RuntimeError("physical Lottie frame evidence is visually invariant across sampled frames")

    return {
        "schema": "motion-os.lottie-physical-player/v1",
        "renderer": "lottie-web",
        "player_version": player_version,
        "player_bundle_sha256": sha256_file(bundle_path),
        "npm_dist_integrity": integrity_path.read_text(encoding="utf-8").strip(),
        "document_sha256": canonical_hash,
        "animation_file_sha256": sha256_file(animation_path),
        "expected_frame_count": expected_frames,
        "visual_duration_authority": "frame_count/fps",
        "fps": document["fr"],
        "frame_evidence": frame_evidence,
        "stable_layer_ids": contract.get("stable_layer_ids", []),
        "authority": "RENDERER_EXECUTED",
        "creative_authority": "none",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--chrome", default=None)
    parser.add_argument("--player-version", required=True)
    args = parser.parse_args()
    chrome = args.chrome or shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        raise SystemExit("Chrome/Chromium executable unavailable")
    evidence = verify(root=args.root.resolve(), chrome=str(chrome), player_version=args.player_version)
    output = args.root / "player_evidence.json"
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
