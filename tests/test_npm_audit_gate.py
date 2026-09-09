from __future__ import annotations

from copy import deepcopy
import subprocess
from pathlib import Path
import sys

import pytest

import scripts.npm_audit_gate as gate


ROOT = Path(__file__).resolve().parents[1]


def _payload(*, low=0, moderate=0, high=0, critical=0, info=0) -> dict:
    entries = {}
    for severity, count in (("info", info), ("low", low), ("moderate", moderate), ("high", high), ("critical", critical)):
        for index in range(count):
            name = f"pkg-{severity}-{index}"
            entries[name] = {"name": name, "severity": severity, "isDirect": False, "via": [], "effects": [], "range": "*", "nodes": []}
    return {
        "auditReportVersion": 2,
        "vulnerabilities": entries,
        "metadata": {
            "vulnerabilities": {
                "info": info,
                "low": low,
                "moderate": moderate,
                "high": high,
                "critical": critical,
                "total": info + low + moderate + high + critical,
            }
        },
    }


def test_clean_audit_passes():
    result = gate.assess_npm_audit(_payload(), tool_returncode=0)
    assert result["status"] == "PASS"
    assert result["blocking_packages"] == []


def test_low_and_moderate_are_visible_but_not_initially_blocking():
    result = gate.assess_npm_audit(_payload(low=2, moderate=1), tool_returncode=0)
    assert result["status"] == "PASS"
    assert result["counts"]["low"] == 2
    assert result["counts"]["moderate"] == 1
    assert result["blocking_packages"] == []


def test_high_vulnerability_blocks_even_if_tool_exit_is_zero():
    result = gate.assess_npm_audit(_payload(high=1), tool_returncode=0)
    assert result["status"] == "FAIL"
    assert result["blocking_packages"] == ["pkg-high-0"]


def test_critical_vulnerability_blocks():
    result = gate.assess_npm_audit(_payload(critical=1), tool_returncode=1)
    assert result["status"] == "FAIL"
    assert result["blocking_packages"] == ["pkg-critical-0"]


def test_nonzero_tool_without_blocking_advisory_is_blocked_not_pass():
    result = gate.assess_npm_audit(_payload(moderate=1), tool_returncode=1)
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "npm_audit_nonzero_without_blocking_advisory"


def test_metadata_count_mismatch_is_rejected():
    payload = _payload(high=1)
    payload["metadata"]["vulnerabilities"]["high"] = 2
    payload["metadata"]["vulnerabilities"]["total"] = 2
    with pytest.raises(ValueError, match="vulnerability_count_mismatch"):
        gate.assess_npm_audit(payload, tool_returncode=1)


def test_invalid_total_is_rejected():
    payload = _payload(low=1)
    payload["metadata"]["vulnerabilities"]["total"] = 2
    with pytest.raises(ValueError, match="invalid_vulnerability_total"):
        gate.assess_npm_audit(payload, tool_returncode=0)


def test_unknown_severity_is_rejected():
    payload = _payload()
    payload["vulnerabilities"]["pkg-weird"] = {"name": "pkg-weird", "severity": "urgent"}
    with pytest.raises(ValueError, match="invalid_vulnerability_entry"):
        gate.assess_npm_audit(payload, tool_returncode=1)


def test_duplicate_json_keys_are_rejected():
    raw = b'{"auditReportVersion":2,"auditReportVersion":2}'
    with pytest.raises(ValueError, match="duplicate_json_key"):
        gate._strict_json(raw)


def test_nonfinite_json_is_rejected():
    with pytest.raises(ValueError, match="nonfinite_json"):
        gate._strict_json(b'{"x":NaN}')


def test_oversized_json_is_rejected():
    with pytest.raises(ValueError, match="audit_json_size_limit"):
        gate._strict_json(b" " * (gate.MAX_AUDIT_BYTES + 1))


def test_invalid_tool_returncode_is_rejected():
    with pytest.raises(ValueError, match="invalid_tool_returncode"):
        gate.assess_npm_audit(_payload(), tool_returncode=-1)


def test_cli_bootstraps_without_site_packages():
    completed = subprocess.run(
        [sys.executable, "-S", "scripts/npm_audit_gate.py", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--json-out" in completed.stdout
    assert "--timeout" in completed.stdout


def test_assessment_does_not_mutate_input():
    payload = _payload(moderate=1)
    original = deepcopy(payload)
    gate.assess_npm_audit(payload, tool_returncode=0)
    assert payload == original
