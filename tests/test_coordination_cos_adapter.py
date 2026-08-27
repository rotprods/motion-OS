from src.coordination.cos_adapter import COS_BASELINE_COMMIT, CosShadowAdapter
from src.coordination.events import CoordinationEvent, ProvenanceRef
from src.coordination.projection import CoordinationGraphProjector


def event(event_type: str, aggregate_type: str, aggregate_id: str, revision: int, idem: str, payload=None, workstream_id=None):
    return CoordinationEvent(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        aggregate_revision=revision,
        expected_revision=revision - 1,
        project_id="motion://project/MOTION.OS",
        agent_id="motion://agent/test",
        session_id="motion://session/test",
        correlation_id="motion://work/test",
        idempotency_key=idem,
        payload=payload or {},
        provenance=(ProvenanceRef("test", "cos-adapter"),),
        workstream_id=workstream_id,
    )


def test_cos_shadow_bundle_is_pinned_deterministic_and_hash_verified():
    events = [
        event("TASK_STARTED", "task", "motion://task/t1", 1, "idem-1", {"task_uri": "motion://task/t1"}, "motion://workstream/w1"),
    ]
    projection = CoordinationGraphProjector().build(events, projection_version=1)
    adapter = CosShadowAdapter()
    first = adapter.compile_bundle(projection)
    second = adapter.compile_bundle(projection)
    assert first.bundle_hash == second.bundle_hash
    assert first.verify_hash()
    assert first.cos_baseline_commit == COS_BASELINE_COMMIT
    assert first.level15_workflow["enabled"] is False
    assert first.source_projection_hash == projection.projection_hash


def test_cos_bundle_preserves_motion_uri_as_authoritative_identity_metadata():
    projection = CoordinationGraphProjector().build([
        event("TASK_STARTED", "task", "motion://task/t1", 1, "idem-1", {"task_uri": "motion://task/t1"}, "motion://workstream/w1"),
    ], projection_version=1)
    bundle = CosShadowAdapter().compile_bundle(projection)
    agent_uris = {item["motion_uri"] for item in bundle.level13_agent["agents"]}
    assert "motion://agent/test" in agent_uris
    assert bundle.generic_graph["projection_hash"] == projection.projection_hash
