import hashlib

import pytest

from src.coordination.session_fabric import (
    EventSurfaceConflict,
    SessionGraphCompiler,
    SessionIdentity,
    Surface,
    SurfaceEvent,
    deduplicate_surface_events,
    reconcile_github_lifecycle,
)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def identity() -> SessionIdentity:
    return SessionIdentity(
        project_id="motion://project/motion-os",
        agent_id="motion://agent/chatgpt/test",
        session_id="motion://session/chatgpt/test/session-1",
        workstream_id="motion://workstream/regression",
        correlation_id="corr-regression-1",
    )


def event(event_id: str, *, causation_id=None, parents=()):
    return {
        "event_id": event_id,
        "event_type": "CHECKPOINT",
        "session_id": identity().session_id,
        "correlation_id": identity().correlation_id,
        "causation_id": causation_id,
        "parent_event_ids": list(parents),
    }


def test_same_logical_fact_across_surfaces_deduplicates():
    payload_hash = _hash("same")
    rows = [
        SurfaceEvent(Surface.GITHUB_BOOTSTRAP, "logical-1", payload_hash, {"x": 1}),
        SurfaceEvent(Surface.REPO_EVENT, "logical-1", payload_hash, {"x": 1}),
        SurfaceEvent(Surface.RUNTIME_EVENTSTORE, "logical-1", payload_hash, {"x": 1}),
    ]
    deduped = deduplicate_surface_events(rows)
    assert len(deduped) == 1


def test_conflicting_duplicate_surface_fact_fails_closed():
    with pytest.raises(EventSurfaceConflict):
        deduplicate_surface_events([
            SurfaceEvent(Surface.GITHUB_BOOTSTRAP, "logical-1", _hash("a"), {"x": 1}),
            SurfaceEvent(Surface.RUNTIME_EVENTSTORE, "logical-1", _hash("b"), {"x": 2}),
        ])


def test_live_github_lifecycle_supersedes_stale_projection():
    projected = {"pr:37": "OPEN", "pr:44": "OPEN_DRAFT"}
    live = {"pr:37": "MERGED", "main:sha": "0de63a1"}
    reconciled = reconcile_github_lifecycle(projected, live)
    assert reconciled["pr:37"] == "MERGED"
    assert reconciled["pr:44"] == "OPEN_DRAFT"
    assert reconciled["main:sha"] == "0de63a1"


def test_non_github_lifecycle_key_cannot_self_promote():
    with pytest.raises(ValueError):
        reconcile_github_lifecycle({}, {"authority:write": "GRANTED"})


def test_session_graph_is_deterministic_and_session_native():
    compiler = SessionGraphCompiler()
    events = [event("e1"), event("e2", causation_id="e1", parents=("e1",))]
    first = compiler.compile(
        identity=identity(),
        live_main_sha="0de63a1e56cd289655c45d0b19796442d406ce83",
        event_watermark=12,
        events=events,
        resources=["contract:coordination-event-v1", "plan:regression"],
        live_lifecycle={"pr:37": "MERGED", "pr:44": "OPEN_DRAFT"},
    )
    second = compiler.compile(
        identity=identity(),
        live_main_sha="0de63a1e56cd289655c45d0b19796442d406ce83",
        event_watermark=12,
        events=events,
        resources=["plan:regression", "contract:coordination-event-v1"],
        live_lifecycle={"pr:44": "OPEN_DRAFT", "pr:37": "MERGED"},
    )
    assert first.projection_hash == second.projection_hash
    assert first.verify_hash()
    assert any(n.node_id == identity().session_id and n.node_type == "Session" for n in first.nodes)
    assert any(e.relation == "AGENT_OPENED_SESSION" for e in first.edges)
    assert any(e.relation == "EVENT_CAUSED_BY" for e in first.edges)


def test_cross_session_event_is_rejected():
    bad = event("e1")
    bad["session_id"] = "motion://session/other"
    with pytest.raises(ValueError, match="cross-session"):
        SessionGraphCompiler().compile(
            identity=identity(),
            live_main_sha="0de63a1",
            event_watermark=1,
            events=[bad],
        )
