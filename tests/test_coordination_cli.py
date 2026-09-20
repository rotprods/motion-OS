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


def test_live_context_compile_cli_reconciles_pr_lifecycle(tmp_path):
    lifecycle = tmp_path / "lifecycle.json"
    lifecycle.write_text(json.dumps({
        "repository": "rotprods/motion-OS",
        "main_sha": "e77b2aaf01e0c439306aa3374f8c8df6fea0afed",
        "supersessions": {"34": 42, "35": 38},
        "prs": [
            {"number": 34, "head": "feat/remotion-runtime-proof", "head_sha": "1" * 40, "base": "main", "state": "closed", "merged": False},
            {"number": 37, "head": "feat/avatar-script-engine", "head_sha": "2" * 40, "base": "main", "state": "open", "draft": True},
            {"number": 42, "head": "fix/remotion-runtime-proof-v2", "head_sha": "3" * 40, "base": "main", "state": "closed", "merged": True},
            {"number": 44, "head": "feat/agentic-coordination-kernel", "head_sha": "4" * 40, "base": "main", "state": "open", "draft": True},
        ],
    }), encoding="utf-8")
    output = tmp_path / "live-context.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/coordination_cli.py",
            "live-context-compile",
            "coordination/bootstrap_snapshot.json",
            str(lifecycle),
            "--agent-id", "motion://agent/test",
            "--session-id", "motion://session/live-test",
            "--goal", "reconstruct current truth",
            "--generated-at", "2026-08-27T12:00:00Z",
            "--event-watermark", "7",
            "--allow", "phase:07/agentic-coordination",
            "--output", str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert [pr["number"] for pr in payload["active_prs"]] == [37, 44]
    assert payload["main_sha"] == "e77b2aaf01e0c439306aa3374f8c8df6fea0afed"
    assert payload["expected_revisions"]["event:watermark"] == 7
    assert len(payload["seal_sha256"]) == 64


def test_irreversible_preflight_cli_blocks_stale_context():
    result = subprocess.run(
        [
            sys.executable, "scripts/coordination_cli.py", "irreversible-preflight",
            "--context-main-sha", "abc1234",
            "--context-event-watermark", "7",
            "--live-main-sha", "def5678",
            "--live-event-watermark", "8",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 3
    payload = json.loads(result.stdout)
    assert payload["fresh"] is False
    assert payload["reasons"] == ["main_sha_advanced", "event_watermark_advanced"]


def test_truth_check_cli_reports_stale_current_surface(tmp_path):
    source = tmp_path / "truth.json"
    source.write_text(json.dumps({
        "live_github": {"pr:44": "MERGED", "main:sha": "abc1234"},
        "claims": [
            {"surface": "ACTIVE_AGENTS.yaml", "key": "pr:44", "value": "FINAL_QUALIFICATION"},
            {"surface": "historical", "key": "pr:44", "value": "OPEN_DRAFT", "current": False},
        ],
    }), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "scripts/coordination_cli.py", "truth-check", str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 4
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["stale_surfaces"] == ["ACTIVE_AGENTS.yaml"]


def test_truth_check_cli_preserves_boolean_semantics_and_rejects_string_boolean(tmp_path):
    good = tmp_path / "truth-good.json"
    good.write_text(json.dumps({
        "live_github": {"ci:green": True},
        "claims": [{"surface": "machine", "key": "ci:green", "value": True, "current": True}],
    }), encoding="utf-8")
    good_run = subprocess.run(
        [sys.executable, "scripts/coordination_cli.py", "truth-check", str(good)],
        capture_output=True, text=True, check=False,
    )
    assert good_run.returncode == 0, good_run.stderr

    bad = tmp_path / "truth-bad.json"
    bad.write_text(json.dumps({
        "live_github": {"ci:green": True},
        "claims": [{"surface": "machine", "key": "ci:green", "value": True, "current": "false"}],
    }), encoding="utf-8")
    bad_run = subprocess.run(
        [sys.executable, "scripts/coordination_cli.py", "truth-check", str(bad)],
        capture_output=True, text=True, check=False,
    )
    assert bad_run.returncode == 2
    assert "current must be boolean" in bad_run.stderr


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
