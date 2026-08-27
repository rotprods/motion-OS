#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.content.avatar_script_engine import (
    build_avatar_request,
    estimate_duration_s,
    get_profile,
    schema_validate,
    validate_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Phase 06 avatar manifest and compile provider request JSON.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--profile", default="heygen_rot_canonical_v1")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    profile = get_profile(args.profile)
    schema_validate(manifest)
    issues = validate_manifest(manifest, profile)
    for issue in issues:
        print(f"{issue.severity} {issue.code}: {issue.message}")
    if any(i.severity == "ERROR" for i in issues):
        return 2

    estimate = estimate_duration_s(
        manifest["script_tts_text"],
        profile,
        phonetic_expansion_chars=max(len(manifest["script_tts_text"]) - len(manifest["script_display_text"]), 0),
    )
    request = build_avatar_request(manifest, profile)
    payload = {
        "content_id": manifest["content_id"],
        "duration_estimate_s": estimate,
        "provider_request": request,
        "semantic_beats": manifest["semantic_beats"],
        "downstream_edit_cues": manifest["downstream_edit_cues"],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print(args.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
