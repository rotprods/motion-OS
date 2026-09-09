from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/python_lock_gate.py'
SPEC = importlib.util.spec_from_file_location('python_lock_gate', SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gate)


def _copy_fixture(tmp_path: Path, lock_name: str = 'pylock.py312-dev.toml') -> Path:
    root = tmp_path / 'repo'
    (root / 'ci').mkdir(parents=True)
    shutil.copy2(ROOT / 'pyproject.toml', root / 'pyproject.toml')
    shutil.copy2(ROOT / lock_name, root / lock_name)
    manifest = json.loads((ROOT / 'ci/python_toolchain.json').read_text(encoding='utf-8'))
    manifest['locks'] = {lock_name: manifest['locks'][lock_name]}
    (root / 'ci/python_toolchain.json').write_text(json.dumps(manifest), encoding='utf-8')
    return root


def _mock_environment(monkeypatch, version: str = '3.12.14') -> None:
    monkeypatch.setattr(gate.platform, 'python_version', lambda: version)
    monkeypatch.setattr(gate.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(gate.platform, 'machine', lambda: 'x86_64')


def test_committed_toolchain_manifest_covers_all_four_locks():
    manifest = json.loads((ROOT / 'ci/python_toolchain.json').read_text(encoding='utf-8'))
    assert manifest['schema'] == 'motion-os.python-toolchain/v1'
    assert manifest['pip'] == '26.2.1'
    assert manifest['setuptools_build'] == '84.0.0'
    assert manifest['pip_audit'] == '2.10.1'
    assert set(manifest['locks']) == {
        'pylock.py311-dev.toml', 'pylock.py312-dev.toml',
        'pylock.py312-analysis.toml', 'pylock.py312-security.toml',
    }


@pytest.mark.parametrize(
    ('lock_name', 'python_version', 'entries'),
    [
        ('pylock.py311-dev.toml', '3.11.16', 13),
        ('pylock.py312-dev.toml', '3.12.14', 13),
        ('pylock.py312-analysis.toml', '3.12.14', 16),
        ('pylock.py312-security.toml', '3.12.14', 39),
    ],
)
def test_committed_locks_validate(monkeypatch, lock_name: str, python_version: str, entries: int):
    _mock_environment(monkeypatch, python_version)
    result = gate.validate(lock_name)
    assert result['status'] == 'PASS'
    manifest = json.loads((ROOT / 'ci/python_toolchain.json').read_text())
    assert manifest['locks'][lock_name]['package_entries'] == entries


def test_security_lock_contains_exact_pip_audit_and_pip(monkeypatch):
    _mock_environment(monkeypatch)
    result = gate.validate('pylock.py312-security.toml')
    assert result['packages']['pip-audit'] == '2.10.1'
    doc = tomllib.loads((ROOT / 'pylock.py312-security.toml').read_text())
    versions = {p['name']: p.get('version') for p in doc['packages']}
    assert versions['pip'] == '26.2.1'


def test_python_patch_mismatch_fails_closed(monkeypatch, tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _mock_environment(monkeypatch, '3.12.13')
    with pytest.raises(ValueError, match='python_version_mismatch'):
        gate.validate('pylock.py312-dev.toml', root=root)


def test_pyproject_tamper_fails_before_install(monkeypatch, tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _mock_environment(monkeypatch)
    with (root / 'pyproject.toml').open('a', encoding='utf-8') as f:
        f.write('\n# drift\n')
    with pytest.raises(ValueError, match='pyproject_hash_mismatch'):
        gate.validate('pylock.py312-dev.toml', root=root)


def test_lock_tamper_fails_hash_binding(monkeypatch, tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _mock_environment(monkeypatch)
    with (root / 'pylock.py312-dev.toml').open('a', encoding='utf-8') as f:
        f.write('\n# drift\n')
    with pytest.raises(ValueError, match='lock_hash_mismatch'):
        gate.validate('pylock.py312-dev.toml', root=root)


def test_untrusted_wheel_origin_is_rejected_even_when_manifest_rehashed(monkeypatch, tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _mock_environment(monkeypatch)
    lock = root / 'pylock.py312-dev.toml'
    text = lock.read_text().replace('https://files.pythonhosted.org/', 'https://evil.example/', 1)
    lock.write_text(text)
    manifest_path = root / 'ci/python_toolchain.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['locks']['pylock.py312-dev.toml']['sha256'] = hashlib.sha256(lock.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='untrusted_wheel_origin'):
        gate.validate('pylock.py312-dev.toml', root=root)


def test_local_project_must_remain_editable_dot(monkeypatch, tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _mock_environment(monkeypatch)
    lock = root / 'pylock.py312-dev.toml'
    text = lock.read_text().replace('path = "."\neditable = true', 'path = "../outside"\neditable = true')
    lock.write_text(text)
    manifest_path = root / 'ci/python_toolchain.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['locks']['pylock.py312-dev.toml']['sha256'] = hashlib.sha256(lock.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='invalid_local_project_entry'):
        gate.validate('pylock.py312-dev.toml', root=root)


def test_build_backend_pin_is_mandatory(monkeypatch, tmp_path: Path):
    root = _copy_fixture(tmp_path)
    _mock_environment(monkeypatch)
    pyproject = root / 'pyproject.toml'
    pyproject.write_text(pyproject.read_text().replace('setuptools==84.0.0', 'setuptools>=68'))
    manifest_path = root / 'ci/python_toolchain.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['pyproject_sha256'] = hashlib.sha256(pyproject.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='build_backend_not_exactly_pinned'):
        gate.validate('pylock.py312-dev.toml', root=root)


def test_unsupported_platform_fails_closed(monkeypatch):
    monkeypatch.setattr(gate.platform, 'python_version', lambda: '3.12.14')
    monkeypatch.setattr(gate.platform, 'system', lambda: 'Darwin')
    monkeypatch.setattr(gate.platform, 'machine', lambda: 'arm64')
    with pytest.raises(ValueError, match='unsupported_lock_platform'):
        gate.validate('pylock.py312-dev.toml')


def test_cli_bootstraps_without_site_packages():
    completed = subprocess.run(
        [sys.executable, '-S', str(SCRIPT), '--help'], cwd=ROOT,
        text=True, capture_output=True, timeout=15,
    )
    assert completed.returncode == 0, completed.stderr
    assert 'reproduce' in completed.stdout
    assert '--lock' in completed.stdout
