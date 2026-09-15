from dataclasses import replace

import pytest

from src.avatar.provider_submission import SubmissionBlocked, submit_paid_render
from src.avatar.render_guard import RenderState, SpendPolicy, authorize_render, next_retry
from src.avatar.spend_reservation import SQLitePaidRenderAuthorityStore


class Provider:
    provider_id = "heygen"

    def __init__(self, *, status="pending", job_id="vid"):
        self.status = status
        self.job_id = job_id
        self.calls = 0

    def submit(self, payload):
        self.calls += 1
        return {"video_id": self.job_id, "status": self.status}


def authorized(content_id: str, script: str, credits: float, policy: SpendPolicy):
    return authorize_render(
        content_id=content_id,
        profile_id="PROFILE_BUDGET",
        script=script,
        explicit_authorization=True,
        preflight_ok=True,
        estimated_credits=credits,
        spent_today=0.0,
        concurrent_renders=0,
        policy=policy,
    )


def request(script: str):
    return {
        "avatarId": "avatar_1",
        "voiceId": "voice_1",
        "script": script,
        "title": "budget regression",
        "aspectRatio": "9:16",
        "resolution": "1080p",
        "outputFormat": "mp4",
    }


def persist(store, intent, owner):
    lease = store.acquire_lease(intent.intent_id, owner)
    try:
        store.put_intent(intent, lease)
    finally:
        store.release_lease(lease)


def submit(store, intent, script, provider, policy, owner):
    return submit_paid_render(
        intent=intent,
        request_payload=request(script),
        provider=provider,
        store=store,
        policy=policy,
        spent_today=0.0,
        concurrent_renders=0,
        owner_id=owner,
    )


def test_two_store_instances_cannot_overspend_same_daily_budget_from_stale_zero_snapshots(tmp_path):
    db = tmp_path / "shared-authority.sqlite"
    first_store = SQLitePaidRenderAuthorityStore(db)
    second_store = SQLitePaidRenderAuthorityStore(db)
    policy = SpendPolicy(10.0, 10.0, 5)
    first = authorized("CNT_A", "script a", 6.0, policy)
    second = authorized("CNT_B", "script b", 6.0, policy)
    persist(first_store, first, "seed-a")
    persist(second_store, second, "seed-b")

    first_provider = Provider(job_id="vid-a")
    submit(first_store, first, "script a", first_provider, policy, "worker-a")
    assert first_provider.calls == 1
    assert first_store.spent_for_day() == pytest.approx(6.0)

    second_provider = Provider(job_id="vid-b")
    with pytest.raises(SubmissionBlocked, match="atomic spend/capacity reservation"):
        submit(second_store, second, "script b", second_provider, policy, "worker-b")
    assert second_provider.calls == 0
    assert second_store.spent_for_day() == pytest.approx(6.0)
    assert second_store.spend_reservation_count() == 1


def test_two_distinct_intents_cannot_exceed_global_concurrency_from_stale_zero_snapshots(tmp_path):
    db = tmp_path / "shared-concurrency.sqlite"
    first_store = SQLitePaidRenderAuthorityStore(db)
    second_store = SQLitePaidRenderAuthorityStore(db)
    policy = SpendPolicy(10.0, 100.0, 1)
    first = authorized("CNT_A", "script a", 2.0, policy)
    second = authorized("CNT_B", "script b", 2.0, policy)
    persist(first_store, first, "seed-a")
    persist(second_store, second, "seed-b")

    first_provider = Provider(job_id="vid-a", status="pending")
    submit(first_store, first, "script a", first_provider, policy, "worker-a")
    assert first_store.active_spend_reservation_count() == 1

    second_provider = Provider(job_id="vid-b", status="pending")
    with pytest.raises(SubmissionBlocked, match="atomic spend/capacity reservation"):
        submit(second_store, second, "script b", second_provider, policy, "worker-b")
    assert second_provider.calls == 0
    assert second_store.active_spend_reservation_count() == 1


def test_terminal_provider_result_releases_concurrency_but_keeps_daily_spend_consumed(tmp_path):
    db = tmp_path / "terminal-release.sqlite"
    store = SQLitePaidRenderAuthorityStore(db)
    policy = SpendPolicy(10.0, 100.0, 1)
    first = authorized("CNT_DONE", "script done", 3.0, policy)
    second = authorized("CNT_NEXT", "script next", 4.0, policy)
    persist(store, first, "seed-done")
    persist(store, second, "seed-next")

    completed = Provider(job_id="vid-done", status="completed")
    outcome = submit(store, first, "script done", completed, policy, "worker-done")
    assert outcome.intent.state.value == "COMPLETED"
    assert store.active_spend_reservation_count() == 0
    assert store.spent_for_day() == pytest.approx(3.0)

    pending = Provider(job_id="vid-next", status="pending")
    submit(store, second, "script next", pending, policy, "worker-next")
    assert pending.calls == 1
    assert store.active_spend_reservation_count() == 1
    assert store.spent_for_day() == pytest.approx(7.0)


def test_later_terminal_reconciliation_releases_capacity_automatically(tmp_path):
    store = SQLitePaidRenderAuthorityStore(tmp_path / "later-terminal.sqlite")
    policy = SpendPolicy(10.0, 100.0, 1)
    intent = authorized("CNT_LATER", "script later", 3.0, policy)
    persist(store, intent, "seed")
    outcome = submit(store, intent, "script later", Provider(status="pending"), policy, "worker")
    assert outcome.intent.state == RenderState.ACKNOWLEDGED
    assert store.active_spend_reservation_count() == 1

    completed = replace(outcome.intent, state=RenderState.COMPLETED)
    persist(store, completed, "reconciler")
    assert store.get_intent(intent.intent_id) == completed
    assert store.active_spend_reservation_count() == 0
    assert store.spent_for_day() == pytest.approx(3.0)


def test_retryable_generation_releases_capacity_so_retry_can_reserve_new_generation(tmp_path):
    store = SQLitePaidRenderAuthorityStore(tmp_path / "retryable.sqlite")
    policy = SpendPolicy(10.0, 100.0, 1, max_retries=1)
    intent = authorized("CNT_RETRY", "script retry", 3.0, policy)
    persist(store, intent, "seed")
    store.reserve_spend(
        intent,
        policy=policy,
        observed_spent_today=0.0,
        observed_concurrent_renders=0,
    )
    assert store.active_spend_reservation_count() == 1

    failed = replace(intent, state=RenderState.FAILED_RETRYABLE)
    persist(store, failed, "failure-classifier")
    assert store.active_spend_reservation_count() == 0

    retried = next_retry(failed, policy)
    provider = Provider(job_id="vid-retry", status="pending")
    outcome = submit(store, retried, "script retry", provider, policy, "retry-worker")
    assert provider.calls == 1
    assert outcome.intent.state == RenderState.ACKNOWLEDGED
    assert store.active_spend_reservation_count() == 1
    assert store.spent_for_day() == pytest.approx(6.0)


def test_paid_authority_store_rejects_stable_identity_drift_before_event_write(tmp_path):
    store = SQLitePaidRenderAuthorityStore(tmp_path / "identity.sqlite")
    policy = SpendPolicy(10.0, 100.0, 1)
    intent = authorized("CNT_ID", "script id", 2.0, policy)
    persist(store, intent, "seed")
    before_events = store.event_count(intent.intent_id)
    forged = replace(intent, content_id="CNT_OTHER")
    lease = store.acquire_lease(intent.intent_id, "forger")
    try:
        with pytest.raises(RuntimeError, match="stable identity"):
            store.put_intent(forged, lease)
    finally:
        store.release_lease(lease)
    assert store.get_intent(intent.intent_id) == intent
    assert store.event_count(intent.intent_id) == before_events


def test_same_submission_generation_cannot_reserve_spend_twice(tmp_path):
    store = SQLitePaidRenderAuthorityStore(tmp_path / "duplicate.sqlite")
    policy = SpendPolicy(10.0, 100.0, 5)
    intent = authorized("CNT_DUP", "script dup", 2.0, policy)
    first = store.reserve_spend(
        intent,
        policy=policy,
        observed_spent_today=0.0,
        observed_concurrent_renders=0,
    )
    assert first.intent_id == intent.intent_id
    with pytest.raises(RuntimeError, match="already has a durable spend reservation"):
        store.reserve_spend(
            intent,
            policy=policy,
            observed_spent_today=0.0,
            observed_concurrent_renders=0,
        )
    assert store.spend_reservation_count() == 1
