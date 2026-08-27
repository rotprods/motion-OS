from src.coordination.operator_status import OperatorStatusCompiler


def test_operator_status_is_deterministic_and_sealed():
    compiler = OperatorStatusCompiler()
    kwargs = dict(
        project_id="motion://project/MOTION.OS",
        main_sha="abcdef1234567890",
        event_watermark=12,
        health={"healthy": True, "active_leases": 1},
        active_work=({"work_id": "w2"}, {"work_id": "w1"}),
        conflicts=({"class": "SEMANTIC_OVERLAP", "resource": "contract:x"},),
        next_actions=({"priority": 1, "action": "resolve conflict"},),
        traces=(
            {"event_id": "evt-1", "content_id": "CNT_001", "work_id": "w1"},
            {"event_id": "evt-2", "content_id": "CNT_002", "work_id": "w2"},
        ),
    )
    a = compiler.compile(**kwargs)
    b = compiler.compile(**kwargs)
    assert a.verify()
    assert a == b
    assert a.snapshot_sha256 == b.snapshot_sha256


def test_trace_lookup_connects_content_work_and_event_identifiers():
    snapshot = OperatorStatusCompiler().compile(
        project_id="motion://project/MOTION.OS",
        main_sha="abcdef1234567890",
        event_watermark=1,
        health={"healthy": True},
        traces=(
            {"event_id": "evt-1", "content_id": "CNT_001", "work_id": "work-A"},
            {"event_id": "evt-2", "content_id": "CNT_002", "work_id": "work-B"},
        ),
    )
    assert len(snapshot.trace("CNT_001")) == 1
    assert snapshot.trace("work-A")[0]["event_id"] == "evt-1"
    assert snapshot.trace("missing") == ()


def test_operator_snapshot_rejects_noncanonical_project_and_negative_watermark():
    compiler = OperatorStatusCompiler()
    try:
        compiler.compile(project_id="bad", main_sha="abcdef1", event_watermark=0, health={})
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    try:
        compiler.compile(project_id="motion://project/x", main_sha="abcdef1", event_watermark=-1, health={})
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
