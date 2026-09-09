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
SCRIPT = ROOT / "scripts/python_environment.py"
SPEC = importlib.util.spec_from_file_location("python_environment", SCRIPT)
envmod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(envmod)


def _mock_platform(monkeypatch, version: str) -> None:
    monkeypatch.setattr(envmod.platform, "python_version", lambda: version)
    monkeypatch.setattr(envmod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(envmod.platform, "machine", lambda: "x86_64")


def test_manifest_defines_four_canonical_environments_and_four_locks():
    manifest = json.loads((ROOT / "ci/python_environments.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "motion-os.python-environments/v2"
    assert manifest["pip"] == "26.2.1"
    assert manifest["setuptools_build"] == "84.0.0"
    assert manifest["pip_audit"] == "2.10.1"
    assert set(manifest["environments"]) == {"quick311", "quick312", "analysis", "security"}
    assert set(manifest["locks"]) == {
        "pylock.py311-dev.toml",
        "pylock.py312-dev.toml",
        "pylock.py312-analysis.toml",
        "pylock.py312-audit.toml",
    }
    assert manifest["environments"]["security"] == {
        "python": "3.12.14",
        "project_lock": "pylock.py312-dev.toml",
        "tool_lock": "pylock.py312-audit.toml",
    }


@pytest.mark.parametrize(
    ("environment", "python_version"),
    [
        ("quick311", "3.11.16"),
        ("quick312", "3.12.14"),
        ("analysis", "3.12.14"),
        ("security", "3.12.14"),
    ],
)
def test_committed_environment_validates(monkeypatch, environment: str, python_version: str):
    _mock_platform(monkeypatch, python_version)
    result = envmod.validate_environment(environment)
    assert result["status"] == "PASS"
    assert result["environment"] == environment
    assert result["expected_inventory"]["motion-os"] == "0.9.1"
    assert result["expected_inventory"]["pip"] == "26.2.1"


def test_committed_locks_are_wheel_only_and_have_no_local_project():
    manifest = json.loads((ROOT / "ci/python_environments.json").read_text())
    for lock_name in manifest["locks"]:
        doc = tomllib.loads((ROOT / lock_name).read_text(encoding="utf-8"))
        names = []
        for package in doc["packages"]:
            names.append(package["name"])
            assert "directory" not in package
            assert "vcs" not in package
            assert "sdist" not in package
            assert "archive" not in package
            assert package["wheels"]
        assert "motion-os" not in names


def test_security_overlap_is_exact_identity(monkeypatch):
    _mock_platform(monkeypatch, "3.12.14")
    manifest = json.loads((ROOT / "ci/python_environments.json").read_text())
    dev = manifest["locks"]["pylock.py312-dev.toml"]
    audit = manifest["locks"]["pylock.py312-audit.toml"]
    _, dev_ids = envmod._load_lock(ROOT / "pylock.py312-dev.toml", dev["sha256"], dev["package_entries"])
    _, audit_ids = envmod._load_lock(ROOT / "pylock.py312-audit.toml", audit["sha256"], audit["package_entries"])
    overlap = set(dev_ids) & set(audit_ids)
    assert overlap == {"packaging", "pygments", "typing-extensions"}
    assert all(dev_ids[name] == audit_ids[name] for name in overlap)


def test_python_patch_drift_fails_closed(monkeypatch):
    _mock_platform(monkeypatch, "3.12.13")
    with pytest.raises(ValueError, match="python_version_mismatch"):
        envmod.validate_environment("quick312")


def test_untrusted_wheel_origin_is_rejected(tmp_path: Path):
    source = ROOT / "pylock.py312-dev.toml"
    raw = source.read_text(encoding="utf-8").replace("https://files.pythonhosted.org/", "https://evil.example/", 1)
    target = tmp_path / "pylock.py312-dev.toml"
    target.write_text(raw, encoding="utf-8")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    entries = len(tomllib.loads(raw)["packages"])
    with pytest.raises(ValueError, match="untrusted_wheel_origin"):
        envmod._load_lock(target, digest, entries)


def test_local_directory_entry_is_rejected_even_when_hash_matches(tmp_path: Path):
    source = ROOT / "pylock.py312-dev.toml"
    raw = source.read_text(encoding="utf-8") + '\n[[packages]]\nname = "motion-os"\n[packages.directory]\npath = "."\neditable = true\n'
    target = tmp_path / "pylock.py312-dev.toml"
    target.write_text(raw, encoding="utf-8")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    entries = len(tomllib.loads(raw)["packages"])
    with pytest.raises(ValueError, match="non_wheel_or_local_entry_rejected"):
        envmod._load_lock(target, digest, entries)


def test_duplicate_package_identity_is_rejected(tmp_path: Path):
    source = ROOT / "pylock.py312-dev.toml"
    doc = tomllib.loads(source.read_text(encoding="utf-8"))
    first = doc["packages"][0]
    wheel = first["wheels"][0]
    duplicate = (
        f'\n[[packages]]\nname = "{first["name"]}"\nversion = "{first["version"]}"\n'
        f'\n[[packages.wheels]]\nname = "{wheel["name"]}"\nurl = "{wheel["url"]}"\n'
        f'\n[packages.wheels.hashes]\nsha256 = "{wheel["hashes"]["sha256"]}"\n'
    )
    target = tmp_path / "dup.toml"
    target.write_text(source.read_text(encoding="utf-8") + duplicate, encoding="utf-8")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    entries = len(tomllib.loads(target.read_text())["packages"])
    with pytest.raises(ValueError, match="duplicate_package_name"):
        envmod._load_lock(target, digest, entries)


def test_cli_bootstraps_without_site_packages():
    completed = subprocess.run(
        [sys.executable, "-S", str(SCRIPT), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=15,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--environment" in completed.stdout
    assert "install" in completed.stdout
