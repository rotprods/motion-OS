from datetime import datetime, timezone
import json
from pathlib import Path

from src.coordination.github_lifecycle import GitHubLifecycleSnapshot
from src.coordination.live_context import LiveContextCompiler
from src.coordination.session_fabric import (
    IrreversibleActionPreflight,
    SessionGraphCompiler,
    SessionIdentity,
)
from src.coordination.snapshot import CoordinationSnapshot


MAIN_SHA = "a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d"
SESSION_ID = "motion://session/zero-context/test/session-001"
CORRELATION_ID = "regression-48-zero-context"


def _bootstrap() -> CoordinationSnapshot:
    raw = json.loads(Path("coordination/bootstrap_snapshot.json").read_text(encoding="utf-8"))
    return CoordinationSnapshot.from_mapping(raw)


def _lifecycle() -> GitHubLifecycleSnapshot:
    return GitHubLifecycleSnapshot.build(
        repository="rotprods/motion-OS",
        main_sha=MAIN_SHA,
        prs=[
            {
                "number": 44,
                "head": "feat/agentic-coordination-kernel",
                "head_sha": "a9a5aa865e4becb0b5ab34998f762dd5d9d097c6",
                "base": "main",
                "state": "closed",
                "merged": True,
                "title": "Phase07 kernel",
            },
            {
                "number": 58,
                "head": "feat/session-native-event-fabric-v3",
                "head_sha": "1" * 40,
                "base": "main",
                "state": "open",
                "draft": True,
                "title": "Event fabric v3",
            },
        ],
    )


def _compile_context():
    return LiveContextCompiler().compile(
        bootstrap=_bootstrap(),
        github=_lifecycle(),
        agent_id="motion://agent/zero-context/test",
        session_id=SESSION_ID,
        goal_summary="recover current safe work without chat history",
        generated_at=datetime(2026, 8, 28, 9, 0, tzinfo=timezone.utc),
        ttl_seconds=900,
        allowed_write_scopes=("architecture:canonical-event-fabric",),
        forbidden_write_scopes=("state:canonical-release-truth",),
        event_watermark=42,
    )


def test_zero_context_reconstruction_is_deterministic_and_live_lifecycle_wins():
    first = _compile_context()
    second = _compile_context()

    assert first.verify_seal() and second.verify_seal()
    assert first.seal_sha256 == second.seal_sha256
    assert first.main_sha == MAIN_SHA
    assert first.expected_revisions["git:main"] == MAIN_SHA
    assert first.expected_revisions["event:watermark"] == 42

    # Historical/bootstrap topology cannot resurrect merged #44.
    assert [row["number"] for row in first.active_prs] == [58]
    assert first.active_prs[0]["state"] == "OPEN_DRAFT"


def test_zero_context_session_graph_binds_same_main_watermark_and_causality():
    pack = _compile_context()
    identity = SessionIdentity(
        project_id="motion://project/motion-os",
        agent_id=pack.agent_id,
        session_id=pack.session_id,
        workstream_id="motion://workstream/historical-regression-event-fabric",
        correlation_id=CORRELATION_ID,
    )
    events = [
        {
            "event_id": "evt-zero-1",
            "event_type": "WORK_STARTED",
            "session_id": SESSION_ID,
            "correlation_id": CORRELATION_ID,
            "causation_id": None,
            "parent_event_ids": [],
        },
        {
            "event_id": "evt-zero-2",
            "event_type": "CHECKPOINT",
            "session_id": SESSION_ID,
            "correlation_id": CORRELATION_ID,
            "causation_id": "evt-zero-1",
            "parent_event_ids": ["evt-zero-1"],
        },
    ]
    compiler = SessionGraphCompiler()
    kwargs = dict(
        identity=identity,
        live_main_sha=pack.main_sha,
        event_watermark=int(pack.expected_revisions["event:watermark"]),
        events=events,
        resources=("architecture:canonical-event-fabric",),
        live_lifecycle={"main:sha": MAIN_SHA, "pr:44": "MERGED", "pr:58": "OPEN_DRAFT"},
    )
    first = compiler.compile(**kwargs)
    second = compiler.compile(**kwargs)

    assert first.verify_hash()
    assert first.projection_hash == second.projection_hash
    assert first.live_main_sha == MAIN_SHA
    assert first.event_watermark == 42
    assert any(edge.relation == "EVENT_CAUSED_BY" for edge in first.edges)


def test_zero_context_pack_must_be_invalidated_when_live_authority_advances():
    pack = _compile_context()
    fresh = IrreversibleActionPreflight(
        context_main_sha=pack.main_sha,
        context_event_watermark=int(pack.expected_revisions["event:watermark"]),
        live_main_sha=MAIN_SHA,
        live_event_watermark=42,
    )
    fresh.require_fresh()

    advanced = IrreversibleActionPreflight(
        context_main_sha=pack.main_sha,
        context_event_watermark=int(pack.expected_revisions["event:watermark"]),
        live_main_sha="b" * 40,
        live_event_watermark=43,
    )
    assert not advanced.fresh
    assert advanced.reasons == ("main_sha_advanced", "event_watermark_advanced")
