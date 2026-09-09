#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import tomllib
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1] if '__file__' in globals() else Path.cwd()
HEX64 = re.compile(r'^[0-9a-f]{64}$')
NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
MAX_LOCK_BYTES = 1_048_576
MAX_PACKAGES = 512
ALLOWED_WHEEL_HOST = 'files.pythonhosted.org'
BOOTSTRAP_DISTS = {'pip', 'setuptools', 'wheel'}


class LockCommandError(RuntimeError):
    def __init__(self, step: str, returncode: int):
        super().__init__(f'{step}_failed')
        self.step = step
        self.returncode = returncode


def _canonical_name(value: str) -> str:
    return re.sub(r'[-_.]+', '-', value).lower()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('toolchain_manifest_must_be_object')
    return value


def _load_lock(path: Path) -> tuple[dict, bytes]:
    if not path.is_file() or path.is_symlink():
        raise ValueError('lock_missing_or_symlink')
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_LOCK_BYTES:
        raise ValueError('lock_size_invalid')
    try:
        value = tomllib.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError('invalid_lock_toml') from exc
    if not isinstance(value, dict):
        raise ValueError('lock_must_be_object')
    return value, raw


def _pyproject_version(path: Path) -> str:
    doc = tomllib.loads(path.read_text(encoding='utf-8'))
    project = doc.get('project')
    if not isinstance(project, dict) or not isinstance(project.get('version'), str):
        raise ValueError('project_version_missing')
    build = doc.get('build-system')
    if not isinstance(build, dict) or build.get('requires') != ['setuptools==84.0.0']:
        raise ValueError('build_backend_not_exactly_pinned')
    return project['version']


def _expected_inventory(lock_doc: dict, project_version: str) -> tuple[dict[str, str], int]:
    packages = lock_doc.get('packages')
    if not isinstance(packages, list) or not packages or len(packages) > MAX_PACKAGES:
        raise ValueError('invalid_packages')
    out: dict[str, str] = {}
    seen: set[str] = set()
    local_count = 0
    for pkg in packages:
        if not isinstance(pkg, dict):
            raise ValueError('invalid_package_entry')
        name = pkg.get('name')
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            raise ValueError('invalid_package_name')
        cname = _canonical_name(name)
        if cname in seen:
            raise ValueError('duplicate_package_name')
        seen.add(cname)
        directory = pkg.get('directory')
        if directory is not None:
            if cname != 'motion-os' or directory != {'path': '.', 'editable': True}:
                raise ValueError('invalid_local_project_entry')
            if set(pkg) - {'name', 'directory'}:
                raise ValueError('unexpected_local_project_fields')
            out[cname] = project_version
            local_count += 1
            continue
        version = pkg.get('version')
        wheels = pkg.get('wheels')
        if not isinstance(version, str) or not version or not isinstance(wheels, list) or not wheels:
            raise ValueError('invalid_locked_distribution')
        if 'sdist' in pkg or 'archive' in pkg or 'vcs' in pkg:
            raise ValueError('non_wheel_distribution_rejected')
        for wheel in wheels:
            if not isinstance(wheel, dict):
                raise ValueError('invalid_wheel')
            wname, url, hashes = wheel.get('name'), wheel.get('url'), wheel.get('hashes')
            if not isinstance(wname, str) or not wname.endswith('.whl'):
                raise ValueError('invalid_wheel_name')
            parsed = urlparse(url) if isinstance(url, str) else None
            if parsed is None or parsed.scheme != 'https' or parsed.hostname != ALLOWED_WHEEL_HOST or parsed.username or parsed.password:
                raise ValueError('untrusted_wheel_origin')
            if not isinstance(hashes, dict) or set(hashes) != {'sha256'} or not isinstance(hashes['sha256'], str) or not HEX64.fullmatch(hashes['sha256']):
                raise ValueError('invalid_wheel_hash')
        if cname not in BOOTSTRAP_DISTS:
            out[cname] = version
    if local_count != 1:
        raise ValueError('local_project_entry_count_invalid')
    return out, len(packages)


def validate(lock_name: str, *, root: Path = ROOT) -> dict:
    manifest = _load_json(root / 'ci/python_toolchain.json')
    if manifest.get('schema') != 'motion-os.python-toolchain/v1':
        raise ValueError('invalid_toolchain_schema')
    locks = manifest.get('locks')
    if not isinstance(locks, dict) or lock_name not in locks or not isinstance(locks[lock_name], dict):
        raise ValueError('unknown_lock')
    contract = locks[lock_name]
    expected_python = contract.get('python')
    expected_sha = contract.get('sha256')
    expected_packages = contract.get('package_entries')
    if not isinstance(expected_python, str) or not isinstance(expected_sha, str) or not HEX64.fullmatch(expected_sha):
        raise ValueError('invalid_lock_contract')
    if type(expected_packages) is not int or expected_packages <= 0:
        raise ValueError('invalid_lock_contract')
    current_python = platform.python_version()
    if current_python != expected_python:
        raise ValueError(f'python_version_mismatch:{current_python}:{expected_python}')
    if platform.system() != 'Linux' or platform.machine().lower() not in {'x86_64', 'amd64'}:
        raise ValueError('unsupported_lock_platform')
    if manifest.get('pip') != '26.2.1' or manifest.get('setuptools_build') != '84.0.0':
        raise ValueError('toolchain_pin_mismatch')
    pyproject = root / 'pyproject.toml'
    if _sha256(pyproject) != manifest.get('pyproject_sha256'):
        raise ValueError('pyproject_hash_mismatch')
    project_version = _pyproject_version(pyproject)
    lock_path = root / lock_name
    lock_doc, raw = _load_lock(lock_path)
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('lock_hash_mismatch')
    if lock_doc.get('lock-version') != '1.0' or lock_doc.get('created-by') != 'pip':
        raise ValueError('lock_header_invalid')
    inventory, raw_package_count = _expected_inventory(lock_doc, project_version)
    if raw_package_count != expected_packages:
        raise ValueError('package_entry_count_mismatch')
    return {
        'schema': 'motion-os.python-lock-validation/v1',
        'status': 'PASS',
        'lock': lock_name,
        'lock_sha256': expected_sha,
        'pyproject_sha256': manifest['pyproject_sha256'],
        'python': current_python,
        'pip': manifest['pip'],
        'setuptools_build': manifest['setuptools_build'],
        'packages': inventory,
    }


def _sanitized_tail(stdout: str, stderr: str, *, limit: int = 1600) -> str:
    combined = (stderr + '\n' + stdout)[-limit:]
    combined = re.sub(r'https?://\S+', '<url>', combined)
    combined = re.sub(r'(?i)(token|password|authorization|secret)\s*[:=]\s*\S+', r'\1=<redacted>', combined)
    return ''.join(ch if ch in '\n\t' or ord(ch) >= 32 else '?' for ch in combined).strip()


def _run(cmd: list[str], *, cwd: Path, step: str, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout, shell=False)
    if cp.returncode:
        tail = _sanitized_tail(cp.stdout, cp.stderr)
        print(json.dumps({
            'event': 'LOCK_COMMAND_FAILED',
            'step': step,
            'returncode': cp.returncode,
            'sanitized_tail': tail,
        }, sort_keys=True), file=sys.stderr)
        raise LockCommandError(step, cp.returncode)
    return cp


def _inventory(python: Path, *, cwd: Path = ROOT, step: str = 'inventory') -> dict[str, str]:
    code = (
        "import importlib.metadata as m,json; "
        "print(json.dumps(sorted((d.metadata['Name'],d.version) for d in m.distributions() if d.metadata.get('Name'))))"
    )
    cp = _run([str(python), '-c', code], cwd=cwd, step=step)
    pairs = json.loads(cp.stdout)
    out: dict[str, str] = {}
    seen: set[str] = set()
    for name, version in pairs:
        cname = _canonical_name(name)
        if cname in seen:
            raise ValueError('duplicate_installed_distribution')
        seen.add(cname)
        if cname in BOOTSTRAP_DISTS:
            continue
        out[cname] = version
    return out


def reproduce(lock_name: str, *, root: Path = ROOT) -> dict:
    validation = validate(lock_name, root=root)
    expected = validation['packages']
    before_lock = _sha256(root / lock_name)
    before_project = _sha256(root / 'pyproject.toml')
    inventories = []
    with tempfile.TemporaryDirectory(prefix='motion-python-lock-') as tmp:
        for idx in (1, 2):
            venv = Path(tmp) / f'env{idx}'
            _run([sys.executable, '-m', 'venv', str(venv)], cwd=root, step=f'create_venv_{idx}')
            py = venv / 'bin/python'
            _run(
                [str(py), '-m', 'pip', 'install', '--disable-pip-version-check', 'pip==26.2.1'],
                cwd=root,
                step=f'pin_pip_{idx}',
            )
            _run(
                [str(py), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', lock_name],
                cwd=root,
                step=f'install_lock_{idx}',
            )
            actual = _inventory(py, cwd=root, step=f'inventory_{idx}')
            if actual != expected:
                raise ValueError('installed_inventory_mismatch')
            inventories.append(actual)
    if inventories[0] != inventories[1]:
        raise ValueError('clean_install_inventory_drift')
    if _sha256(root / lock_name) != before_lock or _sha256(root / 'pyproject.toml') != before_project:
        raise ValueError('source_or_lock_mutated')
    digest = hashlib.sha256(json.dumps(inventories[0], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {
        **validation,
        'schema': 'motion-os.python-lock-reproducibility/v1',
        'status': 'PASS',
        'clean_installs': 2,
        'inventory_sha256': digest,
        'installed_packages': inventories[0],
    }


def _write(path: Path | None, value: dict) -> None:
    if path is None:
        return
    target = path if path.is_absolute() else ROOT / path
    root = ROOT.resolve()
    target = target.resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError('output_outside_repo') from exc
    if target.suffix != '.json':
        raise ValueError('output_must_be_json')
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.python-lock-', dir=target.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, target)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description='Validate or physically reproduce a committed MOTION.OS Python lock')
    p.add_argument('mode', choices=['validate', 'reproduce'])
    p.add_argument('--lock', required=True)
    p.add_argument('--json-out', type=Path)
    args = p.parse_args(argv)
    try:
        result = validate(args.lock) if args.mode == 'validate' else reproduce(args.lock)
        _write(args.json_out, result)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    except Exception as exc:
        result = {
            'schema': 'motion-os.python-lock-verification/v1',
            'status': 'BLOCKED',
            'lock': args.lock,
            'reason': str(exc) if isinstance(exc, (ValueError, LockCommandError)) else type(exc).__name__,
        }
        if isinstance(exc, LockCommandError):
            result['command_step'] = exc.step
            result['returncode'] = exc.returncode
        try:
            _write(args.json_out, result)
        except Exception:
            pass
        print(json.dumps(result, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())