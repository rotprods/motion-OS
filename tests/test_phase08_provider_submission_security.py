from src.avatar.provider_submission import submit_paid_render
from src.avatar.render_guard import RenderState, SpendPolicy, authorize_render
from src.avatar.transactional_store import SQLiteTransactionalRenderStore


POLICY = SpendPolicy(10.0, 100.0, 2, max_retries=1)


class PoisonedProvider:
    provider_id = "heygen"

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.calls = 0

    def submit(self, payload):
        self.calls += 1
        return {"video_id": self.job_id, "status": "pending"}


def _authorized():
    return authorize_render(
        content_id="CNT_SECURITY",
        profile_id="PROFILE_SECURITY",
        script="hello world",
        explicit_authorization=True,
        preflight_ok=True,
        estimated_credits=1.0,
        spent_today=0.0,
        concurrent_renders=0,
        policy=POLICY,
    )


def _persist(store, intent):
    lease = store.acquire_lease(intent.intent_id, "seed")
    try:
        store.put_intent(intent, lease)
    finally:
        store.release_lease(lease)


def _request():
    return {
        "avatarId": "avatar_1",
        "voiceId": "voice_1",
        "script": "hello world",
        "title": "security regression",
        "aspectRatio": "9:16",
        "resolution": "1080p",
        "outputFormat": "mp4",
    }


def test_control_or_whitespace_bearing_provider_job_ids_never_persist_as_authority(tmp_path):
    poisoned_ids = [
        "vid_1\nspoof",
        "vid_1\rspoof",
        "vid_1\tspoof",
        " vid_1",
        "vid_1 ",
        "vid_\x00spoof",
    ]
    for index, poisoned in enumerate(poisoned_ids):
        store = SQLiteTransactionalRenderStore(tmp_path / f"poisoned-{index}.db")
        intent = _authorized()
        _persist(store, intent)
        provider = PoisonedProvider(poisoned)

        outcome = submit_paid_render(
            intent=intent,
            request_payload=_request(),
            provider=provider,
            store=store,
            policy=POLICY,
            spent_today=0.0,
            concurrent_renders=0,
            owner_id="worker-security",
        )

        assert provider.calls == 1
        assert outcome.intent.state == RenderState.RECONCILE_REQUIRED
        assert outcome.intent.provider_job_id is None
        persisted = store.get_intent(intent.intent_id)
        assert persisted is not None
        assert persisted.state == RenderState.RECONCILE_REQUIRED
        assert persisted.provider_job_id is None
