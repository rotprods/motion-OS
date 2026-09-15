from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

from src.avatar.provider_submission import SubmissionBlocked, submit_paid_render
from src.avatar.render_guard import RenderState, SpendPolicy, authorize_render
from src.avatar.transactional_store import SQLiteTransactionalRenderStore


POLICY = SpendPolicy(10.0, 100.0, 2, max_retries=1)


def _authorized():
    return authorize_render(
        content_id="CNT_P7",
        profile_id="PROFILE_P7",
        script="hello world",
        explicit_authorization=True,
        preflight_ok=True,
        estimated_credits=2.0,
        spent_today=0.0,
        concurrent_renders=0,
        policy=POLICY,
    )


def _request():
    return {
        "avatarId": "avatar_1",
        "voiceId": "voice_1",
        "script": "hello world",
        "title": "P7 evidence-bound submission",
        "aspectRatio": "9:16",
        "resolution": "1080p",
        "outputFormat": "mp4",
    }


def _persist(store: SQLiteTransactionalRenderStore, intent) -> None:
    lease = store.acquire_lease(intent.intent_id, "seed")
    try:
        store.put_intent(intent, lease)
    finally:
        store.release_lease(lease)


class Provider:
    provider_id = "heygen"

    def __init__(self, *, result=None, exc: Exception | None = None, before_return=None):
        self.result = result if result is not None else {"video_id": "vid_p7", "status": "pending"}
        self.exc = exc
        self.before_return = before_return
        self.calls: list[dict] = []

    def submit(self, payload):
        self.calls.append(dict(payload))
        if self.before_return is not None:
            self.before_return(payload)
        if self.exc is not None:
            raise self.exc
        return self.result


def _submit(store, intent, provider):
    return submit_paid_render(
        intent=intent,
        request_payload=_request(),
        provider=provider,
        store=store,
        policy=POLICY,
        spent_today=0.0,
        concurrent_renders=0,
        owner_id="p7-worker",
    )


def test_request_evidence_is_durable_before_paid_provider_io(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "authority.sqlite")
    intent = _authorized()
    _persist(store, intent)

    observed = {}

    def prove_pre_io_durability(payload):
        current = store.get_intent(intent.intent_id)
        assert current is not None
        assert current.state == RenderState.SUBMITTED
        evidence = store.get_submission_evidence(intent.intent_id, 0)
        assert evidence is not None
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        assert evidence.request_sha256 == hashlib.sha256(canonical).hexdigest()
        assert evidence.request_bytes == len(canonical)
        assert evidence.provider_id == "heygen"
        assert evidence.callback_id == intent.intent_id
        observed["evidence_id"] = evidence.evidence_id

    provider = Provider(before_return=prove_pre_io_durability)
    outcome = _submit(store, intent, provider)

    assert outcome.intent.state == RenderState.ACKNOWLEDGED
    assert outcome.request_sha256 == store.get_submission_evidence(intent.intent_id, 0).request_sha256
    assert store.submission_evidence_count(intent.intent_id) == 1
    assert observed["evidence_id"].startswith("SUBEV_")


def test_timeout_keeps_request_evidence_and_never_persists_raw_request(tmp_path):
    db = tmp_path / "authority.sqlite"
    store = SQLiteTransactionalRenderStore(db)
    intent = _authorized()
    _persist(store, intent)
    provider = Provider(exc=TimeoutError("untrusted upstream failure detail"))

    outcome = _submit(store, intent, provider)
    assert outcome.intent.state == RenderState.RECONCILE_REQUIRED
    assert outcome.failure_type == "TimeoutError"
    assert store.submission_evidence_count(intent.intent_id) == 1

    with sqlite3.connect(db) as conn:
        payloads = [row[0] for row in conn.execute(
            "SELECT payload_json FROM events WHERE intent_id=? ORDER BY seq",
            (intent.intent_id,),
        ).fetchall()]
    assert payloads
    assert all("hello world" not in payload for payload in payloads)
    assert any("submission_evidence" in payload for payload in payloads)


def test_legacy_store_without_atomic_evidence_boundary_is_rejected_before_provider_call():
    class LegacyStore:
        def acquire_lease(self, *args, **kwargs):
            return object()

        def release_lease(self, *args, **kwargs):
            return None

        def get_intent(self, *args, **kwargs):
            return None

        def put_intent(self, *args, **kwargs):
            return None

    intent = _authorized()
    provider = Provider()
    with pytest.raises(SubmissionBlocked, match="put_submitted_with_evidence"):
        submit_paid_render(
            intent=intent,
            request_payload=_request(),
            provider=provider,
            store=LegacyStore(),
            policy=POLICY,
            spent_today=0.0,
            concurrent_renders=0,
            owner_id="p7-worker",
        )
    assert provider.calls == []


def test_reconciliation_after_first_submit_cannot_create_second_spend_generation(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "authority.sqlite")
    intent = _authorized()
    _persist(store, intent)
    first = Provider()
    _submit(store, intent, first)
    assert store.submission_evidence_count(intent.intent_id) == 1

    second = Provider(result={"video_id": "vid_second", "status": "pending"})
    with pytest.raises(SubmissionBlocked, match="requires reconciliation"):
        _submit(store, intent, second)
    assert second.calls == []
    assert store.submission_evidence_count(intent.intent_id) == 1
