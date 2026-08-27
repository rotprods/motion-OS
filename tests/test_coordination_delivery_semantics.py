import pytest

from src.coordination.event_semantics import EventRole, event_role, outcome_satisfies_command
from src.coordination.event_store import InMemoryReferenceEventStore
from src.coordination.events import CoordinationEvent, ProvenanceRef
from src.coordination.inbox import ReferenceInbox


def make_event(revision=1, expected=0, idem="idem-1", event_type="TASK_STARTED"):
    return CoordinationEvent(
        event_type=event_type,
        aggregate_type="task",
        aggregate_id="motion://task/t1",
        aggregate_revision=revision,
        expected_revision=expected,
        project_id="motion://project/MOTION.OS",
        agent_id="motion://agent/test",
        session_id="motion://session/test",
        correlation_id="c1",
        idempotency_key=idem,
        payload={"revision": revision},
        provenance=(ProvenanceRef("test", "fixture:delivery"),),
    )


def test_event_watermark_and_state_snapshot_are_deterministic():
    store = InMemoryReferenceEventStore()
    assert store.watermark() == 0
    store.append(make_event())
    store.append(make_event(2, 1, "idem-2", "TASK_CHECKPOINTED"))
    snapshot = store.snapshot()
    assert snapshot.event_watermark == 2
    assert snapshot.verify()
    assert snapshot == store.snapshot()


def test_reference_inbox_deduplicates_effects_and_detects_conflicting_replay():
    inbox = ReferenceInbox()
    assert inbox.record(consumer_id="cos-projector", event_id="evt-1", effect_hash="abc")
    assert not inbox.record(consumer_id="cos-projector", event_id="evt-1", effect_hash="abc")
    assert inbox.processed(consumer_id="cos-projector", event_id="evt-1")
    with pytest.raises(ValueError, match="conflicting effect_hash"):
        inbox.record(consumer_id="cos-projector", event_id="evt-1", effect_hash="different")


def test_command_and_outcome_are_distinct_event_roles():
    assert event_role("WORK_CLAIM_REQUESTED") == EventRole.COMMAND
    assert event_role("WORK_CLAIMED") == EventRole.OUTCOME
    assert event_role("CI_OBSERVED") == EventRole.FACT
    assert outcome_satisfies_command("WORK_CLAIM_REQUESTED", "WORK_CLAIMED")
    with pytest.raises(ValueError):
        outcome_satisfies_command("WORK_CLAIMED", "WORK_CLAIMED")
