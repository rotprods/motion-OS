import copy

import pytest

from scripts.next_iteration_metaprompt import (
    NextIterationPromptError,
    compile_continuation_packet,
    render_metaprompt,
)


def state():
    return {
        "project_id": "motion://project/motion-os",
        "session_id": "motion://session/chatgpt/autoloop/sess-001",
        "workstream_id": "motion://workstream/p08-test",
        "correlation_id": "task-123",
        "live_main_sha": "a" * 40,
        "event_watermark": "evt-999",
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


def test_packet_is_deterministic_for_same_inputs():
    a = compile_continuation_packet(state(), execute_wave())
    b = compile_continuation_packet(state(), execute_wave())
    assert a == b
    assert len(a["packet_sha256"]) == 64


def test_packet_hash_changes_when_next_wave_changes():
    a = compile_continuation_packet(state(), execute_wave())
    changed = execute_wave()
    changed["selected"]["task_id"] = "P0_OTHER"
    b = compile_continuation_packet(state(), changed)
    assert a["packet_sha256"] != b["packet_sha256"]


def test_missing_authority_fields_fail_closed():
    raw = state()
    raw.pop("event_watermark")
    with pytest.raises(NextIterationPromptError, match="event_watermark"):
        compile_continuation_packet(raw, execute_wave())


def test_non_authoritative_next_wave_decision_fails_closed():
    with pytest.raises(NextIterationPromptError, match="authoritative compiler"):
        compile_continuation_packet(state(), {"decision": "MAYBE"})


def test_execute_prompt_contains_freshness_and_exact_next_task():
    packet = compile_continuation_packet(state(), execute_wave())
    prompt = render_metaprompt(packet)
    assert "/autoprompt" in prompt
    assert "INVALIDATE THIS PACKET" in prompt
    assert "NEXT_TASK_ID: P0_NEXT" in prompt
    assert "TARGET_BRANCH: autoloop/p08/p0-next" in prompt
    assert "/gauntlet-loop" in prompt
    assert "Maximum 3 materially distinct repair attempts" in prompt


def test_blocked_prompt_carries_block_reason_without_execution_claim():
    blocked = {
        "schema": "motion-os.next-wave/v1",
        "decision": "BLOCKED",
        "reason": "EXTERNAL_BLOCKER",
        "next_action": "wait for artifact",
    }
    packet = compile_continuation_packet(state(), blocked)
    prompt = render_metaprompt(packet)
    assert "COMPILED_DECISION: BLOCKED" in prompt
    assert "BLOCK_REASON: EXTERNAL_BLOCKER" in prompt
    assert "wait for artifact" in prompt
    assert "NEXT_TASK_ID" not in prompt


def test_freshness_contract_is_always_fail_closed():
    packet = compile_continuation_packet(state(), execute_wave())
    assert packet["freshness_contract"] == {
        "must_recheck_live_main_sha": True,
        "must_recheck_event_watermark": True,
        "must_recheck_active_claims": True,
        "must_recheck_pr_lifecycle": True,
        "invalidate_on_any_material_drift": True,
    }
