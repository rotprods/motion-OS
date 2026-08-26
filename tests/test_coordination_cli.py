import json
import subprocess
import sys


def test_bootstrap_snapshot_validates_from_cli():
    result = subprocess.run(
        [sys.executable, "scripts/coordination_cli.py", "snapshot-validate", "coordination/bootstrap_snapshot.json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert len(payload["snapshot_sha256"]) == 64


def test_context_compile_cli_emits_verified_pack(tmp_path):
    output = tmp_path / "context.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/coordination_cli.py",
            "context-compile",
            "coordination/bootstrap_snapshot.json",
            "--agent-id", "motion://agent/test",
            "--session-id", "motion://session/test",
            "--goal", "continue without collisions",
            "--allow", "contract:coordination-event",
            "--forbid", "contract:avatar-handoff",
            "--output", str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["agent_id"] == "motion://agent/test"
    assert payload["allowed_write_scopes"] == ["contract:coordination-event"]
    assert payload["forbidden_write_scopes"] == ["contract:avatar-handoff"]
    assert len(payload["seal_sha256"]) == 64


def test_message_cli_fails_closed_on_unknown_kind():
    result = subprocess.run(
        [
            sys.executable,
            "scripts/coordination_cli.py",
            "message",
            "--kind", "MAGIC_SUCCESS",
            "--agent-id", "motion://agent/test",
            "--session-id", "motion://session/test",
            "--correlation-id", "work-1",
            "--summary", "should fail",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "unsupported coordination message kind" in result.stderr
