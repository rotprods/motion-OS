#!/usr/bin/env python3
"""Fail-closed npm audit gate bound to the exact Remotion manifest and lockfile."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_verify import _write_report

RUNTIME = ROOT / "runtime" / "remotion"
MAX_AUDIT_BYTES = 2_097_152
SEVERITIES = ("info", "low", "moderate", "high", "critical")
BLOCKING = {"high", "critical"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_json(raw: bytes) -> object:
    if not isinstance(raw, bytes) or len(raw) > MAX_AUDIT_BYTES:
        raise ValueError("audit_json_size_limit")

    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate_json_key")
            out[key] = value
        return out

    def invalid_constant(_):
        raise ValueError("nonfinite_json")

    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid_constant)
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > 32:
            raise ValueError("json_depth_limit")
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("nonfinite_json")
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
    return value


def assess_npm_audit(payload: object, *, tool_returncode: int) -> dict[str, Any]:
    if type(tool_returncode) is not int or tool_returncode < 0 or tool_returncode > 255:
        raise ValueError("invalid_tool_returncode")
    if not isinstance(payload, dict) or payload.get("auditReportVersion") != 2:
        raise ValueError("unsupported_audit_report")
    vulnerabilities = payload.get("vulnerabilities")
    metadata = payload.get("metadata")
    if not isinstance(vulnerabilities, dict) or len(vulnerabilities) > 10000 or not isinstance(metadata, dict):
        raise ValueError("invalid_audit_report")
    counts_raw = metadata.get("vulnerabilities")
    if not isinstance(counts_raw, dict):
        raise ValueError("invalid_vulnerability_counts")

    counts: dict[str, int] = {}
    for severity in SEVERITIES:
        value = counts_raw.get(severity)
        if type(value) is not int or value < 0:
            raise ValueError("invalid_vulnerability_counts")
        counts[severity] = value
    total = counts_raw.get("total")
    if type(total) is not int or total < 0 or total != sum(counts.values()):
        raise ValueError("invalid_vulnerability_total")

    observed = dict.fromkeys(SEVERITIES, 0)
    blocking_packages: list[str] = []
    for key, item in vulnerabilities.items():
        if not isinstance(key, str) or not key or len(key) > 512 or not isinstance(item, dict):
            raise ValueError("invalid_vulnerability_entry")
        name = item.get("name")
        severity = item.get("severity")
        if not isinstance(name, str) or not name or len(name) > 512 or severity not in SEVERITIES:
            raise ValueError("invalid_vulnerability_entry")
        observed[str(severity)] += 1
        if severity in BLOCKING:
            blocking_packages.append(name)
    if observed != counts:
        raise ValueError("vulnerability_count_mismatch")

    blockers = sorted(set(blocking_packages))
    if blockers:
        status = "FAIL"
        reason = "high_or_critical_vulnerabilities"
    elif tool_returncode != 0:
        status = "BLOCKED"
        reason = "npm_audit_nonzero_without_blocking_advisory"
    else:
        status = "PASS"
        reason = "no_high_or_critical_vulnerabilities"

    return {
        "schema": "motion-os.npm-audit/v1",
        "status": status,
        "reason": reason,
        "audit_report_version": 2,
        "tool_returncode": tool_returncode,
        "threshold": "high",
        "counts": {**counts, "total": total},
        "blocking_packages": blockers,
    }


def run_audit(*, runtime: Path = RUNTIME, timeout_s: float = 120.0) -> dict[str, Any]:
    if not isinstance(runtime, Path):
        raise ValueError("invalid_runtime")
    runtime = runtime.resolve()
    if runtime != RUNTIME.resolve():
        raise ValueError("unexpected_runtime")
    manifest = runtime / "package.json"
    lock = runtime / "package-lock.json"
    if not manifest.is_file() or not lock.is_file() or manifest.is_symlink() or lock.is_symlink():
        raise ValueError("node_manifest_or_lock_unavailable")
    if shutil.which("npm") is None:
        raise RuntimeError("npm_unavailable")
    if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)) or not math.isfinite(timeout_s) or not 0 < timeout_s <= 300:
        raise ValueError("invalid_timeout")

    before_manifest = _sha256(manifest)
    before_lock = _sha256(lock)
    try:
        completed = subprocess.run(
            ["npm", "audit", "--json", "--audit-level=high"],
            cwd=runtime,
            capture_output=True,
            timeout=float(timeout_s),
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("npm_audit_timeout") from exc
    except OSError as exc:
        raise RuntimeError("npm_audit_unavailable") from exc

    after_manifest = _sha256(manifest)
    after_lock = _sha256(lock)
    if before_manifest != after_manifest or before_lock != after_lock:
        raise RuntimeError("npm_audit_mutated_runtime_inputs")
    result = assess_npm_audit(_strict_json(completed.stdout), tool_returncode=completed.returncode)
    result.update(
        package_json_sha256=after_manifest,
        package_lock_sha256=after_lock,
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=Path(".artifacts/npm-audit.json"))
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)

    report: dict[str, Any] = {
        "schema": "motion-os.npm-audit/v1",
        "status": "RUNNING",
        "reason": "audit_in_progress",
        "threshold": "high",
        "blocking_packages": [],
    }
    code = 3
    try:
        _write_report(args.json_out, report)
        report = run_audit(timeout_s=args.timeout)
        code = 0 if report["status"] == "PASS" else 1 if report["status"] == "FAIL" else 2
    except Exception as exc:
        report = {
            "schema": "motion-os.npm-audit/v1",
            "status": "BLOCKED",
            "reason": "invalid_or_unavailable_audit_evidence",
            "threshold": "high",
            "blocking_packages": [],
            "error_type": type(exc).__name__,
        }
        code = 2
    try:
        _write_report(args.json_out, report)
    except (OSError, ValueError):
        return 3
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
