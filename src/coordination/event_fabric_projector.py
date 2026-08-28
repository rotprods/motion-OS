from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from .event_store import StoredEvent
from .session_fabric import (
    EventSurfaceConflict,
    Surface,
    SurfaceEvent,
    deduplicate_surface_events,
    reconcile_github_lifecycle,
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class EventFabricProjectionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CanonicalFabricEvent:
    logical_id: str
    payload_hash: str
    event: Mapping[str, Any]
    observed_surfaces: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EventFabricSnapshot:
    live_main_sha: str
    runtime_watermark: int
    surface_coverage: tuple[str, ...]
    events: tuple[CanonicalFabricEvent, ...]
    live_lifecycle: tuple[tuple[str, str], ...]
    projection_hash: str

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "live_main_sha": self.live_main_sha,
            "runtime_watermark": self.runtime_watermark,
            "surface_coverage": list(self.surface_coverage),
            "events": [
                {
                    "logical_id": event.logical_id,
                    "payload_hash": event.payload_hash,
                    "event": dict(event.event),
                    "observed_surfaces": list(event.observed_surfaces),
                }
                for event in self.events
            ],
            "live_lifecycle": [list(item) for item in self.live_lifecycle],
        }

    def verify_hash(self) -> bool:
        return _sha256(self.canonical_payload()) == self.projection_hash


class CanonicalEventFabricProjector:
    """Read-only convergence projector for the three coordination surfaces.

    The projector grants no mutation authority. It proves that bootstrap GitHub
    events, immutable repo events and runtime EventStore observations can be
    reduced to one deterministic event set. Identical logical events deduplicate;
    conflicting representations fail closed. Live GitHub lifecycle is applied
    separately and supersedes stale historical lifecycle projections.
    """

    REQUIRED_SURFACES = frozenset({
        Surface.GITHUB_BOOTSTRAP,
        Surface.REPO_EVENT,
        Surface.RUNTIME_EVENTSTORE,
    })

    def project(
        self,
        *,
        live_main_sha: str,
        runtime_watermark: int,
        surface_events: Iterable[SurfaceEvent],
        live_lifecycle: Mapping[str, str] | None = None,
        require_all_surfaces: bool = False,
    ) -> EventFabricSnapshot:
        if len(live_main_sha) < 7:
            raise EventFabricProjectionError("live_main_sha required")
        if runtime_watermark < 0:
            raise EventFabricProjectionError("runtime_watermark must be >= 0")

        observed = tuple(surface_events)
        coverage = frozenset(item.surface for item in observed)
        if require_all_surfaces:
            missing = self.REQUIRED_SURFACES - coverage
            if missing:
                names = ",".join(sorted(item.value for item in missing))
                raise EventFabricProjectionError(f"missing required event surfaces: {names}")

        # Validate any runtime sequence evidence before deduplication. Sequence IDs
        # are adapter metadata rather than canonical event identity.
        max_runtime_sequence = 0
        for item in observed:
            if item.surface is not Surface.RUNTIME_EVENTSTORE:
                continue
            sequence = item.event.get("_runtime_sequence_id")
            if sequence is None:
                continue
            if not isinstance(sequence, int) or sequence < 1:
                raise EventFabricProjectionError("invalid runtime sequence id")
            max_runtime_sequence = max(max_runtime_sequence, sequence)
        if runtime_watermark < max_runtime_sequence:
            raise EventFabricProjectionError(
                "runtime watermark is behind observed runtime event sequence"
            )

        # SurfaceEvent itself verifies each declared payload hash. This call then
        # rejects cross-surface logical-ID conflicts.
        deduped = deduplicate_surface_events(observed)

        surfaces_by_id: dict[str, set[str]] = {}
        for item in observed:
            surfaces_by_id.setdefault(item.logical_id, set()).add(item.surface.value)

        canonical_events = tuple(
            CanonicalFabricEvent(
                logical_id=item.logical_id,
                payload_hash=item.payload_hash,
                event=dict(item.event),
                observed_surfaces=tuple(sorted(surfaces_by_id[item.logical_id])),
            )
            for item in deduped
        )

        lifecycle = reconcile_github_lifecycle({}, live_lifecycle or {})
        surface_coverage = tuple(sorted(item.value for item in coverage))
        snapshot_payload = {
            "live_main_sha": live_main_sha,
            "runtime_watermark": runtime_watermark,
            "surface_coverage": list(surface_coverage),
            "events": [
                {
                    "logical_id": event.logical_id,
                    "payload_hash": event.payload_hash,
                    "event": dict(event.event),
                    "observed_surfaces": list(event.observed_surfaces),
                }
                for event in canonical_events
            ],
            "live_lifecycle": [list(item) for item in sorted(lifecycle.items())],
        }
        return EventFabricSnapshot(
            live_main_sha=live_main_sha,
            runtime_watermark=runtime_watermark,
            surface_coverage=surface_coverage,
            events=canonical_events,
            live_lifecycle=tuple(sorted(lifecycle.items())),
            projection_hash=_sha256(snapshot_payload),
        )


def surface_event_from_runtime(stored: StoredEvent) -> SurfaceEvent:
    """Adapt a runtime StoredEvent without changing its canonical event payload.

    Runtime sequence is included as explicit adapter evidence so the projector can
    prove the supplied watermark is not behind observed runtime state.
    """
    payload = stored.event.to_dict()
    payload["_runtime_sequence_id"] = stored.sequence_id
    return SurfaceEvent.create(
        Surface.RUNTIME_EVENTSTORE,
        stored.event.event_id,
        payload,
    )


def surface_event_from_mapping(
    surface: Surface,
    event: Mapping[str, Any],
    *,
    logical_id_key: str = "event_id",
) -> SurfaceEvent:
    logical_id = event.get(logical_id_key)
    if not isinstance(logical_id, str) or not logical_id:
        raise EventFabricProjectionError(f"missing logical event identity: {logical_id_key}")
    return SurfaceEvent.create(surface, logical_id, dict(event))
