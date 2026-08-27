import pytest

from src.coordination.event_store import InMemoryReferenceEventStore
from src.coordination.leases import ReferenceLeaseAuthority
from src.coordination.sdk import AgentCoordinationSDK


AGENT = "motion://agent/sdk-test"
SESSION = "motion://session/sdk-test"
WORKSTREAM = "motion://workstream/sdk-test"


def sdk():
    store = InMemoryReferenceEventStore()
    leases = ReferenceLeaseAuthority()
    return AgentCoordinationSDK(event_store=store, lease_authority=leases), store, leases


def test_claim_emits_command_then_outcome_and_holds_fenced_lease():
    client, store, leases = sdk()
    result = client.claim(
        agent_id=AGENT,
        session_id=SESSION,
        workstream_id=WORKSTREAM,
        resource_uri="contract:coordination-event",
        scope="WRITE",
        correlation_id="motion://work/sdk-test",
        idempotency_key="sdk-claim-1",
    )
    events = [item.event for item in store.read()]
    assert [event.event_type for event in events] == ["WORK_CLAIM_REQUESTED", "WORK_CLAIMED"]
    assert events[1].causation_id == events[0].event_id
    assert result.lease.fencing_token == 1
    assert leases.active()[0].lease_id == result.lease.lease_id


def test_preflight_blocks_overlapping_write_scope():
    client, _, leases = sdk()
    leases.acquire(
        resource_uri="contract:avatar-handoff",
        scope="WRITE",
        agent_id="motion://agent/other",
        session_id="motion://session/other",
    )
    finding = client.preflight_claim(requested_scopes=("contract:avatar-handoff",))
    assert finding.approved is False
    assert finding.finding.classification.value == "SEMANTIC_OVERLAP"


class FailSecondAppendStore(InMemoryReferenceEventStore):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def append(self, event):
        self.calls += 1
        if self.calls == 2:
            raise RuntimeError("simulated outcome persistence failure")
        return super().append(event)


def test_outcome_persistence_failure_compensates_lease_and_records_failure():
    store = FailSecondAppendStore()
    leases = ReferenceLeaseAuthority()
    client = AgentCoordinationSDK(event_store=store, lease_authority=leases)
    with pytest.raises(RuntimeError, match="simulated outcome persistence failure"):
        client.claim(
            agent_id=AGENT,
            session_id=SESSION,
            workstream_id=WORKSTREAM,
            resource_uri="contract:coordination-event",
            scope="WRITE",
            correlation_id="motion://work/sdk-test",
            idempotency_key="sdk-claim-fail",
        )
    assert leases.active() == ()
    events = [item.event for item in store.read()]
    assert [event.event_type for event in events] == ["WORK_CLAIM_REQUESTED", "WORK_CLAIM_FAILED"]
    assert events[-1].payload["compensation"] == "LEASE_RELEASED"


def test_checkpoint_advances_same_workstream_revision():
    client, store, _ = sdk()
    client.claim(
        agent_id=AGENT,
        session_id=SESSION,
        workstream_id=WORKSTREAM,
        resource_uri="contract:coordination-event",
        scope="WRITE",
        correlation_id="motion://work/sdk-test",
        idempotency_key="sdk-claim-2",
    )
    checkpoint = client.checkpoint(
        agent_id=AGENT,
        session_id=SESSION,
        workstream_id=WORKSTREAM,
        correlation_id="motion://work/sdk-test",
        idempotency_key="sdk-checkpoint-1",
        summary="P12 checkpoint",
        evidence_refs=("git:commit:test",),
    )
    assert checkpoint.aggregate_revision == 3
    assert store.aggregate_revision("workstream", WORKSTREAM) == 3
