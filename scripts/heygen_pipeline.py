#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.content.content_factory import preflight_manifest
from src.avatar.heygen_adapter import compile_request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILES = ROOT / "config" / "avatar_profiles.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="MOTION.OS /heygen preflight + provider request compiler")
    p.add_argument("manifest", type=Path, help="avatar content manifest JSON")
    p.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    p.add_argument("--profile", default="heygen_rot_canonical_v1")
    p.add_argument("--title", default="MOTION.OS avatar render")
    p.add_argument("--motion-prompt", default=None)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    manifest = load_json(args.manifest)
    profiles = load_json(args.profiles)["profiles"]
    profile = profiles[args.profile]
    result = preflight_manifest(manifest, profile)
    report = {
        "command": "/heygen",
        "preflight": {
            "ok": result.ok,
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            "estimated_duration_s": result.estimated_duration_s,
        },
        "provider_request": None,
    }
    if result.ok:
        report["provider_request"] = compile_request(
            manifest, profile, title=args.title, motion_prompt=args.motion_prompt
        )
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
