from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from .events import CoordinationEvent
from .inbox import ReferenceInbox


@dataclass(frozen=True, slots=True)
class QuarantinedEvent:
    consumer_id: str
    event_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class DeliveryOutcome:
    event_id: str
    applied: bool
    duplicate: bool
    quarantined: bool


class ReferenceDeliveryProcessor:
    """At-least-once reference consumer with inbox + poison quarantine.

    Unknown event types and handler failures are not acknowledged as successful
    effects. This is a semantic oracle for P5 qualification, not a distributed
    queue implementation.
    """

    authority_level = "REFERENCE_TEST_ONLY"

    def __init__(self, *, consumer_id: str, handlers: Mapping[str, Callable[[CoordinationEvent], str]]) -> None:
        if not consumer_id:
            raise ValueError("consumer_id is required")
        self.consumer_id = consumer_id
        self.handlers = dict(handlers)
        self.inbox = ReferenceInbox()
        self._quarantine: dict[str, QuarantinedEvent] = {}

    def process(self, event: CoordinationEvent) -> DeliveryOutcome:
        if self.inbox.processed(consumer_id=self.consumer_id, event_id=event.event_id):
            return DeliveryOutcome(event.event_id, applied=False, duplicate=True, quarantined=False)

        handler = self.handlers.get(event.event_type)
        if handler is None:
            self._quarantine[event.event_id] = QuarantinedEvent(
                self.consumer_id, event.event_id, f"unknown event type: {event.event_type}"
            )
            return DeliveryOutcome(event.event_id, applied=False, duplicate=False, quarantined=True)

        try:
            effect_hash = handler(event)
            if not effect_hash:
                raise ValueError("handler must return non-empty effect_hash")
        except Exception as exc:
            self._quarantine[event.event_id] = QuarantinedEvent(
                self.consumer_id, event.event_id, f"handler failure: {type(exc).__name__}"
            )
            return DeliveryOutcome(event.event_id, applied=False, duplicate=False, quarantined=True)

        applied = self.inbox.record(
            consumer_id=self.consumer_id,
            event_id=event.event_id,
            effect_hash=effect_hash,
        )
        self._quarantine.pop(event.event_id, None)
        return DeliveryOutcome(event.event_id, applied=applied, duplicate=not applied, quarantined=False)

    def quarantine(self) -> tuple[QuarantinedEvent, ...]:
        return tuple(self._quarantine[key] for key in sorted(self._quarantine))

    def retry_quarantined(self, event: CoordinationEvent) -> DeliveryOutcome:
        if event.event_id not in self._quarantine:
            raise ValueError("event is not quarantined")
        return self.process(event)
