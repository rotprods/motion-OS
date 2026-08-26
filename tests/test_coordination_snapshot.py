from datetime import datetime, timezone

from src.coordination.snapshot import CoordinationSnapshot


def raw_snapshot():
    return {
        "schema_version": 1,
        "project_id": "motion://project/MOTION.OS",
        "captured_at": "2026-08-26T19:55:00Z",
        "main_sha": "abcdef1234567",
        "release_gates": ["gate-b", "gate-a"],
        "active_prs": [{"number": 37, "branch": "feat/x", "state": "OPEN"}],
        "active_agents": [{"agent_id": "motion://agent/a"}],
        "active_leases": [],
        "tasks": [{"task_id": "motion://task/t"}],
        "decisions": [],
        "contracts": [{"uri": "contract:avatar-handoff", "revision": "v2"}],
        "conflicts": [],
        "checkpoints": [{"checkpoint_id": "cp-1"}],
        "source_refs": [{
            "uri": "git:AGENTS.md",
            "revision": "blob:abc",
            "sha256": "a" * 64,
            "sensitivity": "INTERNAL",
        }],
        "projection": {"version": 4, "hash": "b" * 64, "built_at": "2026-08-26T19:54:00Z"},
    }


def test_snapshot_hash_is_deterministic():
    a = CoordinationSnapshot.from_mapping(raw_snapshot())
    b = CoordinationSnapshot.from_mapping(dict(raw_snapshot()))
    assert a.snapshot_sha256 == b.snapshot_sha256
    assert len(a.snapshot_sha256) == 64


def test_snapshot_compiles_sealed_context_pack_with_expected_revisions():
    snapshot = CoordinationSnapshot.from_mapping(raw_snapshot())
    pack = snapshot.compile_context_pack(
        agent_id="motion://agent/a",
        session_id="motion://session/a",
        allowed_write_scopes=["contract:avatar-handoff"],
        forbidden_write_scopes=["contract:studio-entry"],
        goal_summary="continue Phase06 safely",
    )
    assert pack.verify_seal()
    assert pack.main_sha == "abcdef1234567"
    assert pack.projection_version == 4
    assert pack.projection_hash == "b" * 64
    assert pack.expected_revisions["contract:avatar-handoff"] == "v2"
    assert pack.expected_revisions["snapshot:coordination"] == snapshot.snapshot_sha256
    assert pack.checkpoint_refs == ("cp-1",)


def test_snapshot_context_becomes_stale_on_contract_source_or_main_change():
    snapshot = CoordinationSnapshot.from_mapping(raw_snapshot())
    pack = snapshot.compile_context_pack(
        agent_id="motion://agent/a",
        session_id="motion://session/a",
        allowed_write_scopes=[],
        goal_summary="safe work",
    )
    now = datetime(2026, 8, 26, 20, 0, tzinfo=timezone.utc)
    assert pack.is_stale(
        now=now,
        main_sha="changed-main",
        projection_version=4,
        projection_hash="b" * 64,
        current_source_revisions={"git:AGENTS.md": "blob:abc"},
    )
    assert pack.is_stale(
        now=now,
        main_sha="abcdef1234567",
        projection_version=4,
        projection_hash="b" * 64,
        current_source_revisions={"git:AGENTS.md": "blob:changed"},
    )


def test_snapshot_rejects_incomplete_input():
    raw = raw_snapshot()
    raw.pop("main_sha")
    try:
        CoordinationSnapshot.from_mapping(raw)
    except ValueError as exc:
        assert "main_sha" in str(exc)
    else:
        raise AssertionError("incomplete snapshot should fail closed")
