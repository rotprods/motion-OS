from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.agent_event as agent_event


def _valid_event() -> dict:
    return {
        "event_id": "20260827T120000000000Z-test-agent-abcdef12",
        "event_type": "work.completed",
        "timestamp": "2026-08-27T12:00:00Z",
        "agent_id": "test-agent",
        "project": "MOTION.OS",
        "branch": "test/branch",
        "commit_sha": "abcdef1",
        "pr_number": 46,
        "summary": "test event",
        "affected_paths": ["src/content/example.py"],
        "checks": {"quick": "PASS"},
        "authority": "VERIFIED",
        "correlation_id": "TEST",
        "metadata": {},
    }


def test_valid_event_passes_schema_and_format():
    agent_event.validate_event(_valid_event())


def test_invalid_timestamp_is_rejected():
    event = _valid_event()
    event["timestamp"] = "yesterday"
    with pytest.raises(ValueError):
        agent_event.validate_event(event)


def test_invalid_commit_sha_is_rejected():
    event = _valid_event()
    event["commit_sha"] = "not-a-sha"
    with pytest.raises(ValueError):
        agent_event.validate_event(event)


def test_validate_tree_rejects_duplicate_event_ids(tmp_path: Path, monkeypatch):
    root = tmp_path / "events"
    day = root / "2026-08-27"
    day.mkdir(parents=True)
    event = _valid_event()
    (day / "one.json").write_text(json.dumps(event), encoding="utf-8")
    (day / "two.json").write_text(json.dumps(event), encoding="utf-8")
    monkeypatch.setattr(agent_event, "EVENT_ROOT", root)
    with pytest.raises(ValueError, match="duplicate event_id"):
        agent_event.validate_tree()
