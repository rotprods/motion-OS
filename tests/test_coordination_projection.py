from src.coordination.events import CoordinationEvent, ProvenanceRef
from src.coordination.projection import CoordinationGraphProjector


def event(event_type: str, aggregate_type: str, aggregate_id: str, correlation_id: str, payload=None, **kwargs):
    return CoordinationEvent(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        aggregate_revision=kwargs.pop("aggregate_revision", 1),
        expected_revision=kwargs.pop("expected_revision", 0),
        project_id="motion://project/MOTION.OS",
        agent_id="motion://agent/a",
        session_id="motion://session/a",
        correlation_id=correlation_id,
        idempotency_key=kwargs.pop("idempotency_key", f"idem-{correlation_id}-{event_type}"),
        payload=payload or {},
        provenance=(ProvenanceRef("test", "fixture:projection"),),
        **kwargs,
    )


def test_same_event_sequence_rebuilds_same_projection_hash():
    events = [
        event("TASK_STARTED", "task", "motion://task/t1", "c1", {"task_uri": "motion://task/t1"}),
        event("WORK_CLAIMED", "lease", "lease-1", "c2", {
            "resource_uri": "contract:avatar-handoff",
            "lease_id": "lease-1",
            "fencing_token": 4,
        }),
    ]
    projector = CoordinationGraphProjector()
    a = projector.build(events, projection_version=1)
    b = projector.build(events, projection_version=1)
    assert a.projection_hash == b.projection_hash
    assert a.verify_hash()
    assert b.verify_hash()


def test_projection_contains_agent_session_task_and_lease_relations():
    events = [
        event("TASK_STARTED", "task", "motion://task/t1", "c1", {"task_uri": "motion://task/t1"}),
        event("WORK_CLAIMED", "lease", "lease-1", "c2", {
            "resource_uri": "contract:avatar-handoff",
            "lease_id": "lease-1",
            "fencing_token": 2,
        }),
    ]
    snapshot = CoordinationGraphProjector().build(events, projection_version=3)
    relations = {(x.source, x.relation, x.target) for x in snapshot.edges}
    assert ("motion://session/a", "RUN_BY", "motion://agent/a") in relations
    assert ("motion://agent/a", "EXECUTES", "motion://task/t1") in relations
    assert ("motion://agent/a", "OWNS_LEASE", "contract:avatar-handoff") in relations


def test_git_metadata_projects_pr_branch_and_commit():
    e = event(
        "CHECKPOINT_EMITTED", "checkpoint", "cp-1", "c1",
        git={
            "repository": "rotprods/motion-OS",
            "branch": "feat/x",
            "sha": "abc1234",
            "pr_number": 44,
        },
    )
    snapshot = CoordinationGraphProjector().build([e], projection_version=1)
    node_ids = {x.node_id for x in snapshot.nodes}
    assert "motion://repo/rotprods/motion-OS/pr/44" in node_ids
    assert "motion://repo/rotprods/motion-OS/branch/feat/x" in node_ids
    assert "motion://repo/rotprods/motion-OS/commit/abc1234" in node_ids


def test_parent_events_workstream_and_resource_scope_are_projected():
    parent = event("TASK_STARTED", "task", "motion://task/t1", "root")
    child = event(
        "CHECKPOINT_EMITTED",
        "checkpoint",
        "cp-1",
        "root",
        parent_event_ids=(parent.event_id,),
        workstream_id="motion://workstream/phase07",
        resource_scope=("contract:coordination-event",),
    )
    snapshot = CoordinationGraphProjector().build([parent, child], projection_version=1)
    relations = {(x.source, x.relation, x.target) for x in snapshot.edges}
    child_uri = f"motion://event/{child.event_id}"
    parent_uri = f"motion://event/{parent.event_id}"
    assert (child_uri, "CAUSED_BY", parent_uri) in relations
    assert (child_uri, "IN_WORKSTREAM", "motion://workstream/phase07") in relations
    assert (child_uri, "TOUCHES", "contract:coordination-event") in relations
