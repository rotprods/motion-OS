from __future__ import annotations

import json

import pytest

from src.avatar.fault_simulation import FaultMode, simulate_fault
from src.avatar.render_guard import RenderIntent, RenderState
from src.avatar.render_ledger import RenderLedger
from src.content.integrity import seal_manifest, verify_manifest
from src.content.replica_reconciliation import ReplicaStatus, build_replica_digest, reconcile, reconciliation_report
from src.content.schema_migrations import CURRENT_SCHEMA_VERSION, migrate


def _intent(state=RenderState.AUTHORIZED):
    return RenderIntent(
        intent_id="RND_TEST",
        content_id="CONTENT_TEST",
        profile_id="PROFILE_TEST",
        script_hash="abc",
        state=state,
        estimated_credits=8.0,
    )


def test_manifest_seal_detects_downstream_mutation():
    manifest = {
        "content_id": "X",
        "schema_version": 2,
        "source_refs": ["source"],
        "claim_notes": [],
        "viral_driver": "MONEY",
        "secondary_driver": None,
        "core_thesis": "save time",
        "hook": "hook",
        "script_display_text": "hello",
        "script_tts_text": "hello",
        "semantic_beats": [{"id": "B00_HOOK"}],
        "cta": {"text": "comment"},
        "moral": "moral",
        "duration_target_s": 35,
        "avatar": {"profile_id": "p"},
    }
    sealed = seal_manifest(manifest)
    assert verify_manifest(sealed)
    sealed["semantic_beats"][0]["id"] = "B99_MUTATED"
    assert not verify_manifest(sealed)


def test_schema_migration_rejects_future_version():
    migrated = migrate({"content_id": "x"})
    assert migrated["schema_version"] == CURRENT_SCHEMA_VERSION
    assert "claim_lineage" in migrated
    with pytest.raises(ValueError):
        migrate({"schema_version": CURRENT_SCHEMA_VERSION + 1})


def test_replica_reconciliation_is_fail_closed_on_conflict():
    canonical = build_replica_digest("github", {"a": 2}, revision=2)
    stale = build_replica_digest("drive", {"a": 1}, revision=1)
    conflict = build_replica_digest("library", {"a": 3}, revision=3)
    assert reconcile(canonical, stale) == ReplicaStatus.STALE_REPLICA
    assert reconcile(canonical, conflict) == ReplicaStatus.CONFLICT
    report = reconciliation_report(canonical, [stale, conflict])
    assert report["automatic_write_allowed"] is False
    assert report["write_requires_explicit_authorization"] is True
    assert "library" in report["conflicts"]
    assert report["safe_to_refresh"] == []
    assert "drive" in report["refresh_candidates"]


def test_timeout_after_acceptance_never_blindly_retries():
    outcome = simulate_fault(_intent(RenderState.SUBMITTED), FaultMode.TIMEOUT_AFTER_ACCEPT)
    assert outcome.reconcile_required is True
    assert outcome.retry_allowed is False
    assert outcome.state == RenderState.RECONCILE_REQUIRED


def test_render_ledger_detects_duplicate_submission_and_tamper(tmp_path):
    ledger = RenderLedger(tmp_path / "render.jsonl")
    intent = _intent(RenderState.SUBMITTED)
    ledger.record_intent(intent, "SUBMITTED")
    with pytest.raises(RuntimeError):
        ledger.assert_unique_submission(intent.intent_id)

    lines = ledger.path.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[0])
    record["state"] = "COMPLETED"
    ledger.path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ledger.read()


def test_render_ledger_reconstructs_latest_intent(tmp_path):
    ledger = RenderLedger(tmp_path / "render.jsonl")
    authorized = _intent(RenderState.AUTHORIZED)
    running = RenderIntent(**{**authorized.__dict__, "state": RenderState.RUNNING, "provider_job_id": "job1"})
    ledger.record_intent(authorized, "AUTHORIZED")
    ledger.record_intent(running, "RUNNING")
    restored = ledger.latest_intents()[authorized.intent_id]
    assert restored.state == RenderState.RUNNING
    assert restored.provider_job_id == "job1"
