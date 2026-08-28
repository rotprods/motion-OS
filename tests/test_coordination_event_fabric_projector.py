from dataclasses import replace

import pytest

from src.coordination.event_fabric_projector import (
    CanonicalEventFabricProjector,
    EventFabricProjectionError,
    surface_event_from_mapping,
    surface_event_from_runtime,
)
from src.coordination.event_store import InMemoryReferenceEventStore
from src.coordination.events import CoordinationEvent, ProvenanceRef
from src.coordination.session_fabric import EventSurfaceConflict, Surface, SurfaceEvent


MAIN = "a" * 40
SESSION = "motion://session/chatgpt/test/session-1"


def _bootstrap_event(event_id: str = "evt-shared") -> dict:
    return {
        "event_id": event_id,
        "event_type": "CHECKPOINT",
        "project_id": "motion://project/motion-os",
        "agent_id": "motion://agent/chatgpt/test",
        "session_id": SESSION,
        "workstream_id": "motion://workstream/test",
        "correlation_id": "corr-1",
        "summary": "same logical checkpoint",
    }


def _runtime_event() -> CoordinationEvent:
    return CoordinationEvent(
        event_id="11111111-1111-4111-8111-111111111111",
        event_type="WORK_CHECKPOINTED",
        aggregate_type="workstream",
        aggregate_id="test",
        aggregate_revision=1,
        expected_revision=0,
        project_id="motion://project/motion-os",
        agent_id="motion://agent/chatgpt/test",
        session_id=SESSION,
        workstream_id="motion://workstream/test",
        correlation_id="corr-runtime",
        idempotency_key="idem-runtime-1",
        payload={"status": "VERIFIED"},
        provenance=(ProvenanceRef("git", "main", revision=MAIN),),
    )


def test_three_surfaces_project_to_one_deterministic_snapshot():
    shared = _bootstrap_event()
    github = surface_event_from_mapping(Surface.GITHUB_BOOTSTRAP, shared)
    repo = surface_event_from_mapping(Surface.REPO_EVENT, shared)

    store = InMemoryReferenceEventStore()
    stored = store.append(_runtime_event())
    runtime = surface_event_from_runtime(stored)

    projector = CanonicalEventFabricProjector()
    first = projector.project(
        live_main_sha=MAIN,
        runtime_watermark=store.watermark(),
        surface_events=[repo, runtime, github],
        live_lifecycle={"main:sha": MAIN, "pr:58": "OPEN_DRAFT"},
        require_all_surfaces=True,
    )
    second = projector.project(
        live_main_sha=MAIN,
        runtime_watermark=store.watermark(),
        surface_events=[github, repo, runtime],
        live_lifecycle={"pr:58": "OPEN_DRAFT", "main:sha": MAIN},
        require_all_surfaces=True,
    )

    assert first == second
    assert first.verify_hash()
    assert first.surface_coverage == (
        "GITHUB_BOOTSTRAP",
        "REPO_EVENT",
        "RUNTIME_EVENTSTORE",
    )
    # The identical GitHub/repo logical event is represented once, with both
    # observations retained as evidence; runtime is a distinct logical event.
    assert len(first.events) == 2
    shared_projection = next(event for event in first.events if event.logical_id == "evt-shared")
    assert shared_projection.observed_surfaces == ("GITHUB_BOOTSTRAP", "REPO_EVENT")


def test_conflicting_cross_surface_duplicate_fails_closed():
    original = _bootstrap_event()
    mutated = dict(original)
    mutated["summary"] = "different payload"

    with pytest.raises(EventSurfaceConflict):
        CanonicalEventFabricProjector().project(
            live_main_sha=MAIN,
            runtime_watermark=0,
            surface_events=[
                surface_event_from_mapping(Surface.GITHUB_BOOTSTRAP, original),
                surface_event_from_mapping(Surface.REPO_EVENT, mutated),
            ],
        )


def test_all_surface_qualification_rejects_missing_adapter():
    with pytest.raises(EventFabricProjectionError, match="missing required event surfaces"):
        CanonicalEventFabricProjector().project(
            live_main_sha=MAIN,
            runtime_watermark=0,
            surface_events=[
                surface_event_from_mapping(Surface.GITHUB_BOOTSTRAP, _bootstrap_event()),
                surface_event_from_mapping(Surface.REPO_EVENT, _bootstrap_event()),
            ],
            require_all_surfaces=True,
        )


def test_runtime_watermark_cannot_be_behind_observed_runtime_sequence():
    store = InMemoryReferenceEventStore()
    runtime = surface_event_from_runtime(store.append(_runtime_event()))
    with pytest.raises(EventFabricProjectionError, match="watermark is behind"):
        CanonicalEventFabricProjector().project(
            live_main_sha=MAIN,
            runtime_watermark=0,
            surface_events=[runtime],
        )


def test_live_github_lifecycle_is_separate_authoritative_overlay():
    snapshot = CanonicalEventFabricProjector().project(
        live_main_sha=MAIN,
        runtime_watermark=0,
        surface_events=[],
        live_lifecycle={"pr:44": "MERGED", "main:sha": MAIN},
    )
    assert dict(snapshot.live_lifecycle) == {"main:sha": MAIN, "pr:44": "MERGED"}


def test_adapter_declared_hash_is_recomputed_and_tampering_rejected():
    event = _bootstrap_event()
    valid = surface_event_from_mapping(Surface.GITHUB_BOOTSTRAP, event)
    with pytest.raises(ValueError, match="payload_hash does not match"):
        SurfaceEvent(
            surface=valid.surface,
            logical_id=valid.logical_id,
            payload_hash=valid.payload_hash,
            event={**event, "summary": "tampered after hashing"},
        )
