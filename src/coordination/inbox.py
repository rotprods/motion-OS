from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass(frozen=True, slots=True)
class InboxRecord:
    consumer_id: str
    event_id: str
    effect_hash: str | None = None


class ReferenceInbox:
    """Process-local exactly-once-effect oracle for at-least-once delivery tests."""

    authority_level = "REFERENCE_TEST_ONLY"

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[tuple[str, str], InboxRecord] = {}

    def record(self, *, consumer_id: str, event_id: str, effect_hash: str | None = None) -> bool:
        if not consumer_id or not event_id:
            raise ValueError("consumer_id and event_id are required")
        key = (consumer_id, event_id)
        with self._lock:
            existing = self._records.get(key)
            if existing is not None:
                if existing.effect_hash != effect_hash:
                    raise ValueError("duplicate inbox event has conflicting effect_hash")
                return False
            self._records[key] = InboxRecord(consumer_id, event_id, effect_hash)
            return True

    def processed(self, *, consumer_id: str, event_id: str) -> bool:
        with self._lock:
            return (consumer_id, event_id) in self._records
