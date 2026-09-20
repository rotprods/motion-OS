from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/python_ci_env.py"
SPEC = importlib.util.spec_from_file_location("python_ci_env", SCRIPT)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def _platform(monkeypatch, version: str) -> None:
    monkeypatch.setattr(mod.platform, "python_version", lambda: version)
    monkeypatch.setattr(mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(mod.platform, "machine", lambda: "x86_64")


@pytest.mark.parametrize(
    ("environment", "python_version"),
    [("quick311", "3.11.16"), ("quick312", "3.12.14"), ("analysis", "3.12.14"), ("security", "3.12.14")],
)
def test_canonical_contract_validates(monkeypatch, environment: str, python_version: str):
    _platform(monkeypatch, python_version)
    result = mod.contract(environment)
    assert result["status"] == "PASS"
    assert result["expected_inventory"]["motion-os"] == "0.9.1"
    assert result["expected_inventory"]["pip"] == "26.2.1"


def test_security_uses_separate_project_and_tool_locks(monkeypatch):
    _platform(monkeypatch, "3.12.14")
    result = mod.contract("security")
    assert result["project_lock"] == "pylock.py312-dev.toml"
    assert result["tool_lock"] == "pylock.py312-audit.toml"
    assert result["expected_inventory"]["pip-audit"] == "2.10.1"


def test_all_committed_locks_are_hash_bound_wheel_only():
    manifest = json.loads((ROOT / "ci/python_environments.json").read_text())
    for name, contract in manifest["locks"].items():
        versions, identities = mod.load_lock(ROOT, name, contract)
        assert versions
        assert set(versions) == set(identities)
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == contract["sha256"]
        doc = tomllib.loads((ROOT / name).read_text())
        assert all("directory" not in package for package in doc["packages"])


def test_security_overlap_is_byte_identity_equivalent(monkeypatch):
    _platform(monkeypatch, "3.12.14")
    manifest = mod.load_manifest()
    dev_versions, dev_ids = mod.load_lock(ROOT, "pylock.py312-dev.toml", manifest["locks"]["pylock.py312-dev.toml"])
    audit_versions, audit_ids = mod.load_lock(ROOT, "pylock.py312-audit.toml", manifest["locks"]["pylock.py312-audit.toml"])
    overlap = set(dev_ids) & set(audit_ids)
    assert overlap == {"packaging", "pygments", "typing-extensions"}
    assert all(dev_ids[name] == audit_ids[name] for name in overlap)


def test_venv_must_stay_under_repo_dot_venv_ci(tmp_path: Path):
    with pytest.raises(ValueError, match="venv_outside_repo|venv_must_live"):
        mod._safe_venv_path(ROOT, tmp_path / "foreign")


def test_existing_venv_fails_closed(monkeypatch, tmp_path: Path):
    _platform(monkeypatch, "3.12.14")
    existing = ROOT / ".venv-ci" / "already-present-test"
    existing.mkdir(parents=True, exist_ok=True)
    try:
        with pytest.raises(ValueError, match="venv_already_exists"):
            mod.create("quick312", venv=Path(".venv-ci/already-present-test"))
    finally:
        existing.rmdir()


def test_python_patch_drift_is_rejected(monkeypatch):
    _platform(monkeypatch, "3.12.13")
    with pytest.raises(ValueError, match="python_version_mismatch"):
        mod.contract("quick312")


def test_cli_bootstraps_without_site_packages():
    cp = subprocess.run([sys.executable, "-S", str(SCRIPT), "--help"], cwd=ROOT, text=True, capture_output=True, timeout=15)
    assert cp.returncode == 0, cp.stderr
    assert "--environment" in cp.stdout
    assert "create" in cp.stdout
