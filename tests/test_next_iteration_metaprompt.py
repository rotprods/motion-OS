import copy

import pytest

from scripts.next_iteration_metaprompt import (
    NextIterationPromptError,
    compile_continuation_packet,
    render_metaprompt,
    verify_continuation_packet,
)


def state():
    return {
        "project_id": "motion://project/motion-os",
        "session_id": "motion://session/chatgpt/autoloop/sess-001",
        "workstream_id": "motion://workstream/p08-test",
        "correlation_id": "task-123",
        "live_main_sha": "a" * 40,
        "event_watermark": 999,
        "context_projection_hash": "c" * 64,
        "event_fabric_snapshot_hash": "d" * 64,
        "authority_state": "VERIFIED_BRANCH_HEAD_NOT_PROMOTED",
        "branch": "feat/example",
        "pr": 123,
        "head_sha": "b" * 40,
        "completed_work": ["implemented X"],
        "exact_tests": ["pytest: 10 passed"],
        "gauntlet_findings": ["stale writer rejected"],
        "blockers": [],
        "external_degraded": ["Drive unavailable"],
        "evidence_refs": ["workflow#123"],
        "released_scopes": ["contract:x"],
    }


def execute_wave():
    return {
        "schema": "motion-os.next-wave/v1",
        "decision": "EXECUTE",
        "authority_binding": {
            "main_sha": "a" * 40,
            "event_watermark": 999,
            "context_projection_hash": "c" * 64,
            "event_fabric_snapshot_hash": "d" * 64,
            "event_fabric_contract_version": "motion-os.event-fabric/v3",
        },
        "selected": {
            "task_id": "P0_NEXT",
            "title": "Execute next P0",
            "priority": "P0",
            "score": 1200.0,
            "resource_scope": ["file:src/x.py", "contract:x"],
            "branch": "autoloop/p08/p0-next",
            "local_profiles": ["quick", "merge"],
            "adversarial_tests": ["stale-main", "scope-conflict"],
        },
    }


def blocked_wave():
    return {
        "schema": "motion-os.next-wave/v1",
        "decision": "BLOCKED",
        "reason": "EXTERNAL_BLOCKER",
        "next_action": "wait for artifact",
    }


def test_packet_is_deterministic_and_self_verifying():
    a = compile_continuation_packet(state(), execute_wave())
    b = compile_continuation_packet(state(), execute_wave())
    assert a == b
    assert len(a["packet_sha256"]) == 64
    assert verify_continuation_packet(a) is True


def test_packet_hash_changes_when_next_wave_changes():
    a = compile_continuation_packet(state(), execute_wave())
    changed = execute_wave()
    changed["selected"]["task_id"] = "P0_OTHER"
    b = compile_continuation_packet(state(), changed)
    assert a["packet_sha256"] != b["packet_sha256"]


def test_packet_tampering_fails_closed_before_render():
    packet = compile_continuation_packet(state(), execute_wave())
    packet["authority_state"] = "EMPIRICALLY_QUALIFIED"
    with pytest.raises(NextIterationPromptError, match="hash mismatch"):
        verify_continuation_packet(packet)
    with pytest.raises(NextIterationPromptError, match="hash mismatch"):
        render_metaprompt(packet)


def test_missing_authority_fields_fail_closed():
    raw = state()
    raw.pop("event_watermark")
    with pytest.raises(NextIterationPromptError, match="event_watermark"):
        compile_continuation_packet(raw, execute_wave())


def test_non_authoritative_next_wave_decision_fails_closed():
    with pytest.raises(NextIterationPromptError, match="authoritative compiler"):
        compile_continuation_packet(state(), {"schema": "motion-os.next-wave/v1", "decision": "MAYBE"})


def test_execute_wave_must_bind_same_main_watermark_and_projection():
    for field, value, message in [
        ("main_sha", "f" * 40, "main_sha"),
        ("event_watermark", 1000, "watermark"),
        ("context_projection_hash", "e" * 64, "projection"),
        ("event_fabric_snapshot_hash", "f" * 64, "snapshot"),
    ]:
        wave = execute_wave()
        wave["authority_binding"][field] = value
        with pytest.raises(NextIterationPromptError, match=message):
            compile_continuation_packet(state(), wave)


def test_execute_wave_requires_event_fabric_v3_binding():
    wave = execute_wave()
    wave["authority_binding"]["event_fabric_contract_version"] = "motion-os.event-fabric/v2"
    with pytest.raises(NextIterationPromptError, match="Event Fabric"):
        compile_continuation_packet(state(), wave)


def test_execute_prompt_contains_packet_verification_and_exact_next_task_as_untrusted_json():
    packet = compile_continuation_packet(state(), execute_wave())
    prompt = render_metaprompt(packet)
    assert "/autoprompt" in prompt
    assert "Verify PACKET_SHA256" in prompt
    assert "INVALIDATE THIS PACKET" in prompt
    assert "UNTRUSTED_DATA" in prompt
    assert 'NEXT_TASK_ID_JSON: "P0_NEXT"' in prompt
    assert 'TARGET_BRANCH_JSON: "autoloop/p08/p0-next"' in prompt
    assert "/gauntlet-loop" in prompt
    assert "Maximum 3 materially distinct repair attempts" in prompt


def test_blocked_prompt_carries_block_reason_as_untrusted_json_without_execution_claim():
    packet = compile_continuation_packet(state(), blocked_wave())
    prompt = render_metaprompt(packet)
    assert "COMPILED_DECISION: BLOCKED" in prompt
    assert 'BLOCK_REASON_JSON: "EXTERNAL_BLOCKER"' in prompt
    assert 'NEXT_ACTION_JSON: "wait for artifact"' in prompt
    assert "NEXT_TASK_ID_JSON" not in prompt


def test_freshness_contract_is_always_fail_closed():
    packet = compile_continuation_packet(state(), execute_wave())
    assert packet["freshness_contract"] == {
        "must_recheck_live_main_sha": True,
        "must_recheck_event_watermark": True,
        "must_recheck_active_claims": True,
        "must_recheck_pr_lifecycle": True,
        "must_verify_packet_hash": True,
        "must_verify_event_fabric_contract": True,
        "invalidate_on_any_material_drift": True,
    }


def test_malformed_sha_watermark_authority_and_pr_fail_closed():
    raw = state()
    raw["live_main_sha"] = "bad"
    with pytest.raises(NextIterationPromptError, match="git SHA"):
        compile_continuation_packet(raw, execute_wave())

    raw = state()
    raw["event_watermark"] = "999"
    with pytest.raises(NextIterationPromptError, match="non-negative integer"):
        compile_continuation_packet(raw, execute_wave())

    raw = state()
    raw["authority_state"] = "MAGIC"
    with pytest.raises(NextIterationPromptError, match="authority_state"):
        compile_continuation_packet(raw, execute_wave())

    raw = state()
    raw["pr"] = True
    with pytest.raises(NextIterationPromptError, match="positive integer"):
        compile_continuation_packet(raw, execute_wave())


def test_blocked_wave_requires_reason():
    with pytest.raises(NextIterationPromptError, match="reason"):
        compile_continuation_packet(state(), {"schema": "motion-os.next-wave/v1", "decision": "BLOCKED"})
