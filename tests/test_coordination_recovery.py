from dataclasses import replace

import pytest

from src.coordination.events import CoordinationEvent, ProvenanceRef
from src.coordination.github_lifecycle import GitHubLifecycleSnapshot
from src.coordination.recovery import (
    ColdRecoveryVerifier,
    RecoveryError,
    RecoverySourceStatus,
)
from src.coordination.replay import ReplayVerifier


MAIN = "a" * 40
EVENT_TIME = "2026-08-28T11:00:00Z"


def _event(*, event_id: str, revision: int, expected: int, payload: dict) -> CoordinationEvent:
    return CoordinationEvent(
        event_id=event_id,
        event_type="WORK_CHECKPOINTED",
        aggregate_type="workstream",
        aggregate_id="recovery-test",
        aggregate_revision=revision,
        expected_revision=expected,
        project_id="motion://project/motion-os",
        agent_id="motion://agent/chatgpt/recovery-test",
        session_id="motion://session/chatgpt/recovery-test/1",
        workstream_id="motion://workstream/recovery-test",
        correlation_id="recovery-test",
        idempotency_key=f"idem-{revision}",
        payload=payload,
        provenance=(ProvenanceRef("git", "main", revision=MAIN),),
        occurred_at=EVENT_TIME,
        recorded_at=EVENT_TIME,
    )


def _events() -> tuple[CoordinationEvent, ...]:
    return (
        _event(
            event_id="11111111-1111-4111-8111-111111111111",
            revision=1,
            expected=0,
            payload={"status": "STARTED"},
        ),
        _event(
            event_id="22222222-2222-4222-8222-222222222222",
            revision=2,
            expected=1,
            payload={"status": "VERIFIED"},
        ),
    )


def _github(main_sha: str = MAIN) -> GitHubLifecycleSnapshot:
    return GitHubLifecycleSnapshot.build(
        repository="rotprods/motion-OS",
        main_sha=main_sha,
        prs=(
            {
                "number": 58,
                "head": "feat/session-native-event-fabric-v3",
                "head_sha": "b" * 40,
                "base": "main",
                "state": "open",
                "draft": True,
                "title": "event fabric",
            },
        ),
    )


def test_cold_recovery_is_deterministic_and_binds_live_github():
    verifier = ColdRecoveryVerifier()
    events = _events()
    first = verifier.rebuild(events=events, github=_github())
    second = verifier.rebuild(events=events, github=_github())

    assert verifier.equivalent(first, second)
    assert first.verify_hash()
    assert first.live_main_sha == MAIN
    assert first.event_watermark == 2
    assert first.authority == "RECOVERED"
    assert first.degraded_sources == ()


def test_drive_outage_is_explicit_degraded_not_fabricated_authority():
    drive = RecoverySourceStatus(
        source="drive:artifact-recovery",
        required=False,
        available=False,
        reason="connector unavailable during cold restore",
    )
    report = ColdRecoveryVerifier().rebuild(
        events=_events(),
        github=_github(),
        auxiliary_sources=(drive,),
    )

    assert report.authority == "RECOVERED_DEGRADED"
    assert report.degraded_sources == ("drive:artifact-recovery",)
    assert report.verify_hash()


def test_live_main_change_changes_recovery_identity():
    verifier = ColdRecoveryVerifier()
    events = _events()
    before = verifier.rebuild(events=events, github=_github("a" * 40))
    after = verifier.rebuild(events=events, github=_github("c" * 40))

    assert before.live_main_sha != after.live_main_sha
    assert before.lifecycle_revision != after.lifecycle_revision
    assert before.report_hash != after.report_hash
    assert not verifier.equivalent(before, after)


def test_empty_event_history_fails_closed():
    with pytest.raises(RecoveryError, match="immutable event history"):
        ColdRecoveryVerifier().rebuild(events=(), github=_github())


def test_available_aux_source_requires_evidence_identity():
    with pytest.raises(ValueError, match="requires revision"):
        RecoverySourceStatus(
            source="drive:artifact-recovery",
            required=False,
            available=True,
        )


def test_report_detects_tampering_and_replay_mismatch():
    verifier = ColdRecoveryVerifier()
    events = _events()
    report = verifier.rebuild(events=events, github=_github())
    replay = ReplayVerifier().rebuild(events)
    verifier.verify_against_replay(report, replay)

    tampered_report = replace(report, replay_graph_hash="0" * 64)
    assert not tampered_report.verify_hash()
    with pytest.raises(RecoveryError, match="graph hash"):
        verifier.verify_against_replay(tampered_report, replay)


def test_unexpected_repository_fails_closed():
    github = GitHubLifecycleSnapshot.build(
        repository="rotprods/other",
        main_sha=MAIN,
        prs=(),
    )
    with pytest.raises(RecoveryError, match="unexpected recovery repository"):
        ColdRecoveryVerifier().rebuild(events=_events(), github=github)
