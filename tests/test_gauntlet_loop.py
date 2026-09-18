import pytest

from scripts.gauntlet_loop import GauntletError, evaluate_gauntlet


def h(ch):
    return ch * 64


def attempt(i, strategy, result_hash, complete=False, reason="not done", progress=0.0):
    return {
        "iteration": i,
        "strategy": strategy,
        "result_hash": result_hash,
        "verifier_complete": complete,
        "verifier_reason": reason,
        "measurable_progress": progress,
    }


def receipt(result_hash, *, implementer="motion://agent/implementer/1", verifier="motion://agent/verifier/1"):
    return {
        "implementer_id": implementer,
        "verifier_id": verifier,
        "verified_result_hash": result_hash,
        "evidence_hash": h("e"),
        "decision": "PASS",
    }


def test_empty_history_requests_first_iteration():
    result = evaluate_gauntlet([])
    assert result["state"] == "ITERATE"
    assert result["remaining_attempts"] == 3


def test_verifier_completion_is_evidence_bound_but_cannot_mint_verified_authority():
    result_hash = h("a")
    result = evaluate_gauntlet(
        [attempt(1, "fix-a", result_hash, True, "all gates pass", 1.0)],
        verifier_receipt=receipt(result_hash),
    )
    assert result["state"] == "VERIFIER_PASS_UNPROMOTED"
    assert result["promotion_authority"] == "NONE"
    assert result["result_hash"] == result_hash
    assert result["verifier_receipt"]["verifier_id"] == "motion://agent/verifier/1"
    assert "external authority" in result["next_action"]


def test_caller_supplied_receipt_never_grants_verified_state():
    result_hash = h("a")
    result = evaluate_gauntlet(
        [attempt(1, "fix-a", result_hash, True, "pass", 1.0)],
        verifier_receipt=receipt(result_hash),
    )
    assert result["state"] != "VERIFIED"
    assert result["promotion_authority"] == "NONE"


def test_completion_without_independent_receipt_cannot_self_certify():
    with pytest.raises(GauntletError, match="independent verifier receipt"):
        evaluate_gauntlet([attempt(1, "fix-a", h("a"), True, "self says pass", 1.0)])


def test_same_actor_cannot_implement_and_verify():
    result_hash = h("a")
    with pytest.raises(GauntletError, match="must differ"):
        evaluate_gauntlet(
            [attempt(1, "fix-a", result_hash, True, "pass", 1.0)],
            verifier_receipt=receipt(result_hash, implementer="motion://agent/same/1", verifier="motion://agent/same/1"),
        )


def test_verifier_receipt_must_bind_exact_result_hash_and_pass_decision():
    with pytest.raises(GauntletError, match="different result_hash"):
        evaluate_gauntlet(
            [attempt(1, "fix-a", h("a"), True, "pass", 1.0)],
            verifier_receipt=receipt(h("b")),
        )
    bad = receipt(h("a"))
    bad["decision"] = "COMMENT"
    with pytest.raises(GauntletError, match="decision must be PASS"):
        evaluate_gauntlet(
            [attempt(1, "fix-a", h("a"), True, "pass", 1.0)],
            verifier_receipt=bad,
        )


def test_receipt_on_incomplete_attempt_is_rejected():
    with pytest.raises(GauntletError, match="only valid"):
        evaluate_gauntlet(
            [attempt(1, "fix-a", h("a"), False, "not done", 0.5)],
            verifier_receipt=receipt(h("a")),
        )


def test_same_strategy_same_result_detects_stuck_loop():
    result = evaluate_gauntlet([
        attempt(1, "same patch", h("a"), progress=0.2),
        attempt(2, "same patch", h("a"), progress=0.2),
    ])
    assert result["state"] == "BLOCKED"
    assert result["reason"] == "STUCK_LOOP"


def test_same_strategy_without_measurable_progress_detects_stuck_loop():
    result = evaluate_gauntlet([
        attempt(1, "same patch", h("a"), progress=0.20),
        attempt(2, "same patch", h("b"), progress=0.205),
    ], min_progress_delta=0.01)
    assert result["reason"] == "STUCK_LOOP"


def test_materially_different_strategy_can_continue():
    result = evaluate_gauntlet([
        attempt(1, "patch parser", h("a"), progress=0.2),
        attempt(2, "replace parser boundary", h("b"), progress=0.3),
    ])
    assert result["state"] == "ITERATE"
    assert result["remaining_attempts"] == 1


def test_attempt_budget_blocks_after_three_failures():
    result = evaluate_gauntlet([
        attempt(1, "a", h("1"), progress=0.1),
        attempt(2, "b", h("2"), progress=0.2),
        attempt(3, "c", h("3"), progress=0.3),
    ])
    assert result["state"] == "BLOCKED"
    assert result["reason"] == "ATTEMPT_BUDGET_EXHAUSTED"


def test_kill_switch_always_blocks():
    result = evaluate_gauntlet([attempt(1, "a", h("1"))], kill_switch=True)
    assert result == {"state": "BLOCKED", "reason": "KILL_SWITCH_ACTIVE", "next_action": "stop immediately"}


def test_non_contiguous_history_fails_closed():
    with pytest.raises(GauntletError, match="contiguous"):
        evaluate_gauntlet([attempt(2, "a", h("1"))])


def test_history_beyond_budget_fails_closed():
    with pytest.raises(GauntletError, match="exceeds"):
        evaluate_gauntlet([
            attempt(1, "a", h("1")), attempt(2, "b", h("2")),
            attempt(3, "c", h("3")), attempt(4, "d", h("4")),
        ])


def test_string_bool_and_nonfinite_progress_fail_closed():
    bad = attempt(1, "a", h("1"))
    bad["verifier_complete"] = "false"
    with pytest.raises(GauntletError, match="JSON boolean"):
        evaluate_gauntlet([bad])

    bad = attempt(1, "a", h("1"), progress=float("nan"))
    with pytest.raises(GauntletError, match="finite"):
        evaluate_gauntlet([bad])


def test_malformed_result_hash_and_empty_strategy_fail_closed():
    with pytest.raises(GauntletError, match="sha256"):
        evaluate_gauntlet([attempt(1, "a", "abc")])
    with pytest.raises(GauntletError, match="strategy"):
        evaluate_gauntlet([attempt(1, "", h("1"))])


def test_invalid_budget_and_kill_switch_types_fail_closed():
    with pytest.raises(GauntletError):
        evaluate_gauntlet([], max_attempts=True)
    with pytest.raises(GauntletError):
        evaluate_gauntlet([], min_progress_delta=float("inf"))
    with pytest.raises(GauntletError):
        evaluate_gauntlet([], kill_switch="false")
