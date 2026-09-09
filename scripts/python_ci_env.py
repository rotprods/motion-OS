#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ci/python_environments.json"
MAX_LOCK_BYTES = 1_048_576
MAX_PACKAGES = 512
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TRUSTED_HOST = "files.pythonhosted.org"


def canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(root: Path = ROOT) -> dict:
    value = json.loads((root / "ci/python_environments.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != "motion-os.python-environments/v2":
        raise ValueError("invalid_environment_manifest")
    return value


def load_lock(root: Path, name: str, contract: dict) -> tuple[dict[str, str], dict[str, tuple[str, tuple[tuple[str, str], ...]]]]:
    path = root / name
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"lock_missing_or_symlink:{name}")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_LOCK_BYTES:
        raise ValueError(f"lock_size_invalid:{name}")
    expected_sha = contract.get("sha256")
    entries = contract.get("package_entries")
    if not isinstance(expected_sha, str) or not HEX64.fullmatch(expected_sha) or type(entries) is not int or entries <= 0:
        raise ValueError(f"invalid_lock_contract:{name}")
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError(f"lock_hash_mismatch:{name}")
    try:
        doc = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"invalid_lock_toml:{name}") from exc
    if doc.get("lock-version") != "1.0" or doc.get("created-by") != "pip":
        raise ValueError(f"invalid_lock_header:{name}")
    packages = doc.get("packages")
    if not isinstance(packages, list) or len(packages) != entries or len(packages) > MAX_PACKAGES:
        raise ValueError(f"package_entry_count_mismatch:{name}")
    versions: dict[str, str] = {}
    identities: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {}
    for package in packages:
        if not isinstance(package, dict) or any(key in package for key in ("directory", "vcs", "sdist", "archive")):
            raise ValueError(f"non_wheel_or_local_entry:{name}")
        package_name = package.get("name")
        version = package.get("version")
        wheels = package.get("wheels")
        if not isinstance(package_name, str) or not NAME_RE.fullmatch(package_name) or not isinstance(version, str) or not version:
            raise ValueError(f"invalid_package:{name}")
        canonical = canonical_name(package_name)
        if canonical in versions:
            raise ValueError(f"duplicate_package:{canonical}")
        if not isinstance(wheels, list) or not wheels:
            raise ValueError(f"missing_wheels:{canonical}")
        wheel_identity: list[tuple[str, str]] = []
        for wheel in wheels:
            if not isinstance(wheel, dict):
                raise ValueError(f"invalid_wheel:{canonical}")
            wheel_name = wheel.get("name")
            url = wheel.get("url")
            hashes = wheel.get("hashes")
            parsed = urlparse(url) if isinstance(url, str) else None
            if not isinstance(wheel_name, str) or not wheel_name.endswith(".whl"):
                raise ValueError(f"invalid_wheel_name:{canonical}")
            if parsed is None or parsed.scheme != "https" or parsed.hostname != TRUSTED_HOST or parsed.username or parsed.password:
                raise ValueError(f"untrusted_wheel_origin:{canonical}")
            if not isinstance(hashes, dict) or set(hashes) != {"sha256"} or not isinstance(hashes.get("sha256"), str) or not HEX64.fullmatch(hashes["sha256"]):
                raise ValueError(f"invalid_wheel_hash:{canonical}")
            wheel_identity.append((wheel_name, hashes["sha256"]))
        versions[canonical] = version
        identities[canonical] = (version, tuple(sorted(wheel_identity)))
    return versions, identities


def contract(environment: str, *, root: Path = ROOT) -> dict:
    manifest = load_manifest(root)
    environments = manifest.get("environments")
    locks = manifest.get("locks")
    if not isinstance(environments, dict) or environment not in environments or not isinstance(environments[environment], dict) or not isinstance(locks, dict):
        raise ValueError("unknown_environment")
    spec = environments[environment]
    expected_python = spec.get("python")
    if platform.python_version() != expected_python:
        raise ValueError(f"python_version_mismatch:{platform.python_version()}:{expected_python}")
    if platform.system() != "Linux" or platform.machine().lower() not in {"x86_64", "amd64"}:
        raise ValueError("unsupported_platform")
    if manifest.get("pip") != "26.2.1" or manifest.get("setuptools_build") != "84.0.0":
        raise ValueError("toolchain_pin_mismatch")
    pyproject_path = root / "pyproject.toml"
    if sha256_file(pyproject_path) != manifest.get("pyproject_sha256"):
        raise ValueError("pyproject_hash_mismatch")
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = manifest.get("project")
    if pyproject.get("build-system", {}).get("requires") != ["setuptools==84.0.0"]:
        raise ValueError("build_backend_pin_mismatch")
    if not isinstance(project, dict) or pyproject.get("project", {}).get("name") != project.get("name") or pyproject.get("project", {}).get("version") != project.get("version"):
        raise ValueError("project_identity_mismatch")
    project_lock = spec.get("project_lock")
    tool_lock = spec.get("tool_lock")
    if not isinstance(project_lock, str) or project_lock not in locks:
        raise ValueError("project_lock_missing")
    project_versions, project_ids = load_lock(root, project_lock, locks[project_lock])
    tool_versions: dict[str, str] = {}
    tool_ids: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {}
    if tool_lock is not None:
        if not isinstance(tool_lock, str) or tool_lock not in locks:
            raise ValueError("tool_lock_missing")
        tool_versions, tool_ids = load_lock(root, tool_lock, locks[tool_lock])
        for name in set(project_ids) & set(tool_ids):
            if project_ids[name] != tool_ids[name]:
                raise ValueError(f"overlapping_lock_identity_mismatch:{name}")
    expected = dict(project_versions)
    expected.update(tool_versions)
    expected[canonical_name(project["name"])] = project["version"]
    expected["pip"] = manifest["pip"]
    return {
        "schema": "motion-os.python-ci-environment-contract/v2",
        "status": "PASS",
        "environment": environment,
        "python": expected_python,
        "pip": manifest["pip"],
        "pip_audit": manifest.get("pip_audit"),
        "project_lock": project_lock,
        "tool_lock": tool_lock,
        "expected_inventory": expected,
    }


def _safe_venv_path(root: Path, raw: Path) -> Path:
    target = (root / raw).resolve() if not raw.is_absolute() else raw.resolve()
    try:
        relative = target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("venv_outside_repo") from exc
    if len(relative.parts) < 1 or relative.parts[0] != ".venv-ci":
        raise ValueError("venv_must_live_under_dot_venv_ci")
    return target


def _run(command: list[str], *, cwd: Path, step: str, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, shell=False, timeout=timeout)
    if completed.returncode:
        tail = (completed.stderr + "\n" + completed.stdout)[-1200:]
        tail = re.sub(r"https?://\S+", "<url>", tail)
        tail = re.sub(r"(?i)(token|password|authorization|secret)\s*[:=]\s*\S+", r"\1=<redacted>", tail)
        print(json.dumps({"event": "PYTHON_CI_ENV_COMMAND_FAILED", "step": step, "returncode": completed.returncode, "tail": tail}, sort_keys=True), file=sys.stderr)
        raise RuntimeError(f"{step}_failed:{completed.returncode}")
    return completed


def _inventory(python: Path, *, root: Path) -> dict[str, str]:
    code = "import importlib.metadata as m,json; print(json.dumps([(d.metadata.get('Name'),d.version) for d in m.distributions() if d.metadata.get('Name')]))"
    completed = _run([str(python), "-c", code], cwd=root, step="inventory")
    pairs = json.loads(completed.stdout)
    versions: dict[str, set[str]] = {}
    for name, version in pairs:
        versions.setdefault(canonical_name(name), set()).add(version)
    result: dict[str, str] = {}
    for name, values in versions.items():
        if len(values) != 1:
            raise ValueError(f"installed_version_conflict:{name}")
        result[name] = next(iter(values))
    return result


def create(environment: str, *, root: Path = ROOT, venv: Path | None = None) -> dict:
    spec = contract(environment, root=root)
    venv_path = _safe_venv_path(root, venv or Path(".venv-ci") / environment)
    if venv_path.exists():
        raise ValueError("venv_already_exists")
    venv_path.parent.mkdir(parents=True, exist_ok=True)
    _run([sys.executable, "-m", "venv", str(venv_path)], cwd=root, step="create_venv")
    python = venv_path / "bin/python"
    _run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "pip==26.2.1"], cwd=root, step="pin_pip")
    _run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", spec["project_lock"]], cwd=root, step="install_project_lock")
    if spec["tool_lock"]:
        _run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", spec["tool_lock"]], cwd=root, step="install_tool_lock")
    _run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-build-isolation", "--no-deps", "-e", "."], cwd=root, step="install_local_project")
    _run([str(python), "-m", "pip", "check"], cwd=root, step="pip_check")
    actual = _inventory(python, root=root)
    expected = spec["expected_inventory"]
    extras = sorted(set(actual) - set(expected))
    missing = sorted(set(expected) - set(actual))
    mismatched = sorted(name for name in set(expected) & set(actual) if expected[name] != actual[name])
    if extras or missing or mismatched:
        raise ValueError(f"inventory_mismatch:extra={extras}:missing={missing}:mismatched={mismatched}")
    if environment == "security":
        if actual.get("pip-audit") != spec["pip_audit"]:
            raise ValueError("pip_audit_version_mismatch")
        _run([str(python), "-m", "pip_audit", "--version"], cwd=root, step="pip_audit_smoke")
    digest = hashlib.sha256(json.dumps(actual, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        **spec,
        "schema": "motion-os.python-ci-environment/v2",
        "status": "PASS",
        "venv": str(venv_path.relative_to(root.resolve())),
        "python_executable": str(python),
        "inventory_sha256": digest,
        "installed_inventory": actual,
    }


def write_report(path: Path | None, report: dict) -> None:
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
    fd, temp = tempfile.mkstemp(prefix=".python-ci-env-", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, target)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or validate a fresh frozen MOTION.OS Python CI environment")
    parser.add_argument("mode", choices=["validate", "create"])
    parser.add_argument("--environment", required=True)
    parser.add_argument("--venv", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    try:
        report = contract(args.environment) if args.mode == "validate" else create(args.environment, venv=args.venv)
        write_report(args.json_out, report)
        print(json.dumps(report, sort_keys=True, allow_nan=False))
        return 0
    except Exception as exc:
        report = {"schema": "motion-os.python-ci-environment-verification/v2", "status": "BLOCKED", "environment": args.environment, "reason": str(exc) if isinstance(exc, (ValueError, RuntimeError)) else type(exc).__name__}
        try:
            write_report(args.json_out, report)
        except Exception:
            pass
        print(json.dumps(report, sort_keys=True, allow_nan=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
