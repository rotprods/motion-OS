import math

import pytest

from src.avatar.render_guard import (
    RenderIntent,
    RenderState,
    SpendPolicy,
    authorize_render,
    can_submit,
    next_retry,
)


def _policy() -> SpendPolicy:
    return SpendPolicy(
        max_credits_per_render=10.0,
        max_credits_per_day=100.0,
        max_concurrent_renders=2,
        max_retries=1,
    )


def _authorize(**overrides):
    args = dict(
        content_id="CNT_1",
        profile_id="P_1",
        script="hello",
        explicit_authorization=True,
        preflight_ok=True,
        estimated_credits=2.0,
        spent_today=3.0,
        concurrent_renders=0,
        policy=_policy(),
    )
    args.update(overrides)
    return authorize_render(**args)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), -0.01, True])
def test_estimated_credits_fail_closed_for_nonfinite_negative_or_bool(bad):
    with pytest.raises(ValueError, match="estimated_credits"):
        _authorize(estimated_credits=bad)


def test_paid_authorization_requires_credit_estimate():
    with pytest.raises(ValueError, match="estimated_credits is required"):
        _authorize(estimated_credits=None)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), -1.0, True])
def test_spent_today_fail_closed_for_nonfinite_negative_or_bool(bad):
    with pytest.raises(ValueError, match="spent_today"):
        _authorize(spent_today=bad)


@pytest.mark.parametrize("bad", [-1, 1.5, True])
def test_concurrency_count_requires_nonnegative_integer(bad):
    with pytest.raises(ValueError, match="concurrent_renders"):
        _authorize(concurrent_renders=bad)


def test_truthy_strings_cannot_spoof_explicit_authorization_or_preflight():
    with pytest.raises(PermissionError, match="explicit render authorization"):
        _authorize(explicit_authorization="true")
    with pytest.raises(ValueError, match="preflight"):
        _authorize(preflight_ok="true")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_credits_per_render": float("nan"), "max_credits_per_day": 100.0, "max_concurrent_renders": 2},
        {"max_credits_per_render": 10.0, "max_credits_per_day": float("inf"), "max_concurrent_renders": 2},
        {"max_credits_per_render": -1.0, "max_credits_per_day": 100.0, "max_concurrent_renders": 2},
        {"max_credits_per_render": 10.0, "max_credits_per_day": -1.0, "max_concurrent_renders": 2},
        {"max_credits_per_render": 10.0, "max_credits_per_day": 100.0, "max_concurrent_renders": 0},
        {"max_credits_per_render": 10.0, "max_credits_per_day": 100.0, "max_concurrent_renders": True},
    ],
)
def test_invalid_spend_policy_cannot_exist(kwargs):
    with pytest.raises(ValueError):
        SpendPolicy(**kwargs)


def test_per_render_cap_cannot_exceed_daily_cap():
    with pytest.raises(ValueError, match="cannot exceed"):
        SpendPolicy(11.0, 10.0, 1)


def test_zero_retries_is_valid_but_negative_retry_policy_is_not():
    policy = SpendPolicy(1.0, 1.0, 1, max_retries=0)
    assert policy.max_retries == 0
    with pytest.raises(ValueError, match="max_retries"):
        SpendPolicy(1.0, 1.0, 1, max_retries=-1)


def test_valid_authorization_preserves_normalized_credit_value():
    intent = _authorize(estimated_credits=2)
    assert intent.state == RenderState.AUTHORIZED
    assert intent.estimated_credits == 2.0
    assert math.isfinite(intent.estimated_credits)
    assert can_submit(intent, {}) is True


def test_budget_limits_still_enforced_after_validation():
    with pytest.raises(RuntimeError, match="per-render"):
        _authorize(estimated_credits=11.0)
    with pytest.raises(RuntimeError, match="daily"):
        _authorize(estimated_credits=9.0, spent_today=95.0)
    with pytest.raises(RuntimeError, match="concurrent"):
        _authorize(concurrent_renders=2)


def test_negative_or_noninteger_retry_count_cannot_reenter_authorized_state():
    base = RenderIntent(
        intent_id="RND_X",
        content_id="CNT_X",
        profile_id="P_X",
        script_hash="a" * 64,
        state=RenderState.FAILED_RETRYABLE,
        retry_count=-1,
    )
    with pytest.raises(ValueError, match="retry_count"):
        next_retry(base, _policy())

    noninteger = RenderIntent(**{**base.__dict__, "retry_count": 0.5})
    with pytest.raises(ValueError, match="retry_count"):
        next_retry(noninteger, _policy())


def test_provider_job_still_blocks_retry_before_counter_validation():
    intent = RenderIntent(
        intent_id="RND_X",
        content_id="CNT_X",
        profile_id="P_X",
        script_hash="a" * 64,
        state=RenderState.FAILED_RETRYABLE,
        provider_job_id="provider-job-1",
        retry_count=0,
    )
    with pytest.raises(RuntimeError, match="reconcile"):
        next_retry(intent, _policy())


def test_retry_submission_requires_exact_bounded_transition_and_policy():
    original = _authorize()
    failed = RenderIntent(**{**original.__dict__, "state": RenderState.FAILED_RETRYABLE})
    retried = next_retry(failed, _policy())

    assert can_submit(retried, {original.intent_id: failed}) is False
    assert can_submit(retried, {original.intent_id: failed}, policy=_policy()) is True

    fresh_reauthorization = _authorize()
    assert fresh_reauthorization.retry_count == 0
    assert can_submit(fresh_reauthorization, {original.intent_id: failed}, policy=_policy()) is False

    forged_wrong_generation = RenderIntent(**{**retried.__dict__, "retry_count": 7})
    assert can_submit(forged_wrong_generation, {original.intent_id: failed}, policy=_policy()) is False


def test_retry_submission_respects_max_retries_and_non_authorized_states():
    no_retry = SpendPolicy(10.0, 100.0, 2, max_retries=0)
    original = _authorize()
    failed = RenderIntent(**{**original.__dict__, "state": RenderState.FAILED_RETRYABLE})
    forged = RenderIntent(**{**failed.__dict__, "state": RenderState.AUTHORIZED, "retry_count": 1})
    assert can_submit(forged, {original.intent_id: failed}, policy=no_retry) is False

    completed = RenderIntent(**{**original.__dict__, "state": RenderState.COMPLETED})
    assert can_submit(completed, {}) is False
