#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def run(name: str, cmd: list[str], *, cwd: Path = ROOT, required: bool = True) -> dict:
    started = time.time()
    print(f"\n==> {name}\n$ {' '.join(cmd)}")
    cp = subprocess.run(cmd, cwd=cwd, text=True)
    result = {
        "name": name,
        "command": cmd,
        "returncode": cp.returncode,
        "duration_s": round(time.time() - started, 3),
        "required": required,
        "status": "PASS" if cp.returncode == 0 else ("FAIL" if required else "WARN"),
    }
    if required and cp.returncode:
        raise SystemExit(cp.returncode)
    return result


def require_binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"required local binary missing: {name}")
    return path


def main() -> int:
    p = argparse.ArgumentParser(description="MOTION.OS local-first verification runner")
    p.add_argument("profile", choices=["quick", "analysis", "remotion", "security", "merge"], nargs="?", default="quick")
    p.add_argument("--json-out", type=Path)
    p.add_argument("--skip-install-check", action="store_true")
    args = p.parse_args()

    py = sys.executable
    results: list[dict] = []

    if not args.skip_install_check:
        results.append(run("import-smoke", [py, "-c", "import PIL, pytest, jsonschema; import src"]))

    if args.profile in {"quick", "merge"}:
        results.append(run("compileall", [py, "-m", "compileall", "-q", "src", "scripts"]))
        results.append(run("pytest", [py, "-m", "pytest", "-q"]))
        results.append(run("repo-health", [py, "scripts/repo_health.py"]))

    if args.profile in {"analysis", "merge"}:
        require_binary("ffmpeg")
        require_binary("ffprobe")
        results.append(run(
            "analysis-runtime",
            [py, "-m", "pytest", "-q", "tests/test_real_signal_providers.py", "tests/test_real_video_e2e.py", "tests/test_style_signature_vector.py"],
        ))

    if args.profile in {"remotion", "merge"}:
        require_binary("ffmpeg")
        require_binary("ffprobe")
        require_binary("node")
        require_binary("npm")
        runtime = ROOT / "runtime" / "remotion"
        if not (runtime / "node_modules").exists():
            raise SystemExit("runtime/remotion/node_modules missing; run `npm install --no-audit --no-fund` locally once before remotion verification")
        results.append(run("remotion-fixture", [py, "scripts/build_remotion_runtime_fixture.py"]))
        results.append(run("remotion-typecheck", ["npx", "tsc", "--noEmit"], cwd=runtime))
        results.append(run("remotion-compositions", ["npx", "remotion", "compositions", "src/index.ts"], cwd=runtime))
        (runtime / "out").mkdir(exist_ok=True)
        results.append(run(
            "remotion-render",
            ["npx", "remotion", "render", "src/index.ts", "MotionOSRuntime", "out/runtime-local.mp4", "--codec=h264", "--log=error"],
            cwd=runtime,
        ))
        results.append(run(
            "remotion-verify",
            [py, "scripts/verify_remotion_render.py", "--spec", "runtime/remotion/src/runtimeSpec.json", "--video", "runtime/remotion/out/runtime-local.mp4", "--out", "runtime/remotion/render_evidence.local.json"],
        ))

    if args.profile in {"security", "merge"}:
        results.append(run(
            "repo-security-gauntlet",
            [py, "scripts/security_gauntlet.py", "--json-out", ".artifacts/security-gauntlet.json"],
        ))
        pip_audit = require_binary("pip-audit")
        results.append(run("pip-audit", [pip_audit]))

    report = {
        "schema": "motion-os.local-verification/v1",
        "profile": args.profile,
        "python": sys.version.split()[0],
        "cwd": str(ROOT),
        "git_sha": os.environ.get("GITHUB_SHA"),
        "results": results,
        "status": "PASS",
    }
    text = json.dumps(report, indent=2)
    print("\n" + text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
