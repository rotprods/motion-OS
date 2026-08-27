import json
from pathlib import Path
import subprocess
import sys


def write_input(tmp_path: Path) -> Path:
    path = tmp_path / "status.json"
    path.write_text(json.dumps({
        "project_id": "motion://project/MOTION.OS",
        "main_sha": "abcdef1234567890",
        "event_watermark": 9,
        "health": {"healthy": True, "active_leases": 0},
        "active_work": [{"work_id": "w1"}],
        "conflicts": [{"class": "SEMANTIC_OVERLAP", "resource": "contract:x"}],
        "next_actions": [{"priority": 1, "action": "resolve x"}],
        "traces": [{"event_id": "evt-1", "content_id": "CNT_001", "work_id": "w1"}],
    }), encoding="utf-8")
    return path


def run_cli(path: Path, *args: str):
    return subprocess.run(
        [sys.executable, "scripts/coordination_status.py", str(path), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_status_cli_exposes_health_next_conflicts_and_trace(tmp_path):
    path = write_input(tmp_path)
    for command in ("status", "health", "next", "conflicts"):
        result = run_cli(path, command)
        assert result.returncode == 0, result.stderr
        json.loads(result.stdout)
    trace = run_cli(path, "trace", "CNT_001")
    assert trace.returncode == 0, trace.stderr
    assert json.loads(trace.stdout)[0]["event_id"] == "evt-1"


def test_trace_without_identifier_fails_visible(tmp_path):
    result = run_cli(write_input(tmp_path), "trace")
    assert result.returncode == 2
    assert "trace requires an identifier" in result.stderr


def test_malformed_operator_input_never_converts_to_success(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"project_id":"bad"}', encoding="utf-8")
    result = run_cli(path, "status")
    assert result.returncode == 2
    assert "coordination_status error" in result.stderr
