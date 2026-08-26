from __future__ import annotations

import pytest

from src.coordination.contracts import (
    AgentEvent,
    LeaseToken,
    ProvenanceRef,
    normalize_scopes,
    semantic_resource,
    sha256_json,
)


def make_event(**overrides):
    base = dict(
        event_id="evt_01",
        actor_id="motion://agent/developer/test",
        session_id="motion://session/test-1",
        event_type="WORK_STARTED",
        aggregate_type="workstream",
        aggregate_id="ws-test",
        aggregate_revision=1,
        expected_revision=0,
        correlation_id="corr_12345678",
        idempotency_key="idem_12345678",
        payload={"scope": ["src/foo.py"], "summary": "test"},
        provenance=(ProvenanceRef("git", "rotprods/motion-OS", revision="abc"),),
    )
    base.update(overrides)
    return AgentEvent(**base)


def test_payload_hash_is_order_independent_for_object_keys():
    assert sha256_json({"b": 2, "a": 1}) == sha256_json({"a": 1, "b": 2})


def test_event_payload_hash_matches_serialized_envelope():
    event = make_event()
    assert event.to_dict()["payload_hash"] == sha256_json(event.payload)


def test_event_requires_agent_uri():
    with pytest.raises(ValueError):
        make_event(actor_id="developer/test")


def test_event_requires_provenance():
    with pytest.raises(ValueError):
        make_event(provenance=())


def test_event_rejects_duplicate_parents():
    with pytest.raises(ValueError):
        make_event(parent_event_ids=("evt_a", "evt_a"))


def test_event_rejects_non_uppercase_type():
    with pytest.raises(ValueError):
        make_event(event_type="work_started")


def test_lease_generation_is_fencing_token():
    lease = LeaseToken(
        lease_id="lease_1",
        resource_key="schema:phase06-handoff",
        owner_agent_id="motion://agent/developer/test",
        session_id="motion://session/test-1",
        workstream_id="ws-test",
        generation=3,
        acquired_at="2026-08-26T19:00:00Z",
        expires_at="2026-08-26T19:10:00Z",
    )
    assert lease.generation == 3


def test_lease_rejects_generation_zero():
    with pytest.raises(ValueError):
        LeaseToken(
            lease_id="lease_1",
            resource_key="x",
            owner_agent_id="motion://agent/developer/test",
            session_id="motion://session/test-1",
            workstream_id="ws-test",
            generation=0,
            acquired_at="2026-08-26T19:00:00Z",
            expires_at="2026-08-26T19:10:00Z",
        )


def test_semantic_resource_and_scope_normalization_are_deterministic():
    assert semantic_resource("schema", "phase06", "handoff") == "schema:phase06:handoff"
    assert normalize_scopes(["b", " a ", "b", ""]) == ("a", "b")
