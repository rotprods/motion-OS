from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from .event_store import StoredEvent
from .session_fabric import (
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
class RuntimeObservation:
    event: SurfaceEvent
    sequence_id: int

    def __post_init__(self) -> None:
        if self.event.surface is not Surface.RUNTIME_EVENTSTORE:
            raise ValueError("runtime observation must carry a runtime surface event")
        if self.sequence_id < 1:
            raise ValueError("runtime sequence_id must be >= 1")


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
    conflicting representations fail closed. Transport metadata (for example a
    runtime sequence number) is never mixed into canonical event identity. Live
    GitHub lifecycle is applied separately and supersedes stale historical facts.
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
        runtime_observations: Sequence[RuntimeObservation] = (),
        live_lifecycle: Mapping[str, str] | None = None,
        require_all_surfaces: bool = False,
    ) -> EventFabricSnapshot:
        if len(live_main_sha) < 7:
            raise EventFabricProjectionError("live_main_sha required")
        if runtime_watermark < 0:
            raise EventFabricProjectionError("runtime_watermark must be >= 0")

        external_events = tuple(surface_events)
        if any(item.surface is Surface.RUNTIME_EVENTSTORE for item in external_events):
            raise EventFabricProjectionError(
                "runtime surface events require RuntimeObservation sequence evidence"
            )

        observed = list(external_events)
        observed.extend(item.event for item in runtime_observations)
        observed_tuple = tuple(observed)
        coverage = frozenset(item.surface for item in observed_tuple)
        if require_all_surfaces:
            missing = self.REQUIRED_SURFACES - coverage
            if missing:
                names = ",".join(sorted(item.value for item in missing))
                raise EventFabricProjectionError(f"missing required event surfaces: {names}")

        if runtime_observations:
            max_runtime_sequence = max(item.sequence_id for item in runtime_observations)
            if runtime_watermark < max_runtime_sequence:
                raise EventFabricProjectionError(
                    "runtime watermark is behind observed runtime event sequence"
                )

        deduped = deduplicate_surface_events(observed_tuple)

        surfaces_by_id: dict[str, set[str]] = {}
        for item in observed_tuple:
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


def runtime_observation_from_stored(stored: StoredEvent) -> RuntimeObservation:
    # The canonical CoordinationEvent payload is unchanged. sequence_id remains
    # transport/store metadata so an identical repo event can deduplicate with it.
    event = SurfaceEvent.create(
        Surface.RUNTIME_EVENTSTORE,
        stored.event.event_id,
        stored.event.to_dict(),
    )
    return RuntimeObservation(event=event, sequence_id=stored.sequence_id)


def surface_event_from_mapping(
    surface: Surface,
    event: Mapping[str, Any],
    *,
    logical_id_key: str = "event_id",
) -> SurfaceEvent:
    if surface is Surface.RUNTIME_EVENTSTORE:
        raise EventFabricProjectionError(
            "runtime mappings must use runtime_observation_from_stored()"
        )
    logical_id = event.get(logical_id_key)
    if not isinstance(logical_id, str) or not logical_id:
        raise EventFabricProjectionError(f"missing logical event identity: {logical_id_key}")
    return SurfaceEvent.create(surface, logical_id, dict(event))
