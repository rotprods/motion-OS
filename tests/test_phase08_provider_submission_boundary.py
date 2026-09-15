from dataclasses import replace

import pytest

from src.avatar.provider_submission import (
    SubmissionBlocked,
    SubmissionConflict,
    submit_paid_render,
)
from src.avatar.render_guard import (
    RenderIntent,
    RenderState,
    SpendPolicy,
    authorize_render,
    next_retry,
)
from src.avatar.transactional_store import SQLiteTransactionalRenderStore


POLICY = SpendPolicy(10.0, 100.0, 2, max_retries=1)


def _authorized(*, credits: float = 2.0) -> RenderIntent:
    return authorize_render(
        content_id="CNT_1",
        profile_id="PROFILE_1",
        script="hello world",
        explicit_authorization=True,
        preflight_ok=True,
        estimated_credits=credits,
        spent_today=0.0,
        concurrent_renders=0,
        policy=POLICY,
    )


def _request(**extra):
    payload = {
        "avatarId": "avatar_1",
        "voiceId": "voice_1",
        "script": "hello world",
        "title": "test",
        "aspectRatio": "9:16",
        "resolution": "1080p",
        "outputFormat": "mp4",
    }
    payload.update(extra)
    return payload


def _persist(store: SQLiteTransactionalRenderStore, intent: RenderIntent, owner: str = "seed") -> None:
    lease = store.acquire_lease(intent.intent_id, owner)
    try:
        store.put_intent(intent, lease)
    finally:
        store.release_lease(lease)


class FakeProvider:
    provider_id = "heygen"

    def __init__(self, result=None, exc: Exception | None = None, before_return=None):
        self.result = result if result is not None else {"video_id": "vid_1", "status": "pending"}
        self.exc = exc
        self.before_return = before_return
        self.calls = []

    def submit(self, payload):
        self.calls.append(dict(payload))
        if self.before_return is not None:
            self.before_return(payload)
        if self.exc is not None:
            raise self.exc
        return self.result


def _submit(store, intent, provider, *, spent_today=0.0, concurrent_renders=0, request=None):
    return submit_paid_render(
        intent=intent,
        request_payload=request or _request(),
        provider=provider,
        store=store,
        policy=POLICY,
        spent_today=spent_today,
        concurrent_renders=concurrent_renders,
        owner_id="worker-1",
    )


def test_initial_submission_persists_submitted_before_provider_call_then_acknowledges(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "renders.db")
    intent = _authorized()
    _persist(store, intent)

    def assert_durable_submitted(_payload):
        current = store.get_intent(intent.intent_id)
        assert current is not None
        assert current.state == RenderState.SUBMITTED
        assert current.provider_job_id is None

    provider = FakeProvider(before_return=assert_durable_submitted)
    outcome = _submit(store, intent, provider)

    assert outcome.intent.state == RenderState.ACKNOWLEDGED
    assert outcome.intent.provider_job_id == "vid_1"
    assert outcome.provider_id == "heygen"
    assert outcome.provider_called is True
    assert len(outcome.request_sha256) == 64
    assert provider.calls[0]["callbackId"] == intent.intent_id
    assert store.get_intent(intent.intent_id) == outcome.intent
    assert store.event_count(intent.intent_id) == 3  # AUTHORIZED -> SUBMITTED -> ACKNOWLEDGED


def test_initial_submit_rechecks_live_budget_and_capacity_before_provider_call(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "renders.db")
    intent = _authorized(credits=8.0)
    _persist(store, intent)

    provider = FakeProvider()
    with pytest.raises(SubmissionBlocked, match="live spend/capacity"):
        _submit(store, intent, provider, spent_today=95.0)
    assert provider.calls == []
    assert store.get_intent(intent.intent_id) == intent

    with pytest.raises(SubmissionBlocked, match="live spend/capacity"):
        _submit(store, intent, provider, concurrent_renders=2)
    assert provider.calls == []
    assert store.get_intent(intent.intent_id) == intent


def test_provider_timeout_after_durable_submitted_forces_reconciliation_and_hides_message(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "renders.db")
    intent = _authorized()
    _persist(store, intent)
    provider = FakeProvider(exc=TimeoutError("token=sk-super-secret-provider-payload"))

    outcome = _submit(store, intent, provider)
    assert outcome.intent.state == RenderState.RECONCILE_REQUIRED
    assert outcome.failure_type == "TimeoutError"
    assert "super-secret" not in repr(outcome)
    assert store.get_intent(intent.intent_id).state == RenderState.RECONCILE_REQUIRED

    with pytest.raises(SubmissionBlocked, match="requires reconciliation"):
        _submit(store, intent, provider)
    assert len(provider.calls) == 1


def test_job_id_without_status_is_reconcile_required_not_acknowledged(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "renders.db")
    intent = _authorized()
    _persist(store, intent)
    provider = FakeProvider(result={"video_id": "vid_uncertain"})

    outcome = _submit(store, intent, provider)
    assert outcome.intent.state == RenderState.RECONCILE_REQUIRED
    assert outcome.intent.provider_job_id == "vid_uncertain"
    assert outcome.requires_reconciliation is True


def test_missing_or_malformed_job_identity_is_reconcile_required(tmp_path):
    for result in ({"status": "pending"}, {"video_id": "", "status": "pending"}, "not-a-mapping"):
        store = SQLiteTransactionalRenderStore(tmp_path / f"renders-{hash(str(result))}.db")
        intent = _authorized()
        _persist(store, intent)
        provider = FakeProvider(result=result)
        outcome = _submit(store, intent, provider)
        assert outcome.intent.state == RenderState.RECONCILE_REQUIRED
        assert outcome.intent.provider_job_id is None


def test_duplicate_submission_after_acknowledgement_never_calls_provider_again(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "renders.db")
    intent = _authorized()
    _persist(store, intent)
    first_provider = FakeProvider()
    _submit(store, intent, first_provider)

    second_provider = FakeProvider(result={"video_id": "vid_2", "status": "pending"})
    with pytest.raises(SubmissionBlocked, match="requires reconciliation"):
        _submit(store, intent, second_provider)
    assert second_provider.calls == []


def test_retry_must_be_exact_transition_and_rechecks_live_budget(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "renders.db")
    original = _authorized(credits=8.0)
    failed = replace(original, state=RenderState.FAILED_RETRYABLE)
    _persist(store, failed)
    retried = next_retry(failed, POLICY)

    blocked_provider = FakeProvider()
    with pytest.raises(SubmissionBlocked, match="exact live-budget"):
        _submit(store, retried, blocked_provider, spent_today=95.0)
    assert blocked_provider.calls == []
    assert store.get_intent(original.intent_id) == failed

    forged = replace(retried, retry_count=7)
    with pytest.raises(SubmissionBlocked, match="exact live-budget"):
        _submit(store, forged, blocked_provider)
    assert blocked_provider.calls == []

    provider = FakeProvider(result={"video_id": "vid_retry", "status": "queued"})
    outcome = _submit(store, retried, provider, spent_today=10.0)
    assert outcome.intent.state == RenderState.ACKNOWLEDGED
    assert outcome.intent.provider_job_id == "vid_retry"


def test_fresh_reauthorization_cannot_bypass_persisted_retry_generation(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "renders.db")
    original = _authorized()
    failed = replace(original, state=RenderState.FAILED_RETRYABLE)
    _persist(store, failed)
    fresh = _authorized()
    provider = FakeProvider()

    with pytest.raises(SubmissionBlocked, match="exact live-budget"):
        _submit(store, fresh, provider)
    assert provider.calls == []


def test_request_identity_callback_provider_and_finite_json_fail_before_provider_call(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "renders.db")
    intent = _authorized()
    _persist(store, intent)
    provider = FakeProvider()

    with pytest.raises(SubmissionBlocked, match="not bound"):
        _submit(store, intent, provider, request=_request(script="different script"))
    with pytest.raises(SubmissionBlocked, match="callbackId"):
        _submit(store, intent, provider, request=_request(callbackId="spoof"))
    with pytest.raises(SubmissionBlocked, match="finite JSON"):
        _submit(store, intent, provider, request=_request(extra=float("nan")))
    assert provider.calls == []
    assert store.get_intent(intent.intent_id) == intent

    other_provider = FakeProvider()
    other_provider.provider_id = "other-provider"
    with pytest.raises(SubmissionBlocked, match="bound to heygen"):
        _submit(store, intent, other_provider)
    assert other_provider.calls == []


def test_missing_durable_authorization_or_malformed_port_blocks_before_provider_call(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "renders.db")
    intent = _authorized()
    provider = FakeProvider()

    with pytest.raises(SubmissionBlocked, match="durably authorized"):
        _submit(store, intent, provider)
    assert provider.calls == []

    class NoSubmit:
        provider_id = "heygen"

    with pytest.raises(SubmissionBlocked, match="callable submit"):
        _submit(store, intent, NoSubmit())


def test_concurrent_reconciler_wins_and_stale_provider_return_cannot_overwrite(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "renders.db")
    intent = _authorized()
    _persist(store, intent)

    def concurrent_reconcile(_payload):
        submitted = store.get_intent(intent.intent_id)
        assert submitted.state == RenderState.SUBMITTED
        lease = store.acquire_lease(intent.intent_id, "reconciler")
        try:
            store.put_intent(
                replace(submitted, state=RenderState.RUNNING, provider_job_id="vid_external"),
                lease,
            )
        finally:
            store.release_lease(lease)

    provider = FakeProvider(result={"video_id": "vid_stale", "status": "pending"}, before_return=concurrent_reconcile)
    with pytest.raises(SubmissionConflict, match="changed during submission"):
        _submit(store, intent, provider)

    current = store.get_intent(intent.intent_id)
    assert current.state == RenderState.RUNNING
    assert current.provider_job_id == "vid_external"


def test_unknown_provider_status_with_job_id_stays_reconcile_required(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "renders.db")
    intent = _authorized()
    _persist(store, intent)
    provider = FakeProvider(result={"video_id": "vid_1", "status": "teleported"})

    outcome = _submit(store, intent, provider)
    assert outcome.intent.state == RenderState.RECONCILE_REQUIRED
    assert outcome.intent.provider_job_id == "vid_1"
