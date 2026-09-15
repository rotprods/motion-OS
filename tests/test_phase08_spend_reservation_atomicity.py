import pytest

from src.avatar.provider_submission import SubmissionBlocked, submit_paid_render
from src.avatar.render_guard import SpendPolicy, authorize_render
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
