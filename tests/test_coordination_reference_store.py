from __future__ import annotations

from datetime import datetime, timedelta, timezone
import threading

import pytest

from src.coordination.contracts import AgentEvent, ProvenanceRef, PROJECT_ID
from src.coordination.reference_store import (
    IdempotencyConflict,
    LeaseConflict,
    ReferenceCoordinationStore,
    RevisionConflict,
    StaleWriter,
)


class Clock:
    def __init__(self):
        self.value = datetime(2026, 8, 26, 19, 0, tzinfo=timezone.utc)

    def now(self):
        return self.value

    def advance(self, seconds: int):
        self.value += timedelta(seconds=seconds)


def event(*, event_id="evt1", idem="idem1", rev=1, expected=0, payload=None):
    return AgentEvent(
        event_id=event_id,
        actor_id="motion://agent/developer/test",
        session_id="motion://session/test",
        event_type="TASK_CREATED",
        aggregate_type="task",
        aggregate_id="task-1",
        aggregate_revision=rev,
        expected_revision=expected,
        correlation_id="corr_12345678",
        idempotency_key=idem,
        payload=payload or {"name": "x"},
        provenance=(ProvenanceRef("test", "fixture"),),
    )


def test_idempotent_replay_returns_original_event():
    store = ReferenceCoordinationStore()
    first = store.append_event(event())
    replay = store.append_event(event(event_id="evt-different"))
    assert replay is first
    assert len(store.events()) == 1


def test_idempotency_key_cannot_change_payload():
    store = ReferenceCoordinationStore()
    store.append_event(event())
    with pytest.raises(IdempotencyConflict):
        store.append_event(event(event_id="evt2", payload={"name": "different"}))


def test_expected_revision_is_compare_and_swap():
    store = ReferenceCoordinationStore()
    store.append_event(event())
    with pytest.raises(RevisionConflict):
        store.append_event(event(event_id="evt2", idem="idem2", rev=2, expected=0))
    accepted = store.append_event(event(event_id="evt3", idem="idem3", rev=2, expected=1))
    assert accepted.aggregate_revision == 2


def test_only_one_thread_can_acquire_same_live_resource():
    clock = Clock()
    store = ReferenceCoordinationStore(now=clock.now)
    barrier = threading.Barrier(2)
    wins = []
    losses = []

    def worker(n):
        barrier.wait()
        try:
            token = store.acquire_lease(
                project_id=PROJECT_ID,
                resource_key="schema:phase06-handoff",
                owner_agent_id=f"motion://agent/developer/{n}",
                session_id=f"motion://session/{n}",
                workstream_id=f"ws-{n}",
                ttl_seconds=30,
            )
            wins.append(token)
        except LeaseConflict as exc:
            losses.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(wins) == 1
    assert len(losses) == 1
    assert wins[0].generation == 1


def test_expired_lease_takeover_increments_generation_and_fences_stale_writer():
    clock = Clock()
    store = ReferenceCoordinationStore(now=clock.now)
    first = store.acquire_lease(
        project_id=PROJECT_ID,
        resource_key="contract:renderer-input",
        owner_agent_id="motion://agent/developer/a",
        session_id="motion://session/a",
        workstream_id="ws-a",
        ttl_seconds=10,
    )
    clock.advance(11)
    second = store.acquire_lease(
        project_id=PROJECT_ID,
        resource_key="contract:renderer-input",
        owner_agent_id="motion://agent/developer/b",
        session_id="motion://session/b",
        workstream_id="ws-b",
        ttl_seconds=10,
    )
    assert second.generation == first.generation + 1
    with pytest.raises(StaleWriter):
        store.assert_write_authority(
            project_id=PROJECT_ID,
            resource_key="contract:renderer-input",
            owner_agent_id=first.owner_agent_id,
            session_id=first.session_id,
            generation=first.generation,
        )
    assert store.assert_write_authority(
        project_id=PROJECT_ID,
        resource_key="contract:renderer-input",
        owner_agent_id=second.owner_agent_id,
        session_id=second.session_id,
        generation=second.generation,
    ) == second


def test_live_lease_heartbeat_preserves_generation():
    clock = Clock()
    store = ReferenceCoordinationStore(now=clock.now)
    lease = store.acquire_lease(
        project_id=PROJECT_ID,
        resource_key="artifact:master",
        owner_agent_id="motion://agent/developer/a",
        session_id="motion://session/a",
        workstream_id="ws-a",
        ttl_seconds=10,
    )
    clock.advance(5)
    renewed = store.heartbeat_lease(
        project_id=PROJECT_ID,
        resource_key="artifact:master",
        owner_agent_id=lease.owner_agent_id,
        session_id=lease.session_id,
        generation=lease.generation,
        ttl_seconds=20,
    )
    assert renewed.generation == lease.generation
    assert renewed.expires_at != lease.expires_at
