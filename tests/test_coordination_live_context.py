from datetime import datetime, timezone

from src.coordination.github_lifecycle import GitHubLifecycleSnapshot, PRLifecycle
from src.coordination.live_context import LiveContextCompiler
from src.coordination.snapshot import CoordinationSnapshot


def bootstrap():
    return CoordinationSnapshot.from_mapping({
        "schema_version": 1,
        "project_id": "motion://project/MOTION.OS",
        "captured_at": "2026-08-27T10:00:00Z",
        "main_sha": "oldmain0",
        "active_prs": [{"number": 34, "branch": "old", "state": "OPEN"}],
        "active_agents": [{"agent_id": "motion://agent/content-avatar", "status": "ACTIVE"}],
        "active_leases": [],
        "tasks": [],
        "decisions": [],
        "contracts": [{"uri": "contract:avatar-handoff", "revision": 2}],
        "conflicts": [],
        "checkpoints": [],
        "release_gates": [],
        "source_refs": [],
        "projection": {"version": 1, "hash": "a" * 64},
    })


def lifecycle():
    return GitHubLifecycleSnapshot.build(
        repository="rotprods/motion-OS",
        main_sha="e77b2aaf01e0c439306aa3374f8c8df6fea0afed",
        prs=[
            {"number": 34, "head": "feat/old", "head_sha": "1" * 40, "base": "main", "state": "closed", "merged": False},
            {"number": 37, "head": "feat/avatar-script-engine", "head_sha": "2" * 40, "base": "main", "state": "open", "draft": True},
            {"number": 42, "head": "fix/remotion-runtime-proof-v2", "head_sha": "3" * 40, "base": "main", "state": "closed", "merged": True},
            {"number": 44, "head": "feat/agentic-coordination-kernel", "head_sha": "4" * 40, "base": "main", "state": "open", "draft": True},
        ],
        supersessions={34: 42},
    )


def test_lifecycle_distinguishes_merged_closed_superseded_and_active():
    snap = lifecycle()
    states = {pr.number: pr.state for pr in snap.prs}
    assert states[34] == PRLifecycle.SUPERSEDED
    assert states[37] == PRLifecycle.OPEN_DRAFT
    assert states[42] == PRLifecycle.MERGED
    assert states[44] == PRLifecycle.OPEN_DRAFT
    assert [pr["number"] for pr in snap.active_prs()] == [37, 44]


def test_live_context_overrides_stale_bootstrap_pr_and_main_state():
    pack = LiveContextCompiler().compile(
        bootstrap=bootstrap(),
        github=lifecycle(),
        agent_id="motion://agent/test",
        session_id="motion://session/test",
        goal_summary="continue safely",
        generated_at=datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc),
        allowed_write_scopes=("phase:07/agentic-coordination",),
        event_watermark=12,
    )
    assert pack.main_sha == "e77b2aaf01e0c439306aa3374f8c8df6fea0afed"
    assert [pr["number"] for pr in pack.active_prs] == [37, 44]
    assert pack.expected_revisions["event:watermark"] == 12
    assert pack.expected_revisions["github:lifecycle"] == lifecycle().revision_hash
    assert pack.verify_seal()


def test_lifecycle_revision_changes_when_pr_head_changes():
    first = lifecycle()
    second = GitHubLifecycleSnapshot.build(
        repository="rotprods/motion-OS",
        main_sha=first.main_sha,
        prs=[
            {"number": 37, "head": "feat/avatar-script-engine", "head_sha": "9" * 40, "base": "main", "state": "open", "draft": True},
        ],
    )
    assert first.revision_hash != second.revision_hash
