from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .conflicts import ConflictFinding, ConflictClass
from .event_store import InMemoryReferenceEventStore
from .leases import ReferenceLeaseAuthority


@dataclass(frozen=True, slots=True)
class CoordinationHealth:
    event_watermark: int
    active_leases: int
    unresolved_conflicts: int
    blocked_conflicts: int
    stale_writer_rejections: int
    context_invalidations: int
    replay_failures: int
    duplicate_deliveries: int

    @property
    def healthy(self) -> bool:
        return self.replay_failures == 0 and self.stale_writer_rejections >= 0


class CoordinationMetrics:
    """Provider-neutral counters; telemetry must never change protected outcomes."""

    def __init__(self) -> None:
        self.stale_writer_rejections = 0
        self.context_invalidations = 0
        self.replay_failures = 0
        self.duplicate_deliveries = 0

    def stale_writer_rejected(self) -> None:
        self.stale_writer_rejections += 1

    def context_invalidated(self) -> None:
        self.context_invalidations += 1

    def replay_failed(self) -> None:
        self.replay_failures += 1

    def duplicate_delivery(self) -> None:
        self.duplicate_deliveries += 1

    def snapshot(
        self,
        *,
        event_store: InMemoryReferenceEventStore,
        lease_authority: ReferenceLeaseAuthority,
        conflicts: Iterable[ConflictFinding] = (),
    ) -> CoordinationHealth:
        findings = tuple(conflicts)
        return CoordinationHealth(
            event_watermark=event_store.watermark(),
            active_leases=len(lease_authority.active()),
            unresolved_conflicts=sum(item.classification != ConflictClass.NONE for item in findings),
            blocked_conflicts=sum(item.blocked for item in findings),
            stale_writer_rejections=self.stale_writer_rejections,
            context_invalidations=self.context_invalidations,
            replay_failures=self.replay_failures,
            duplicate_deliveries=self.duplicate_deliveries,
        )
