#!/usr/bin/env python3
"""Local/CI verification: required gates fail closed and retain failure receipts."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


class VerificationStopped(Exception):
    """The failed step has already been recorded; stop without masking its status."""


def run(name: str, cmd: list[str], *, cwd: Path | None = None,
        required: bool = True, timeout: float = 600, quiet: bool = False) -> dict:
    started = time.monotonic()
    print(f"\n==> {name}", flush=True)
    result = {"name": name, "command": cmd, "returncode": None,
              "duration_s": 0.0, "required": required, "status": "BLOCKED"}
    try:
        cp = subprocess.run(cmd, cwd=ROOT if cwd is None else cwd, text=True,
                            shell=False, timeout=timeout,
                            stdout=subprocess.DEVNULL if quiet else None,
                            stderr=subprocess.DEVNULL if quiet else None)
        result.update(returncode=cp.returncode,
                      status="PASS" if cp.returncode == 0 else "FAIL")
        if cp.returncode:
            result["reason"] = "command_failed"
    except subprocess.TimeoutExpired:
        result["reason"] = "command_timeout"
    except OSError:
        result["reason"] = "command_unavailable"
    except KeyboardInterrupt:
        result["reason"] = "interrupted"
    result["duration_s"] = round(time.monotonic() - started, 3)
    return result


def _write_report(path: Path | None, report: dict) -> None:
    """Replace receipts atomically. Never follow symlinks or write outside ROOT."""
    if path is None:
        return
    root = ROOT.resolve()
    target = path if path.is_absolute() else root / path
    relative = target.relative_to(root)
    if not relative.parts or ".." in relative.parts or target.suffix != ".json":
        raise ValueError("invalid_report_path")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlink_report_path")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                         prefix=".verification-", delete=False) as stream:
            temporary = stream.name
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def _observed_head() -> str | None:
    try:
        cp = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT,
                            text=True, capture_output=True, timeout=10, shell=False)
        value = cp.stdout.strip()
        if cp.returncode == 0 and len(value) in (40, 64) and all(c in "0123456789abcdef" for c in value):
            return value
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MOTION.OS local-first verification runner")
    parser.add_argument("profile", choices=["quick", "analysis", "remotion", "security", "merge"],
                        nargs="?", default="quick")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--skip-install-check", action="store_true")
    args = parser.parse_args(argv)
    report = {"schema": "motion-os.local-verification/v1", "profile": args.profile,
              "python": sys.version.split()[0], "cwd": str(ROOT), "git_sha": None,
              "results": [], "status": "RUNNING"}

    def record(result: dict) -> None:
        report["results"].append(result)
        if result["status"] != "PASS":
            report["status"] = result["status"]
        _write_report(args.json_out, report)
        if result["status"] != "PASS":
            raise VerificationStopped

    def blocked(name: str, reason: str) -> None:
        record({"name": name, "required": True, "status": "BLOCKED", "reason": reason,
                "returncode": None, "duration_s": 0.0})

    def execute(name: str, cmd: list[str], **kwargs) -> None:
        record(run(name, cmd, **kwargs))

    def require_binary(name: str) -> None:
        if shutil.which(name) is None:
            blocked(name, "required_binary_missing")

    try:
        # Invalidate an old PASS before attempting a tool, import, scan or test.
        _write_report(args.json_out, report)
        report["git_sha"] = _observed_head()
        _write_report(args.json_out, report)
        py = sys.executable
        if args.profile in {"security", "merge"}:
            # Availability is checked early; --skip-install-check cannot bypass it.
            if importlib.util.find_spec("pip_audit") is None:
                blocked("pip-audit", "required_module_missing")
            scanner = ROOT / "scripts/security_static.py"
            if not scanner.is_file() or scanner.is_symlink():
                blocked("static-security", "required_scanner_missing")
        if not args.skip_install_check:
            execute("import-smoke", [py, "-c", "import PIL, pytest, jsonschema; import src"])
        if args.profile in {"quick", "merge"}:
            execute("compileall", [py, "-m", "compileall", "-q", "src", "scripts"])
            execute("pytest", [py, "-m", "pytest", "-q"])
            execute("repo-health", [py, "scripts/repo_health.py"])
        if args.profile in {"analysis", "merge"}:
            require_binary("ffmpeg")
            require_binary("ffprobe")
            execute("analysis-runtime", [py, "-m", "pytest", "-q", "tests/test_real_signal_providers.py",
                                         "tests/test_real_video_e2e.py", "tests/test_style_signature_vector.py"])
        if args.profile in {"remotion", "merge"}:
            for binary in ("ffmpeg", "ffprobe", "node", "npm", "npx"):
                require_binary(binary)
            runtime = ROOT / "runtime/remotion"
            if not (runtime / "node_modules").is_dir():
                blocked("remotion-install", "frozen_install_required")
            execute("remotion-fixture", [py, "scripts/build_remotion_runtime_fixture.py"])
            execute("remotion-typecheck", ["npx", "--no-install", "tsc", "--noEmit"], cwd=runtime)
            execute("remotion-compositions", ["npx", "--no-install", "remotion", "compositions", "src/index.ts"], cwd=runtime)
            (runtime / "out").mkdir(exist_ok=True)
            execute("remotion-render", ["npx", "--no-install", "remotion", "render", "src/index.ts", "MotionOSRuntime",
                                        "out/runtime-local.mp4", "--codec=h264", "--log=error"], cwd=runtime)
            execute("remotion-verify", [py, "scripts/verify_remotion_render.py", "--spec", "runtime/remotion/src/runtimeSpec.json",
                                        "--video", "runtime/remotion/out/runtime-local.mp4", "--out", "runtime/remotion/render_evidence.local.json"])
        if args.profile in {"security", "merge"}:
            execute("static-security", [py, "scripts/security_static.py"])
            # Audit this interpreter's environment. Raw external errors are not logged.
            execute("pip-audit", [py, "-m", "pip_audit", "--progress-spinner", "off"], timeout=180, quiet=True)
        if not report["results"]:
            blocked("verification", "no_checks_executed")
        report["status"] = "PASS"
    except VerificationStopped:
        pass
    except KeyboardInterrupt:
        report["status"] = "BLOCKED"
        report["results"].append({"name": "verification", "status": "BLOCKED", "required": True,
                                  "reason": "interrupted", "returncode": None})
    except Exception as exc:
        # Keep the exception type for diagnosis, never an untrusted exception message.
        report["status"] = "BLOCKED"
        report["results"].append({"name": "verification", "status": "BLOCKED", "required": True,
                                  "reason": "verification_internal_error", "error_type": type(exc).__name__, "returncode": None})
    try:
        _write_report(args.json_out, report)
    except (OSError, ValueError):
        report["status"] = "BLOCKED"
        report["receipt_error"] = "report_write_failed"
    print("\n" + json.dumps(report, indent=2, allow_nan=False))
    return 0 if report["status"] == "PASS" else (1 if report["status"] == "FAIL" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
