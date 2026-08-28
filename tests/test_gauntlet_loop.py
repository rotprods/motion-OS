import pytest

from scripts.gauntlet_loop import GauntletError, evaluate_gauntlet


def attempt(i, strategy, result_hash, complete=False, reason="not done", progress=0.0):
    return {
        "iteration": i,
        "strategy": strategy,
        "result_hash": result_hash,
        "verifier_complete": complete,
        "verifier_reason": reason,
        "measurable_progress": progress,
    }


def test_empty_history_requests_first_iteration():
    result = evaluate_gauntlet([])
    assert result["state"] == "ITERATE"
    assert result["remaining_attempts"] == 3


def test_verifier_completion_is_terminal_verified():
    result = evaluate_gauntlet([attempt(1, "fix-a", "abc", True, "all gates pass", 1.0)])
    assert result["state"] == "VERIFIED"
    assert result["result_hash"] == "abc"


def test_same_strategy_same_result_detects_stuck_loop():
    result = evaluate_gauntlet([
        attempt(1, "same patch", "abc", progress=0.2),
        attempt(2, "same patch", "abc", progress=0.2),
    ])
    assert result["state"] == "BLOCKED"
    assert result["reason"] == "STUCK_LOOP"


def test_same_strategy_without_measurable_progress_detects_stuck_loop():
    result = evaluate_gauntlet([
        attempt(1, "same patch", "abc", progress=0.20),
        attempt(2, "same patch", "def", progress=0.205),
    ], min_progress_delta=0.01)
    assert result["reason"] == "STUCK_LOOP"


def test_materially_different_strategy_can_continue():
    result = evaluate_gauntlet([
        attempt(1, "patch parser", "abc", progress=0.2),
        attempt(2, "replace parser boundary", "def", progress=0.3),
    ])
    assert result["state"] == "ITERATE"
    assert result["remaining_attempts"] == 1


def test_attempt_budget_blocks_after_three_failures():
    result = evaluate_gauntlet([
        attempt(1, "a", "1", progress=0.1),
        attempt(2, "b", "2", progress=0.2),
        attempt(3, "c", "3", progress=0.3),
    ])
    assert result["state"] == "BLOCKED"
    assert result["reason"] == "ATTEMPT_BUDGET_EXHAUSTED"


def test_kill_switch_always_blocks():
    result = evaluate_gauntlet([attempt(1, "a", "1")], kill_switch=True)
    assert result == {"state": "BLOCKED", "reason": "KILL_SWITCH_ACTIVE", "next_action": "stop immediately"}


def test_non_contiguous_history_fails_closed():
    with pytest.raises(GauntletError, match="contiguous"):
        evaluate_gauntlet([attempt(2, "a", "1")])


def test_history_beyond_budget_fails_closed():
    with pytest.raises(GauntletError, match="exceeds"):
        evaluate_gauntlet([
            attempt(1, "a", "1"), attempt(2, "b", "2"),
            attempt(3, "c", "3"), attempt(4, "d", "4"),
        ])
