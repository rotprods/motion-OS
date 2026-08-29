import pytest

from src.avatar.render_guard import RenderIntent, RenderState, SpendPolicy, authorize_render, next_retry


def _policy() -> SpendPolicy:
    return SpendPolicy(10.0, 100.0, 2, max_retries=1)


def test_valid_authorization_and_retry_path_remain_unchanged():
    intent = authorize_render(
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
    assert intent.state == RenderState.AUTHORIZED
    assert intent.estimated_credits == 2.0

    failed = RenderIntent(**{**intent.__dict__, "state": RenderState.FAILED_RETRYABLE})
    assert next_retry(failed, _policy()).retry_count == 1


def test_invalid_authority_and_spend_inputs_fail_closed():
    base = dict(
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

    with pytest.raises(PermissionError):
        authorize_render(**{**base, "explicit_authorization": "true"})
    with pytest.raises(ValueError):
        authorize_render(**{**base, "preflight_ok": "true"})
    with pytest.raises(ValueError):
        authorize_render(**{**base, "estimated_credits": float("nan")})
    with pytest.raises(ValueError):
        authorize_render(**{**base, "spent_today": -1.0})
    with pytest.raises(ValueError):
        authorize_render(**{**base, "concurrent_renders": 1.5})
    with pytest.raises(ValueError):
        SpendPolicy(float("inf"), 100.0, 2)
    with pytest.raises(ValueError):
        SpendPolicy(11.0, 10.0, 2)

    invalid_retry = RenderIntent(
        intent_id="RND_X",
        content_id="CNT_X",
        profile_id="P_X",
        script_hash="a" * 64,
        state=RenderState.FAILED_RETRYABLE,
        retry_count=-1,
    )
    with pytest.raises(ValueError):
        next_retry(invalid_retry, _policy())
