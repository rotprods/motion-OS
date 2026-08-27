from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .cos_adapter import CosShadowAdapter
from .event_store import InMemoryReferenceEventStore, StateSnapshot
from .events import CoordinationEvent
from .projection import CoordinationGraphProjector, ProjectionSnapshot


@dataclass(frozen=True, slots=True)
class ReplayResult:
    state_snapshot: StateSnapshot
    graph_snapshot: ProjectionSnapshot
    cos_bundle_hash: str


class ReplayVerifier:
    """Cold-rebuild reference verifier from immutable event history only."""

    def rebuild(self, events: Iterable[CoordinationEvent], *, projection_version: int = 1) -> ReplayResult:
        ordered = tuple(events)
        store = InMemoryReferenceEventStore()
        for event in ordered:
            stored = store.append(event)
            if stored.duplicate:
                raise ValueError("replay history contains duplicate logical event")
        state = store.snapshot()
        graph = CoordinationGraphProjector().build(ordered, projection_version=projection_version)
        bundle = CosShadowAdapter().compile_bundle(graph)
        return ReplayResult(state_snapshot=state, graph_snapshot=graph, cos_bundle_hash=bundle.bundle_hash)

    def equivalent(self, left: ReplayResult, right: ReplayResult) -> bool:
        return (
            left.state_snapshot.state_hash == right.state_snapshot.state_hash
            and left.state_snapshot.event_watermark == right.state_snapshot.event_watermark
            and left.graph_snapshot.projection_hash == right.graph_snapshot.projection_hash
            and left.cos_bundle_hash == right.cos_bundle_hash
        )
