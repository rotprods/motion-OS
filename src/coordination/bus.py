from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Protocol, Sequence

from .events import CoordinationEvent


class CoordinationBus(Protocol):
    """Authority-neutral event bus contract.

    Production implementations MUST persist events durably before acknowledging
    append and MUST persist consumer progress. Delivery may be at-least-once;
    consumers are responsible for idempotent side effects.
    """

    def append(self, event: CoordinationEvent) -> int:
        """Append one immutable event and return its monotonically increasing offset."""
        ...

    def read(self, *, after_offset: int = 0, limit: int = 100) -> Sequence[tuple[int, CoordinationEvent]]:
        """Read events with offset strictly greater than `after_offset`."""
        ...

    def consumer_offset(self, consumer_id: str) -> int:
        """Return the last durably acknowledged offset for a consumer."""
        ...

    def acknowledge(self, consumer_id: str, offset: int) -> None:
        """Advance a consumer offset monotonically. Rewinds are rejected."""
        ...


@dataclass(frozen=True, slots=True)
class AppendResult:
    offset: int
    duplicate: bool


class InMemoryReferenceBus:
    """Deterministic reference backend for unit/adversarial tests only.

    This implementation intentionally does NOT claim multi-host authority. It
    models the required append/idempotency/consumer-offset semantics without an
    external dependency so that contract tests can run in the base dev setup.
    """

    authority_level = "REFERENCE_TEST_ONLY"

    def __init__(self) -> None:
        self._lock = RLock()
        self._events: list[CoordinationEvent] = []
        self._by_event_id: dict[str, int] = {}
        self._by_hash: dict[str, int] = {}
        self._consumer_offsets: dict[str, int] = {}

    def append(self, event: CoordinationEvent) -> int:
        return self.append_checked(event).offset

    def append_checked(self, event: CoordinationEvent) -> AppendResult:
        with self._lock:
            by_id = self._by_event_id.get(event.event_id)
            if by_id is not None:
                existing = self._events[by_id - 1]
                if existing.provenance_hash != event.provenance_hash:
                    raise ValueError("event_id collision with different canonical content")
                return AppendResult(offset=by_id, duplicate=True)

            by_hash = self._by_hash.get(event.provenance_hash)
            if by_hash is not None:
                return AppendResult(offset=by_hash, duplicate=True)

            offset = len(self._events) + 1
            self._events.append(event)
            self._by_event_id[event.event_id] = offset
            self._by_hash[event.provenance_hash] = offset
            return AppendResult(offset=offset, duplicate=False)

    def read(self, *, after_offset: int = 0, limit: int = 100) -> Sequence[tuple[int, CoordinationEvent]]:
        if after_offset < 0:
            raise ValueError("after_offset must be >= 0")
        if limit < 1:
            raise ValueError("limit must be >= 1")
        with self._lock:
            start = min(after_offset, len(self._events))
            stop = min(start + limit, len(self._events))
            return tuple((idx + 1, self._events[idx]) for idx in range(start, stop))

    def consumer_offset(self, consumer_id: str) -> int:
        if not consumer_id:
            raise ValueError("consumer_id is required")
        with self._lock:
            return self._consumer_offsets.get(consumer_id, 0)

    def acknowledge(self, consumer_id: str, offset: int) -> None:
        if not consumer_id:
            raise ValueError("consumer_id is required")
        with self._lock:
            if offset < 0 or offset > len(self._events):
                raise ValueError("offset is outside the event stream")
            current = self._consumer_offsets.get(consumer_id, 0)
            if offset < current:
                raise ValueError("consumer offset rewind is forbidden")
            self._consumer_offsets[consumer_id] = offset

    def poll(self, consumer_id: str, *, limit: int = 100) -> Sequence[tuple[int, CoordinationEvent]]:
        return self.read(after_offset=self.consumer_offset(consumer_id), limit=limit)

    def reset_for_test(self) -> None:
        with self._lock:
            self._events.clear()
            self._by_event_id.clear()
            self._by_hash.clear()
            self._consumer_offsets.clear()
