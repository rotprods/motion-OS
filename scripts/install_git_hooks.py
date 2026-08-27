#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".githooks" / "pre-push"


def main() -> int:
    if not (ROOT / ".git").exists():
        raise SystemExit("run inside a git checkout")
    mode = HOOK.stat().st_mode
    HOOK.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT, check=True)
    configured = subprocess.check_output(["git", "config", "--get", "core.hooksPath"], cwd=ROOT, text=True).strip()
    print(f"MOTION.OS hooks installed: {configured}")
    print("pre-push now runs local verification and blocks pushes on applicable failures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
