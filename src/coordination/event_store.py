from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Protocol, Sequence

from .events import CoordinationEvent


class EventStoreError(RuntimeError):
    pass


class RevisionConflict(EventStoreError):
    pass


class IdempotencyConflict(EventStoreError):
    pass


@dataclass(frozen=True, slots=True)
class StoredEvent:
    sequence_id: int
    event: CoordinationEvent
    duplicate: bool = False


class CoordinationEventStore(Protocol):
    """Canonical coordination state-transition contract.

    The event store owns aggregate revision and idempotency semantics. A bus may
    transport committed events, but must not invent aggregate authority.
    """

    def append(self, event: CoordinationEvent) -> StoredEvent: ...

    def aggregate_revision(self, aggregate_type: str, aggregate_id: str) -> int: ...

    def read(self, *, after_sequence: int = 0, limit: int = 100) -> Sequence[StoredEvent]: ...


class InMemoryReferenceEventStore:
    """Deterministic process-local semantic oracle for event-sourced coordination.

    This is deliberately NOT a distributed authority. It exists to qualify the
    contracts that a future SQLite/Postgres backend must preserve.
    """

    authority_level = "REFERENCE_TEST_ONLY"

    def __init__(self) -> None:
        self._lock = RLock()
        self._events: list[CoordinationEvent] = []
        self._heads: dict[tuple[str, str], int] = {}
        self._by_idempotency: dict[str, int] = {}
        self._by_event_id: dict[str, int] = {}

    def aggregate_revision(self, aggregate_type: str, aggregate_id: str) -> int:
        with self._lock:
            return self._heads.get((aggregate_type, aggregate_id), 0)

    def append(self, event: CoordinationEvent) -> StoredEvent:
        with self._lock:
            by_event_id = self._by_event_id.get(event.event_id)
            if by_event_id is not None:
                existing = self._events[by_event_id - 1]
                if existing.provenance_hash != event.provenance_hash:
                    raise IdempotencyConflict("event_id reused with different canonical content")
                return StoredEvent(by_event_id, existing, duplicate=True)

            idem_sequence = self._by_idempotency.get(event.idempotency_key)
            if idem_sequence is not None:
                existing = self._events[idem_sequence - 1]
                if existing.logical_command_hash != event.logical_command_hash:
                    raise IdempotencyConflict(
                        f"idempotency_key {event.idempotency_key!r} reused for a different logical event"
                    )
                return StoredEvent(idem_sequence, existing, duplicate=True)

            key = (event.aggregate_type, event.aggregate_id)
            current = self._heads.get(key, 0)
            if event.expected_revision is not None and event.expected_revision != current:
                raise RevisionConflict(
                    f"expected aggregate revision {event.expected_revision}, current {current}"
                )
            required = current + 1
            if event.aggregate_revision != required:
                raise RevisionConflict(
                    f"event aggregate_revision {event.aggregate_revision}, required {required}"
                )

            sequence = len(self._events) + 1
            self._events.append(event)
            self._heads[key] = event.aggregate_revision
            self._by_event_id[event.event_id] = sequence
            self._by_idempotency[event.idempotency_key] = sequence
            return StoredEvent(sequence, event, duplicate=False)

    def read(self, *, after_sequence: int = 0, limit: int = 100) -> Sequence[StoredEvent]:
        if after_sequence < 0:
            raise ValueError("after_sequence must be >= 0")
        if limit < 1:
            raise ValueError("limit must be >= 1")
        with self._lock:
            start = min(after_sequence, len(self._events))
            stop = min(start + limit, len(self._events))
            return tuple(
                StoredEvent(idx + 1, self._events[idx], duplicate=False)
                for idx in range(start, stop)
            )
