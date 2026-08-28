#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

PATTERNS: dict[str, tuple[str, ...]] = {
    "analysis": (
        r"^src/extraction/",
        r"^src/normalization/",
        r"^tests/test_real_",
        r"^tests/test_style_signature_vector\.py$",
        r"^scripts/analyze_video\.py$",
        r"^pyproject\.toml$",
    ),
    "remotion": (
        r"^runtime/remotion/",
        r"^src/compilers/remotion",
        r"^scripts/(build_remotion_runtime_fixture|verify_remotion_render)\.py$",
        r"^tests/test_remotion_runtime_contract\.py$",
        r"^\.github/workflows/remotion-runtime\.yml$",
    ),
    "security": (
        r"^pyproject\.toml$",
        r"^requirements",
        r"^uv\.lock$",
        r"^poetry\.lock$",
        r"^runtime/remotion/package(-lock)?\.json$",
        r"^SECURITY\.md$",
        r"^\.github/workflows/",
    ),
    "full": (
        r"^\.github/workflows/merge-gate\.yml$",
        r"^scripts/local_verify\.py$",
        r"^scripts/change_impact\.py$",
        r"^scripts/repo_health\.py$",
        r"^scripts/agent_event\.py$",
        r"^schemas/agent_event\.schema\.json$",
        r"^\.githooks/pre-push$",
        r"^scripts/install_git_hooks\.py$",
        r"^docs/MERGE_SAFE_TRAIN\.md$",
        r"^AGENTS\.md$",
        r"^STATE\.md$",
        r"^TASKS\.md$",
        r"^HANDOFF\.md$",
        r"^state/project_state\.json$",
        r"^state/checkpoints\.json$",
        r"^state/github_sync\.json$",
        r"^state/drive_sync\.json$",
        r"^registry/artifact_registry\.json$",
        r"^coordination/ACTIVE_AGENTS\.yaml$",
        r"^src/qa/alignment\.py$",
        r"^config/alignment_weights\.(json|yaml)$",
    ),
}


def classify(paths: list[str], *, force_full: bool = False) -> dict[str, bool]:
    clean = [p.strip() for p in paths if p.strip()]
    result = {
        name: any(re.search(pattern, path) for path in clean for pattern in patterns)
        for name, patterns in PATTERNS.items()
    }
    if force_full or result["full"]:
        result = {name: True for name in result}
    return result


def main() -> int:
    p = argparse.ArgumentParser(description="Classify MOTION.OS changed paths for local/cloud verification")
    p.add_argument("paths", nargs="*")
    p.add_argument("--force-full", action="store_true")
    p.add_argument("--check", choices=sorted(PATTERNS))
    p.add_argument("--github-output", type=Path)
    args = p.parse_args()
    paths = args.paths or sys.stdin.read().splitlines()
    result = classify(paths, force_full=args.force_full)
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as fh:
            for key, value in result.items():
                fh.write(f"{key}={'true' if value else 'false'}\n")
    if args.check:
        return 0 if result[args.check] else 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
