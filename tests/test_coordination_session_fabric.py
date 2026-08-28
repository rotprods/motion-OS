import hashlib
import pytest

from src.coordination.session_fabric import (
    EventSurfaceConflict, SessionGraphCompiler, SessionIdentity, Surface, SurfaceEvent,
    deduplicate_surface_events, reconcile_github_lifecycle,
)

def _hash_mapping(value: dict) -> str:
    import json
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def ident() -> SessionIdentity:
    return SessionIdentity(
        project_id="motion://project/motion-os",
        agent_id="motion://agent/chatgpt/test",
        session_id="motion://session/chatgpt/test/session-1",
        workstream_id="motion://workstream/regression",
        correlation_id="corr-1",
    )

def evt(event_id: str, **extra):
    out = {"event_id": event_id, "event_type": "CHECKPOINT", "session_id": ident().session_id,
           "correlation_id": ident().correlation_id, "causation_id": None, "parent_event_ids": []}
    out.update(extra)
    return out

def test_same_logical_fact_across_surfaces_deduplicates():
    rows = [SurfaceEvent.create(s, "logical-1", {"x": 1}) for s in Surface]
    assert len(deduplicate_surface_events(rows)) == 1

def test_conflicting_surface_duplicate_fails_closed():
    with pytest.raises(EventSurfaceConflict):
        deduplicate_surface_events([
            SurfaceEvent.create(Surface.GITHUB_BOOTSTRAP, "logical-1", {"x": 1}),
            SurfaceEvent.create(Surface.RUNTIME_EVENTSTORE, "logical-1", {"x": 2}),
        ])

def test_surface_event_rejects_forged_payload_hash():
    with pytest.raises(ValueError, match="does not match"):
        SurfaceEvent(Surface.REPO_EVENT, "logical-1", "0" * 64, {"x": 1})

def test_live_github_supersedes_stale_projection():
    result = reconcile_github_lifecycle({"pr:37": "OPEN", "pr:44": "OPEN_DRAFT"},
                                        {"pr:37": "MERGED", "main:sha": "080dfd5"})
    assert result["pr:37"] == "MERGED"
    assert result["pr:44"] == "OPEN_DRAFT"

def test_non_lifecycle_live_key_cannot_promote_authority():
    with pytest.raises(ValueError):
        reconcile_github_lifecycle({}, {"authority:write": "GRANTED"})

def test_session_graph_is_deterministic():
    compiler = SessionGraphCompiler()
    events = [evt("e1"), evt("e2", causation_id="e1", parent_event_ids=["e1"])]
    kwargs = dict(identity=ident(), live_main_sha="080dfd5c16bc06100edd716eadc770530dc47af2",
                  event_watermark=12, events=events,
                  resources=["contract:coordination-event-v1", "plan:regression"],
                  live_lifecycle={"pr:44": "MERGED", "main:sha": "080dfd5"})
    a = compiler.compile(**kwargs)
    b = compiler.compile(**kwargs)
    assert a.projection_hash == b.projection_hash and a.verify_hash()
    assert any(n.node_id == ident().session_id and n.node_type == "Session" for n in a.nodes)
    assert any(e.relation == "EVENT_CAUSED_BY" for e in a.edges)

def test_cross_session_and_cross_correlation_events_are_rejected():
    with pytest.raises(ValueError, match="cross-session"):
        SessionGraphCompiler().compile(identity=ident(), live_main_sha="080dfd5", event_watermark=1,
                                       events=[evt("e1", session_id="motion://session/other")])
    with pytest.raises(ValueError, match="cross-correlation"):
        SessionGraphCompiler().compile(identity=ident(), live_main_sha="080dfd5", event_watermark=1,
                                       events=[evt("e1", correlation_id="corr-other")])

def test_duplicate_event_id_and_parent_ids_are_rejected():
    with pytest.raises(ValueError, match="duplicate event_id"):
        SessionGraphCompiler().compile(identity=ident(), live_main_sha="080dfd5", event_watermark=2,
                                       events=[evt("e1"), evt("e1")])
    with pytest.raises(ValueError, match="duplicate parent_event_ids"):
        SessionGraphCompiler().compile(identity=ident(), live_main_sha="080dfd5", event_watermark=1,
                                       events=[evt("e2", parent_event_ids=["e1", "e1"])])
