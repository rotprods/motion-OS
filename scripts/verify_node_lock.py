#!/usr/bin/env python3
"""Verify the approved npm lock by installation, never by re-resolving it.

Lifecycle scripts run only in the isolated runtime job with read-only permissions.
This receipt proves frozen installation, not dependency vulnerability absence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]


def _strict_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_json_key')
        result[key] = value
    return result


def verify_runtime(runtime: Path, *, runner: Callable = subprocess.run) -> dict:
    report = {'schema': 'motion-os.node-lock-verification/v1', 'status': 'FAIL',
              'installs': [], 'errors': [], 'authority': 'FROZEN_INSTALL_ONLY'}

    def fail(code: str) -> dict:
        report['errors'].append(code)
        return report

    paths = {name: runtime / name for name in ('package.json', 'package-lock.json')}
    try:
        if any(p.is_symlink() or not p.is_file() for p in paths.values()):
            return fail('manifest_or_lock_missing_or_symlink')
        approved = {name: p.read_bytes() for name, p in paths.items()}
        if any(len(b) > 10_000_000 for b in approved.values()):
            return fail('manifest_or_lock_oversized')
        parsed = {name: json.loads(b, object_pairs_hook=_strict_object) for name, b in approved.items()}
        package, lock = parsed['package.json'], parsed['package-lock.json']
        if not isinstance(package, dict) or not isinstance(lock, dict) or lock.get('lockfileVersion') != 3:
            return fail('manifest_or_lock_invalid')
        packages = lock.get('packages')
        if not isinstance(packages, dict) or not isinstance(packages.get(''), dict):
            return fail('lock_root_missing')
        for field in ('dependencies', 'devDependencies', 'optionalDependencies'):
            if package.get(field, {}) != packages[''].get(field, {}):
                return fail('package_lock_dependency_mismatch')
    except (OSError, ValueError, TypeError, UnicodeError):
        return fail('manifest_or_lock_invalid')

    report['approved_sha256'] = {n: hashlib.sha256(b).hexdigest() for n, b in approved.items()}

    def command(argv: list[str], timeout: int = 240):
        return runner(argv, cwd=runtime, text=True, capture_output=True,
                      timeout=timeout, shell=False)

    try:
        report['toolchain'] = {}
        for tool in ('node', 'npm'):
            cp = command([tool, '--version'], timeout=15)
            version = cp.stdout.strip()
            if cp.returncode or not re.fullmatch(r'v?\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
                return fail('toolchain_unavailable_or_invalid')
            report['toolchain'][tool] = version
        for number in (1, 2):
            # npm ci removes node_modules itself; do not rm or regenerate the lock.
            cp = command(['npm', 'ci', '--no-audit', '--no-fund'])
            stable = all(p.read_bytes() == approved[name] for name, p in paths.items())
            report['installs'].append({'number': number, 'exit_code': cp.returncode,
                                       'lock_and_manifest_unchanged': stable})
            if cp.returncode:
                return fail('frozen_install_failed')
            if not stable:
                return fail('approved_inputs_changed')
        cp = command(['npm', 'ls', '--all', '--json'])
        if cp.returncode:
            return fail('installed_dependency_tree_invalid')
        tree = json.loads(cp.stdout, object_pairs_hook=_strict_object)
        if not isinstance(tree, dict):
            return fail('installed_dependency_tree_invalid')
        report['installed_tree_sha256'] = hashlib.sha256(cp.stdout.encode()).hexdigest()
    except (OSError, ValueError, TypeError, UnicodeError, subprocess.TimeoutExpired):
        return fail('runtime_execution_failed')
    report['status'] = 'PASS'
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json-out', type=Path, required=True)
    args = parser.parse_args()
    target = (ROOT / args.json_out).resolve()
    if not target.is_relative_to(ROOT):
        parser.error('evidence output must remain inside the repository')
    report = verify_runtime(ROOT / 'runtime/remotion')
    text = json.dumps(report, indent=2, sort_keys=True) + '\n'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')
    print(text, end='')
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
