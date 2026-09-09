#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
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

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "ci/python_environments.json"
MAX_LOCK_BYTES = 1_048_576
MAX_PACKAGES = 512
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ALLOWED_WHEEL_HOST = "files.pythonhosted.org"


def _canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest(root: Path = ROOT) -> dict:
    value = json.loads((root / "ci/python_environments.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != "motion-os.python-environments/v2":
        raise ValueError("invalid_environment_manifest")
    return value


def _load_lock(path: Path, expected_sha: str, expected_entries: int) -> tuple[dict[str, str], dict[str, tuple[str, tuple[tuple[str, str], ...]]]]:
    if not path.is_file() or path.is_symlink():
        raise ValueError("lock_missing_or_symlink")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_LOCK_BYTES:
        raise ValueError("lock_size_invalid")
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("lock_hash_mismatch")
    try:
        doc = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError("invalid_lock_toml") from exc
    if doc.get("lock-version") != "1.0" or doc.get("created-by") != "pip":
        raise ValueError("invalid_lock_header")
    packages = doc.get("packages")
    if not isinstance(packages, list) or len(packages) != expected_entries or len(packages) > MAX_PACKAGES:
        raise ValueError("package_entry_count_mismatch")
    versions: dict[str, str] = {}
    identities: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {}
    for package in packages:
        if not isinstance(package, dict) or "directory" in package or "vcs" in package or "sdist" in package or "archive" in package:
            raise ValueError("non_wheel_or_local_entry_rejected")
        name = package.get("name")
        version = package.get("version")
        wheels = package.get("wheels")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name) or not isinstance(version, str) or not version:
            raise ValueError("invalid_package_entry")
        canonical = _canonical_name(name)
        if canonical in versions:
            raise ValueError("duplicate_package_name")
        if not isinstance(wheels, list) or not wheels:
            raise ValueError("wheel_list_missing")
        wheel_identity: list[tuple[str, str]] = []
        for wheel in wheels:
            if not isinstance(wheel, dict):
                raise ValueError("invalid_wheel")
            wheel_name = wheel.get("name")
            url = wheel.get("url")
            hashes = wheel.get("hashes")
            if not isinstance(wheel_name, str) or not wheel_name.endswith(".whl"):
                raise ValueError("invalid_wheel_name")
            parsed = urlparse(url) if isinstance(url, str) else None
            if parsed is None or parsed.scheme != "https" or parsed.hostname != ALLOWED_WHEEL_HOST or parsed.username or parsed.password:
                raise ValueError("untrusted_wheel_origin")
            if not isinstance(hashes, dict) or set(hashes) != {"sha256"}:
                raise ValueError("invalid_wheel_hash")
            digest = hashes.get("sha256")
            if not isinstance(digest, str) or not HEX64.fullmatch(digest):
                raise ValueError("invalid_wheel_hash")
            wheel_identity.append((wheel_name, digest))
        versions[canonical] = version
        identities[canonical] = (version, tuple(sorted(wheel_identity)))
    return versions, identities


def validate_environment(name: str, *, root: Path = ROOT) -> dict:
    manifest = _load_manifest(root)
    environments = manifest.get("environments")
    locks = manifest.get("locks")
    if not isinstance(environments, dict) or name not in environments or not isinstance(environments[name], dict):
        raise ValueError("unknown_environment")
    if not isinstance(locks, dict):
        raise ValueError("invalid_lock_registry")
    environment = environments[name]
    expected_python = environment.get("python")
    if platform.python_version() != expected_python:
        raise ValueError(f"python_version_mismatch:{platform.python_version()}:{expected_python}")
    if platform.system() != manifest.get("platform", {}).get("system") or platform.machine().lower() not in {"x86_64", "amd64"}:
        raise ValueError("platform_mismatch")
    if manifest.get("pip") != "26.2.1" or manifest.get("setuptools_build") != "84.0.0":
        raise ValueError("toolchain_pin_mismatch")
    pyproject = root / "pyproject.toml"
    if _sha256(pyproject) != manifest.get("pyproject_sha256"):
        raise ValueError("pyproject_hash_mismatch")
    pyproject_doc = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    if pyproject_doc.get("build-system", {}).get("requires") != ["setuptools==84.0.0"]:
        raise ValueError("build_backend_pin_mismatch")
    project = manifest.get("project")
    if not isinstance(project, dict) or pyproject_doc.get("project", {}).get("name") != project.get("name") or pyproject_doc.get("project", {}).get("version") != project.get("version"):
        raise ValueError("project_identity_mismatch")

    project_lock = environment.get("project_lock")
    tool_lock = environment.get("tool_lock")
    if not isinstance(project_lock, str) or project_lock not in locks:
        raise ValueError("project_lock_missing")
    project_contract = locks[project_lock]
    project_versions, project_ids = _load_lock(root / project_lock, project_contract["sha256"], project_contract["package_entries"])

    tool_versions: dict[str, str] = {}
    tool_ids: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {}
    if tool_lock is not None:
        if not isinstance(tool_lock, str) or tool_lock not in locks:
            raise ValueError("tool_lock_missing")
        tool_contract = locks[tool_lock]
        tool_versions, tool_ids = _load_lock(root / tool_lock, tool_contract["sha256"], tool_contract["package_entries"])
        for package in set(project_ids) & set(tool_ids):
            if project_ids[package] != tool_ids[package]:
                raise ValueError(f"overlapping_lock_identity_mismatch:{package}")

    expected = dict(project_versions)
    expected.update(tool_versions)
    expected[_canonical_name(project["name"])] = project["version"]
    expected["pip"] = manifest["pip"]
    return {
        "schema": "motion-os.python-environment-validation/v2",
        "status": "PASS",
        "environment": name,
        "python": expected_python,
        "pip": manifest["pip"],
        "project_lock": project_lock,
        "tool_lock": tool_lock,
        "expected_inventory": expected,
    }


def _run(command: list[str], *, step: str, cwd: Path = ROOT, timeout: int = 300) -> None:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, shell=False, timeout=timeout)
    if completed.returncode:
        tail = (completed.stderr + "\n" + completed.stdout)[-1200:]
        tail = re.sub(r"https?://\S+", "<url>", tail)
        tail = re.sub(r"(?i)(token|password|authorization|secret)\s*[:=]\s*\S+", r"\1=<redacted>", tail)
        print(json.dumps({"event": "PYTHON_ENV_COMMAND_FAILED", "step": step, "returncode": completed.returncode, "tail": tail}, sort_keys=True), file=sys.stderr)
        raise RuntimeError(f"{step}_failed:{completed.returncode}")


def _installed_inventory() -> dict[str, str]:
    found: dict[str, set[str]] = {}
    for dist in metadata.distributions():
        name = dist.metadata.get("Name")
        if not name:
            continue
        found.setdefault(_canonical_name(name), set()).add(dist.version)
    inventory: dict[str, str] = {}
    for name, versions in found.items():
        if len(versions) != 1:
            raise ValueError(f"installed_version_conflict:{name}")
        inventory[name] = next(iter(versions))
    return inventory


def install_environment(name: str, *, root: Path = ROOT) -> dict:
    validation = validate_environment(name, root=root)
    manifest = _load_manifest(root)
    _run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "pip==26.2.1"], step="pin_pip", cwd=root)
    _run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-r", validation["project_lock"]], step="install_project_lock", cwd=root)
    if validation["tool_lock"]:
        _run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-r", validation["tool_lock"]], step="install_tool_lock", cwd=root)
    _run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-build-isolation", "--no-deps", "-e", "."], step="install_local_project", cwd=root)
    _run([sys.executable, "-m", "pip", "check"], step="pip_check", cwd=root)
    actual = _installed_inventory()
    expected = validation["expected_inventory"]
    extras = sorted(set(actual) - set(expected))
    missing = sorted(set(expected) - set(actual))
    mismatched = sorted(name for name in set(expected) & set(actual) if expected[name] != actual[name])
    if extras or missing or mismatched:
        raise ValueError(f"inventory_mismatch:extra={extras}:missing={missing}:mismatched={mismatched}")
    if name == "security":
        if actual.get("pip-audit") != manifest.get("pip_audit"):
            raise ValueError("pip_audit_version_mismatch")
        _run([sys.executable, "-m", "pip_audit", "--version"], step="pip_audit_smoke", cwd=root)
    inventory_hash = hashlib.sha256(json.dumps(actual, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        **validation,
        "schema": "motion-os.python-environment-install/v2",
        "status": "PASS",
        "inventory_sha256": inventory_hash,
        "installed_inventory": actual,
    }


def _write_report(path: Path | None, value: dict) -> None:
    if path is None:
        return
    target = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("report_outside_repo") from exc
    if target.suffix != ".json":
        raise ValueError("report_must_be_json")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".python-env-", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate or install an exact MOTION.OS Python CI environment")
    parser.add_argument("mode", choices=["validate", "install"])
    parser.add_argument("--environment", required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate_environment(args.environment) if args.mode == "validate" else install_environment(args.environment)
        _write_report(args.json_out, result)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    except Exception as exc:
        result = {"schema": "motion-os.python-environment-verification/v2", "status": "BLOCKED", "environment": args.environment, "reason": str(exc) if isinstance(exc, (ValueError, RuntimeError)) else type(exc).__name__}
        try:
            _write_report(args.json_out, result)
        except Exception:
            pass
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
