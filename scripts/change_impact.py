#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import subprocess

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
        # Reconcile PR56 authority coverage, including future shared contracts.
        r"^(STATE|TASKS|HANDOFF|GOAL)\.md$",
        r"^state/(project_state|checkpoints|github_sync|drive_sync)\.json$",
        r"^(schemas|config|registry|coordination)/",
        r"^src/(avatar|content|coordination|skills|qa|graph|studio|primitives)/",
        r"^\.github/",
        r"^scripts/(repo_health|verify_node_lock)\.py$",
        r"^tests/test_ci_convergence\.py$",
        r"^\.github/workflows/merge-gate\.yml$",
        r"^scripts/local_verify\.py$",
        r"^scripts/change_impact\.py$",
        r"^scripts/merge_safe_gate\.py$",
        r"^tests/test_merge_safe_gate\.py$",
        r"^scripts/agent_event\.py$",
        r"^schemas/agent_event\.schema\.json$",
        r"^\.githooks/pre-push$",
        r"^scripts/install_git_hooks\.py$",
        r"^docs/MERGE_SAFE_TRAIN\.md$",
        r"^AGENTS\.md$",
    ),
}


# Plain documentation keeps the cheap gate; unknown execution surfaces do not.
DOCUMENTATION = re.compile(
    r"^(?:(?:README|CHANGELOG|CONTRIBUTING)(?:_[A-Za-z0-9_-]+)?\.md|"
    r"LICENSE(?:\.[A-Za-z]+)?|(?:docs|reports|evidence)/[A-Za-z0-9_./ -]+\.(?:md|rst|txt))$"
)
MAX_INPUT_BYTES = 1_048_576


def classify(paths: list[str], *, force_full: bool = False) -> dict[str, bool]:
    result = dict.fromkeys(PATTERNS, False)
    if type(force_full) is not bool or force_full or not isinstance(paths, list):
        return dict.fromkeys(PATTERNS, True)
    for path in paths:
        # Reject quoted Git output, traversal, controls and ambiguous whitespace.
        if (not isinstance(path, str) or not path or path != path.strip()
                or len(path) > 4096 or any(ord(c) < 32 or ord(c) == 127 for c in path)
                or '\\' in path or '"' in path
                or any(part in ('', '.', '..') for part in path.split('/'))):
            return dict.fromkeys(PATTERNS, True)
        matched = False
        for name, patterns in PATTERNS.items():
            if any(re.search(pattern, path) for pattern in patterns):
                result[name] = True
                matched = True
        if not matched and not DOCUMENTATION.fullmatch(path):
            result['full'] = True
    if result['full']:
        return dict.fromkeys(PATTERNS, True)
    return result


def changed_paths(base: str, head: str = 'HEAD', *, cwd: Path | None = None) -> tuple[list[str], bool]:
    """One local/cloud Git transport. Uncertain history forces every gate.

    Disable rename detection so both the old (deleted) and new path are routed.
    Resolve revisions first; never interpolate ref/path text into shell commands.
    """
    def git(*args: str) -> bytes:
        cp = subprocess.run(['git', *args], cwd=cwd, capture_output=True, timeout=20)
        if cp.returncode or len(cp.stdout) > MAX_INPUT_BYTES:
            raise ValueError('git_history_unavailable')
        return cp.stdout

    try:
        shas = []
        for ref in (base, head):
            if (not isinstance(ref, str) or len(ref) > 255 or ref.startswith('-')
                    or not re.fullmatch(r'[A-Za-z0-9_./^~@{}-]+', ref)):
                raise ValueError('invalid_revision')
            sha = git('rev-parse', '--verify', '--end-of-options', ref + '^{commit}').decode().strip()
            if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', sha):
                raise ValueError('invalid_revision')
            shas.append(sha)
        raw = git('diff', '--no-renames', '--name-only', '-z', shas[0] + '...' + shas[1], '--')
        if raw and not raw.endswith(b'\0'):
            raise ValueError('invalid_git_transport')
        return ([p.decode('utf-8') for p in raw.split(b'\0')[:-1]], False)
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
        # No silent "no changes" on shallow history, bad refs, timeouts or missing Git.
        return ([], True)


def main() -> int:
    p = argparse.ArgumentParser(description='Classify MOTION.OS changes for local/cloud verification')
    p.add_argument('paths', nargs='*')
    p.add_argument('--force-full', action='store_true')
    p.add_argument('--check', choices=sorted(PATTERNS))
    p.add_argument('--github-output', type=Path)
    p.add_argument('--git-base')
    p.add_argument('--git-head', default='HEAD')
    p.add_argument('--nul', action='store_true', help='Read NUL-delimited paths from stdin')
    p.add_argument('--profiles', action='store_true', help='Print selected local profiles, one per line')
    args = p.parse_args()
    force = args.force_full
    if args.git_base is not None:
        if args.paths or args.nul:
            p.error('--git-base cannot be combined with positional paths or --nul')
        paths, uncertain = changed_paths(args.git_base, args.git_head)
        force = force or uncertain
    elif args.paths:
        paths = args.paths
    else:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        try:
            if len(raw) > MAX_INPUT_BYTES:
                raise ValueError('input_too_large')
            if args.nul:
                if raw and not raw.endswith(b'\0'):
                    raise ValueError('unterminated_nul_input')
                paths = [s.decode('utf-8') for s in raw.split(b'\0')[:-1]]
            else:
                paths = raw.decode('utf-8').splitlines()
        except (ValueError, UnicodeError):
            paths, force = [], True
    result = classify(paths, force_full=force)
    if args.github_output:
        with args.github_output.open('a', encoding='utf-8') as fh:
            for key, value in result.items():
                fh.write(f"{key}={'true' if value else 'false'}\n")
    if args.check:
        return 0 if result[args.check] else 1
    if args.profiles:
        for name in ('analysis', 'remotion', 'security'):
            if result[name]:
                print(name)
    else:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
