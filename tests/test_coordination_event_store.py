from dataclasses import replace

import pytest

from src.coordination.event_store import (
    IdempotencyConflict,
    InMemoryReferenceEventStore,
    RevisionConflict,
)
from src.coordination.events import CoordinationEvent, ProvenanceRef


def make_event(*, revision=1, expected=0, idem="idem-1", payload=None, event_type="TASK_STARTED"):
    return CoordinationEvent(
        event_type=event_type,
        aggregate_type="task",
        aggregate_id="motion://task/t-1",
        aggregate_revision=revision,
        expected_revision=expected,
        project_id="motion://project/MOTION.OS",
        agent_id="motion://agent/test",
        session_id="motion://session/test",
        correlation_id="motion://work/test",
        idempotency_key=idem,
        payload=payload or {"value": revision},
        provenance=(ProvenanceRef("test", "fixture:event-store"),),
    )


def test_append_advances_aggregate_revision_monotonically():
    store = InMemoryReferenceEventStore()
    first = store.append(make_event())
    second = store.append(make_event(revision=2, expected=1, idem="idem-2", event_type="TASK_CHECKPOINTED"))
    assert first.sequence_id == 1
    assert second.sequence_id == 2
    assert store.aggregate_revision("task", "motion://task/t-1") == 2


def test_stale_expected_revision_fails_closed():
    store = InMemoryReferenceEventStore()
    store.append(make_event())
    with pytest.raises(RevisionConflict, match="expected aggregate revision"):
        store.append(make_event(revision=2, expected=0, idem="idem-stale", event_type="TASK_CHECKPOINTED"))


def test_skipped_revision_fails_closed():
    store = InMemoryReferenceEventStore()
    store.append(make_event())
    with pytest.raises(RevisionConflict, match="required 2"):
        store.append(make_event(revision=3, expected=1, idem="idem-skip", event_type="TASK_CHECKPOINTED"))


def test_same_idempotency_key_same_logical_event_returns_committed_event():
    store = InMemoryReferenceEventStore()
    event = make_event()
    first = store.append(event)
    replay = store.append(replace(event, event_id=event.event_id))
    assert first.sequence_id == replay.sequence_id == 1
    assert replay.duplicate
    assert len(store.read()) == 1


def test_same_idempotency_key_different_payload_is_rejected():
    store = InMemoryReferenceEventStore()
    store.append(make_event())
    with pytest.raises(IdempotencyConflict, match="different logical event"):
        store.append(make_event(idem="idem-1", payload={"value": "tampered"}))


def test_same_event_id_with_different_content_is_rejected():
    store = InMemoryReferenceEventStore()
    event = make_event()
    store.append(event)
    with pytest.raises(IdempotencyConflict, match="event_id reused"):
        store.append(replace(event, payload={"tampered": True}, provenance_hash=""))


def test_store_never_claims_distributed_authority():
    assert InMemoryReferenceEventStore().authority_level == "REFERENCE_TEST_ONLY"
