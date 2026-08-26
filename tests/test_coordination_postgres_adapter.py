from __future__ import annotations

from typing import Any

import pytest

from src.coordination.events import CoordinationEvent
from src.coordination.postgres_store import PostgresCoordinationStore


class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.executions: list[tuple[str, tuple[Any, ...] | None]] = []

    def execute(self, query, params=None):
        self.executions.append((query, params))
        return self

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


def event():
    return CoordinationEvent(
        event_type="task.started",
        aggregate_type="task",
        aggregate_id="motion://task/t1",
        project_id="motion://project/MOTION.OS",
        agent_id="motion://agent/a",
        session_id="motion://session/a",
        correlation_id="c1",
        payload={"task_uri": "motion://task/t1"},
    )


def test_append_delegates_atomicity_to_database_function():
    e = event()
    cursor = FakeCursor([(e.event_id, False)])
    store = PostgresCoordinationStore(lambda: FakeConnection(cursor))
    outcome = store.append_event(e)
    assert outcome.event_id == e.event_id
    assert outcome.duplicate is False
    assert "append_coordination_event" in cursor.executions[0][0]
    assert cursor.executions[0][1][0] == e.event_id
    assert cursor.executions[0][1][16] == e.provenance_hash


def test_read_cursor_requires_complete_offset_pair_and_bounded_limit():
    store = PostgresCoordinationStore(lambda: FakeConnection(FakeCursor([])))
    with pytest.raises(ValueError):
        store.read_events(project_id="motion://project/MOTION.OS", after_recorded_at="2026-01-01T00:00:00Z")
    with pytest.raises(ValueError):
        store.read_events(project_id="motion://project/MOTION.OS", limit=1001)


def test_lease_acquisition_uses_database_fencing_function():
    cursor = FakeCursor([("lease-id", 9)])
    store = PostgresCoordinationStore(lambda: FakeConnection(cursor))
    lease_id, token = store.acquire_lease(
        project_id="motion://project/MOTION.OS",
        resource_uri="contract:avatar-handoff",
        scope="WRITE",
        agent_id="motion://agent/a",
        session_id="motion://session/a",
    )
    assert lease_id == "lease-id"
    assert token == 9
    assert "acquire_resource_lease" in cursor.executions[0][0]


def test_outbox_claim_maps_dispatch_lease_state():
    cursor = FakeCursor([(7, "event-id", "motion.coordination", 2, "worker-a")])
    store = PostgresCoordinationStore(lambda: FakeConnection(cursor))
    rows = store.claim_outbox(worker_id="worker-a", limit=5)
    assert rows[0].outbox_id == 7
    assert rows[0].event_id == "event-id"
    assert rows[0].attempts == 2
    assert rows[0].lock_owner == "worker-a"
