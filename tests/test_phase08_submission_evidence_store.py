from dataclasses import replace
import hashlib
import json
import sqlite3

import pytest

from src.avatar.render_guard import RenderIntent, RenderState
from src.avatar.transactional_store import MAX_REQUEST_BYTES, SQLiteTransactionalRenderStore


INTENT_ID = "RND_0123456789ABCDEFGHIJ"
REQUEST = {"script": "Never persist this raw secret: sk-test-DO-NOT-STORE", "callbackId": INTENT_ID}
REQUEST_BYTES = json.dumps(REQUEST, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
REQUEST_SHA = hashlib.sha256(REQUEST_BYTES).hexdigest()


def _intent(state=RenderState.AUTHORIZED, *, retry_count=0, provider_job_id=None):
    return RenderIntent(
        intent_id=INTENT_ID,
        content_id="CNT_1",
        profile_id="heygen_rot_canonical_v1",
        script_hash="a" * 64,
        state=state,
        estimated_credits=2.0,
        provider_job_id=provider_job_id,
        retry_count=retry_count,
    )


def _persist(store, intent):
    lease = store.acquire_lease(intent.intent_id, "seed")
    try:
        store.put_intent(intent, lease)
    finally:
        store.release_lease(lease)


def _submit(store, current, submitted=None, **overrides):
    submitted = submitted or replace(current, state=RenderState.SUBMITTED)
    args = dict(
        expected_current=current,
        request_sha256=REQUEST_SHA,
        provider_id="heygen",
        callback_id=INTENT_ID,
        request_bytes=len(REQUEST_BYTES),
    )
    args.update(overrides)
    lease = store.acquire_lease(INTENT_ID, "submitter")
    try:
        return store.put_submitted_with_evidence(submitted, lease, **args)
    finally:
        store.release_lease(lease)


def test_submitted_transition_and_request_evidence_are_atomic_and_roundtrip(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "authority.sqlite")
    current = _intent()
    _persist(store, current)

    evidence = _submit(store, current)

    persisted = store.get_intent(INTENT_ID)
    assert persisted is not None
    assert persisted.state == RenderState.SUBMITTED
    assert evidence == store.get_submission_evidence(INTENT_ID, 0)
    assert evidence.request_sha256 == REQUEST_SHA
    assert evidence.provider_id == "heygen"
    assert evidence.callback_id == INTENT_ID
    assert evidence.request_bytes == len(REQUEST_BYTES)
    assert evidence.evidence_id.startswith("SUBEV_")
    assert store.submission_evidence_count(INTENT_ID) == 1


def test_submission_event_binds_evidence_without_persisting_raw_request_or_secret(tmp_path):
    db = tmp_path / "authority.sqlite"
    store = SQLiteTransactionalRenderStore(db)
    current = _intent()
    _persist(store, current)
    evidence = _submit(store, current)

    with sqlite3.connect(db) as conn:
        payload = conn.execute(
            "SELECT payload_json FROM events WHERE intent_id=? ORDER BY seq DESC LIMIT 1",
            (INTENT_ID,),
        ).fetchone()[0]

    decoded = json.loads(payload)
    assert decoded["submission_evidence"]["request_sha256"] == REQUEST_SHA
    assert decoded["submission_evidence"]["evidence_id"] == evidence.evidence_id
    assert REQUEST["script"] not in payload
    assert "sk-test-DO-NOT-STORE" not in payload


def test_duplicate_submission_generation_fails_closed_without_extra_event_or_evidence(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "authority.sqlite")
    current = _intent()
    _persist(store, current)
    _submit(store, current)
    events_after_first = store.event_count(INTENT_ID)

    submitted = _intent(RenderState.SUBMITTED)
    lease = store.acquire_lease(INTENT_ID, "duplicate")
    try:
        with pytest.raises((ValueError, RuntimeError)):
            store.put_submitted_with_evidence(
                submitted,
                lease,
                expected_current=submitted,
                request_sha256=REQUEST_SHA,
                provider_id="heygen",
                callback_id=INTENT_ID,
                request_bytes=len(REQUEST_BYTES),
            )
    finally:
        store.release_lease(lease)

    assert store.submission_evidence_count(INTENT_ID) == 1
    assert store.event_count(INTENT_ID) == events_after_first


def test_retry_generation_can_append_exactly_one_new_evidence_record(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "authority.sqlite")
    initial = _intent()
    _persist(store, initial)
    _submit(store, initial)

    failed = _intent(RenderState.FAILED_RETRYABLE, retry_count=0)
    _persist(store, failed)
    retry_submitted = _intent(RenderState.SUBMITTED, retry_count=1)
    retry_sha = hashlib.sha256(b"retry-request").hexdigest()
    second = _submit(
        store,
        failed,
        submitted=retry_submitted,
        request_sha256=retry_sha,
        request_bytes=len(b"retry-request"),
    )

    assert second.retry_count == 1
    assert store.submission_evidence_count(INTENT_ID) == 2
    assert store.get_submission_evidence(INTENT_ID, 0).request_sha256 == REQUEST_SHA
    assert store.get_submission_evidence(INTENT_ID, 1).request_sha256 == retry_sha


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("request_sha256", "A" * 64, "request_sha256"),
        ("request_sha256", "0" * 63, "request_sha256"),
        ("request_sha256", "z" * 64, "request_sha256"),
        ("provider_id", "heygen\npoison", "provider_id"),
        ("provider_id", "HEYGEN", "provider_id"),
        ("provider_id", "other", "bound to heygen"),
        ("callback_id", "foreign-callback", "callback_id"),
        ("request_bytes", True, "request_bytes"),
        ("request_bytes", 0, "request_bytes"),
        ("request_bytes", -1, "request_bytes"),
        ("request_bytes", 1.5, "request_bytes"),
        ("request_bytes", MAX_REQUEST_BYTES + 1, "request_bytes"),
    ],
)
def test_untrusted_submission_metadata_fails_before_state_mutation(tmp_path, field, value, match):
    store = SQLiteTransactionalRenderStore(tmp_path / "authority.sqlite")
    current = _intent()
    _persist(store, current)
    before_events = store.event_count(INTENT_ID)

    with pytest.raises(ValueError, match=match):
        _submit(store, current, **{field: value})

    assert store.get_intent(INTENT_ID) == current
    assert store.submission_evidence_count(INTENT_ID) == 0
    assert store.event_count(INTENT_ID) == before_events


def test_only_submitted_without_provider_job_can_receive_submission_evidence(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "authority.sqlite")
    current = _intent()
    _persist(store, current)

    with pytest.raises(ValueError, match="SUBMITTED"):
        _submit(store, current, submitted=current)

    acknowledged_like = _intent(RenderState.SUBMITTED, provider_job_id="job-1")
    with pytest.raises(ValueError, match="precede provider job"):
        _submit(store, current, submitted=acknowledged_like)


def test_transition_must_match_exact_current_identity_and_retry_generation(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "authority.sqlite")
    current = _intent()
    _persist(store, current)

    changed_script = replace(_intent(RenderState.SUBMITTED), script_hash="b" * 64)
    with pytest.raises(ValueError, match="stable render identity"):
        _submit(store, current, submitted=changed_script)

    bad_retry = _intent(RenderState.SUBMITTED, retry_count=1)
    with pytest.raises(ValueError, match="initial submission retry generation"):
        _submit(store, current, submitted=bad_retry)


def test_stale_fencing_token_cannot_attach_request_evidence(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "authority.sqlite")
    current = _intent()
    _persist(store, current)

    stale = store.acquire_lease(INTENT_ID, "worker")
    store.release_lease(stale)
    fresh = store.acquire_lease(INTENT_ID, "worker")
    try:
        assert fresh.fencing_token > stale.fencing_token
        with pytest.raises(RuntimeError, match="stale fencing token"):
            store.put_submitted_with_evidence(
                _intent(RenderState.SUBMITTED),
                stale,
                expected_current=current,
                request_sha256=REQUEST_SHA,
                provider_id="heygen",
                callback_id=INTENT_ID,
                request_bytes=len(REQUEST_BYTES),
            )
    finally:
        store.release_lease(fresh)

    assert store.get_intent(INTENT_ID) == current
    assert store.submission_evidence_count(INTENT_ID) == 0


def test_expected_current_mismatch_fails_without_overwriting_concurrent_state(tmp_path):
    store = SQLiteTransactionalRenderStore(tmp_path / "authority.sqlite")
    authorized = _intent()
    _persist(store, authorized)
    concurrent = _intent(RenderState.RECONCILE_REQUIRED)
    _persist(store, concurrent)

    lease = store.acquire_lease(INTENT_ID, "stale-submitter")
    try:
        with pytest.raises(RuntimeError, match="changed before submission"):
            store.put_submitted_with_evidence(
                _intent(RenderState.SUBMITTED),
                lease,
                expected_current=authorized,
                request_sha256=REQUEST_SHA,
                provider_id="heygen",
                callback_id=INTENT_ID,
                request_bytes=len(REQUEST_BYTES),
            )
    finally:
        store.release_lease(lease)

    assert store.get_intent(INTENT_ID) == concurrent
    assert store.submission_evidence_count(INTENT_ID) == 0


def test_existing_database_is_additively_migrated_without_losing_intent_history(tmp_path):
    db = tmp_path / "legacy.sqlite"
    with sqlite3.connect(db) as conn:
        conn.executescript(
            """
            CREATE TABLE lease_generations (resource_id TEXT PRIMARY KEY, last_fencing_token INTEGER NOT NULL);
            CREATE TABLE leases (resource_id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, fencing_token INTEGER NOT NULL, expires_at TEXT NOT NULL);
            CREATE TABLE intents (
                intent_id TEXT PRIMARY KEY, content_id TEXT NOT NULL, profile_id TEXT NOT NULL,
                script_hash TEXT NOT NULL, state TEXT NOT NULL, estimated_credits REAL,
                provider_job_id TEXT, retry_count INTEGER NOT NULL DEFAULT 0,
                fencing_token INTEGER NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, intent_id TEXT NOT NULL, state TEXT NOT NULL,
                fencing_token INTEGER NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """
        )
        intent = _intent()
        conn.execute(
            "INSERT INTO intents VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                intent.intent_id,
                intent.content_id,
                intent.profile_id,
                intent.script_hash,
                intent.state.value,
                intent.estimated_credits,
                None,
                0,
                7,
                "2026-08-31T09:00:00+00:00",
            ),
        )
        conn.execute(
            "INSERT INTO events(intent_id,state,fencing_token,payload_json,created_at) VALUES(?,?,?,?,?)",
            (intent.intent_id, intent.state.value, 7, json.dumps(intent.to_dict()), "2026-08-31T09:00:00+00:00"),
        )

    store = SQLiteTransactionalRenderStore(db)
    assert store.get_intent(INTENT_ID) == _intent()
    assert store.event_count(INTENT_ID) == 1
    assert store.submission_evidence_count(INTENT_ID) == 0
    with sqlite3.connect(db) as conn:
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='submission_evidence'"
        ).fetchone()
    assert table == ("submission_evidence",)
