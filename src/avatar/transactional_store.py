from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Protocol
import hashlib
import json
import re
import sqlite3

from .render_guard import RenderIntent, RenderState


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PROVIDER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
MAX_REQUEST_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class Lease:
    resource_id: str
    owner_id: str
    fencing_token: int
    expires_at: str


@dataclass(frozen=True)
class SubmissionEvidence:
    """Immutable evidence for one paid-provider submission generation.

    The raw provider payload is intentionally absent. Only the exact canonical request
    hash plus bounded metadata required to prove which request crossed the spend boundary
    are persisted. `retry_count` is the submission generation and is unique per intent.
    """

    evidence_id: str
    intent_id: str
    retry_count: int
    provider_id: str
    callback_id: str
    request_sha256: str
    request_bytes: int
    fencing_token: int
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "intent_id": self.intent_id,
            "retry_count": self.retry_count,
            "provider_id": self.provider_id,
            "callback_id": self.callback_id,
            "request_sha256": self.request_sha256,
            "request_bytes": self.request_bytes,
            "fencing_token": self.fencing_token,
            "created_at": self.created_at,
        }


class RenderStateStore(Protocol):
    def acquire_lease(self, resource_id: str, owner_id: str, ttl_s: float = 30.0) -> Lease: ...
    def renew_lease(self, lease: Lease, ttl_s: float = 30.0) -> Lease: ...
    def release_lease(self, lease: Lease) -> None: ...
    def put_intent(self, intent: RenderIntent, lease: Lease) -> None: ...
    def get_intent(self, intent_id: str) -> RenderIntent | None: ...


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _intent_from_row(row: sqlite3.Row | None) -> RenderIntent | None:
    if row is None:
        return None
    return RenderIntent(
        intent_id=row["intent_id"],
        content_id=row["content_id"],
        profile_id=row["profile_id"],
        script_hash=row["script_hash"],
        state=RenderState(row["state"]),
        estimated_credits=row["estimated_credits"],
        provider_job_id=row["provider_job_id"],
        retry_count=int(row["retry_count"]),
    )


def _submission_evidence_from_row(row: sqlite3.Row | None) -> SubmissionEvidence | None:
    if row is None:
        return None
    return SubmissionEvidence(
        evidence_id=row["evidence_id"],
        intent_id=row["intent_id"],
        retry_count=int(row["retry_count"]),
        provider_id=row["provider_id"],
        callback_id=row["callback_id"],
        request_sha256=row["request_sha256"],
        request_bytes=int(row["request_bytes"]),
        fencing_token=int(row["fencing_token"]),
        created_at=row["created_at"],
    )


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _submission_evidence_id(
    *,
    intent_id: str,
    retry_count: int,
    provider_id: str,
    callback_id: str,
    request_sha256: str,
    request_bytes: int,
) -> str:
    body = {
        "intent_id": intent_id,
        "retry_count": retry_count,
        "provider_id": provider_id,
        "callback_id": callback_id,
        "request_sha256": request_sha256,
        "request_bytes": request_bytes,
    }
    return "SUBEV_" + hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()[:24].upper()


def _validate_submission_evidence_input(
    *,
    submitted: RenderIntent,
    expected_current: RenderIntent,
    request_sha256: object,
    provider_id: object,
    callback_id: object,
    request_bytes: object,
) -> tuple[str, str, str, int]:
    if not isinstance(submitted, RenderIntent) or not isinstance(expected_current, RenderIntent):
        raise ValueError("submitted and expected_current must be RenderIntent values")
    if submitted.state != RenderState.SUBMITTED:
        raise ValueError("submission evidence requires SUBMITTED intent")
    if submitted.provider_job_id is not None:
        raise ValueError("SUBMITTED evidence must precede provider job acknowledgement")
    if expected_current.intent_id != submitted.intent_id:
        raise ValueError("expected current intent identity mismatch")
    stable_fields = ("content_id", "profile_id", "script_hash", "estimated_credits")
    if any(getattr(expected_current, field) != getattr(submitted, field) for field in stable_fields):
        raise ValueError("submission transition changed stable render identity")
    if expected_current.provider_job_id is not None:
        raise ValueError("provider job already exists; reconcile instead of submitting")
    if expected_current.state == RenderState.AUTHORIZED:
        if submitted.retry_count != expected_current.retry_count:
            raise ValueError("initial submission retry generation mismatch")
    elif expected_current.state == RenderState.FAILED_RETRYABLE:
        if submitted.retry_count != expected_current.retry_count + 1:
            raise ValueError("retry submission generation must advance exactly once")
    else:
        raise ValueError("submission requires AUTHORIZED or FAILED_RETRYABLE durable state")
    if isinstance(submitted.retry_count, bool) or not isinstance(submitted.retry_count, int) or submitted.retry_count < 0:
        raise ValueError("retry_count must be a non-negative integer")

    if not isinstance(request_sha256, str) or _SHA256_RE.fullmatch(request_sha256) is None:
        raise ValueError("request_sha256 must be 64 lowercase hexadecimal characters")
    if not isinstance(provider_id, str) or _PROVIDER_ID_RE.fullmatch(provider_id) is None:
        raise ValueError("provider_id malformed")
    # Current RenderIntent identity generation is explicitly HeyGen-bound. Persisting
    # cross-provider evidence would falsely imply authority the current identity schema
    # cannot prove.
    if provider_id != "heygen":
        raise ValueError("current render intent authority is bound to heygen")
    if not isinstance(callback_id, str) or callback_id != submitted.intent_id:
        raise ValueError("callback_id must exactly equal render intent ID")
    if isinstance(request_bytes, bool) or not isinstance(request_bytes, int):
        raise ValueError("request_bytes must be an integer")
    if request_bytes <= 0 or request_bytes > MAX_REQUEST_BYTES:
        raise ValueError("request_bytes outside allowed bounds")
    return request_sha256, provider_id, callback_id, request_bytes


class SQLiteTransactionalRenderStore:
    """Transactional single-authority store with leases and monotonic fencing tokens.

    SQLite is appropriate for one shared host / filesystem authority. It is intentionally
    *not* advertised as safe across independent hosts or network filesystems. Multi-host
    deployments must implement RenderStateStore against a real transactional database
    while preserving the fencing semantics in this contract.

    Fencing generations live in a separate durable table so releasing a lease never
    resets the token sequence. This is essential: a stale worker must remain fenced out
    even after the previous active lease row has been deleted and ownership is reacquired.
    """

    def __init__(self, path: str | Path, *, timeout_s: float = 5.0) -> None:
        self.path = str(path)
        self.timeout_s = timeout_s
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=self.timeout_s, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS lease_generations (
                    resource_id TEXT PRIMARY KEY,
                    last_fencing_token INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS leases (
                    resource_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    fencing_token INTEGER NOT NULL,
                    expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS intents (
                    intent_id TEXT PRIMARY KEY,
                    content_id TEXT NOT NULL,
                    profile_id TEXT NOT NULL,
                    script_hash TEXT NOT NULL,
                    state TEXT NOT NULL,
                    estimated_credits REAL,
                    provider_job_id TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    fencing_token INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    intent_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    fencing_token INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS submission_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    intent_id TEXT NOT NULL,
                    retry_count INTEGER NOT NULL,
                    provider_id TEXT NOT NULL,
                    callback_id TEXT NOT NULL,
                    request_sha256 TEXT NOT NULL,
                    request_bytes INTEGER NOT NULL,
                    fencing_token INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(intent_id, retry_count),
                    FOREIGN KEY(intent_id) REFERENCES intents(intent_id)
                );
                """
            )

    def acquire_lease(self, resource_id: str, owner_id: str, ttl_s: float = 30.0) -> Lease:
        if not resource_id or not owner_id or ttl_s <= 0:
            raise ValueError("resource_id, owner_id and positive ttl required")
        now = _utcnow()
        expires = now + timedelta(seconds=ttl_s)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            active = conn.execute("SELECT * FROM leases WHERE resource_id=?", (resource_id,)).fetchone()
            if active is not None:
                current_expiry = datetime.fromisoformat(active["expires_at"])
                if current_expiry > now and active["owner_id"] != owner_id:
                    conn.execute("ROLLBACK")
                    raise RuntimeError("resource lease already held")

            generation = conn.execute(
                "SELECT last_fencing_token FROM lease_generations WHERE resource_id=?", (resource_id,)
            ).fetchone()
            token = (int(generation["last_fencing_token"]) if generation is not None else 0) + 1
            conn.execute(
                "INSERT INTO lease_generations(resource_id,last_fencing_token) VALUES(?,?) "
                "ON CONFLICT(resource_id) DO UPDATE SET last_fencing_token=excluded.last_fencing_token",
                (resource_id, token),
            )
            conn.execute(
                "INSERT INTO leases(resource_id, owner_id, fencing_token, expires_at) VALUES(?,?,?,?) "
                "ON CONFLICT(resource_id) DO UPDATE SET owner_id=excluded.owner_id, "
                "fencing_token=excluded.fencing_token, expires_at=excluded.expires_at",
                (resource_id, owner_id, token, _iso(expires)),
            )
            conn.execute("COMMIT")
        return Lease(resource_id, owner_id, token, _iso(expires))

    def _assert_live_lease(self, conn: sqlite3.Connection, lease: Lease) -> None:
        row = conn.execute("SELECT * FROM leases WHERE resource_id=?", (lease.resource_id,)).fetchone()
        if row is None:
            raise RuntimeError("lease missing")
        if row["owner_id"] != lease.owner_id or int(row["fencing_token"]) != lease.fencing_token:
            raise RuntimeError("stale fencing token")
        if datetime.fromisoformat(row["expires_at"]) <= _utcnow():
            raise RuntimeError("lease expired")

    def renew_lease(self, lease: Lease, ttl_s: float = 30.0) -> Lease:
        if ttl_s <= 0:
            raise ValueError("positive ttl required")
        expires = _utcnow() + timedelta(seconds=ttl_s)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._assert_live_lease(conn, lease)
            conn.execute("UPDATE leases SET expires_at=? WHERE resource_id=?", (_iso(expires), lease.resource_id))
            conn.execute("COMMIT")
        return Lease(lease.resource_id, lease.owner_id, lease.fencing_token, _iso(expires))

    def release_lease(self, lease: Lease) -> None:
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._assert_live_lease(conn, lease)
            # Delete only the active ownership row. `lease_generations` remains durable so
            # the next owner receives a strictly larger fencing token.
            conn.execute("DELETE FROM leases WHERE resource_id=?", (lease.resource_id,))
            conn.execute("COMMIT")

    def put_intent(self, intent: RenderIntent, lease: Lease) -> None:
        if lease.resource_id != intent.intent_id:
            raise ValueError("lease resource must equal render intent ID")
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._assert_live_lease(conn, lease)
            existing = conn.execute("SELECT * FROM intents WHERE intent_id=?", (intent.intent_id,)).fetchone()
            if existing is not None and int(existing["fencing_token"]) > lease.fencing_token:
                conn.execute("ROLLBACK")
                raise RuntimeError("write rejected by newer fencing token")
            now = _iso(_utcnow())
            conn.execute(
                "INSERT INTO intents(intent_id,content_id,profile_id,script_hash,state,estimated_credits,provider_job_id,retry_count,fencing_token,updated_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(intent_id) DO UPDATE SET "
                "state=excluded.state,estimated_credits=excluded.estimated_credits,provider_job_id=excluded.provider_job_id,"
                "retry_count=excluded.retry_count,fencing_token=excluded.fencing_token,updated_at=excluded.updated_at",
                (intent.intent_id,intent.content_id,intent.profile_id,intent.script_hash,intent.state.value,
                 intent.estimated_credits,intent.provider_job_id,intent.retry_count,lease.fencing_token,now),
            )
            conn.execute(
                "INSERT INTO events(intent_id,state,fencing_token,payload_json,created_at) VALUES(?,?,?,?,?)",
                (intent.intent_id,intent.state.value,lease.fencing_token,json.dumps(intent.to_dict(),sort_keys=True),now),
            )
            conn.execute("COMMIT")

    def put_submitted_with_evidence(
        self,
        submitted: RenderIntent,
        lease: Lease,
        *,
        expected_current: RenderIntent,
        request_sha256: str,
        provider_id: str,
        callback_id: str,
        request_bytes: int,
    ) -> SubmissionEvidence:
        """Atomically persist the one-way SUBMITTED transition and exact request evidence.

        The same `(intent_id, retry_count)` generation may cross the paid-provider
        boundary at most once. Even an identical replay fails closed: after SUBMITTED the
        correct operation is reconciliation, never an idempotency assumption about spend.
        """
        request_sha256, provider_id, callback_id, request_bytes = _validate_submission_evidence_input(
            submitted=submitted,
            expected_current=expected_current,
            request_sha256=request_sha256,
            provider_id=provider_id,
            callback_id=callback_id,
            request_bytes=request_bytes,
        )
        if lease.resource_id != submitted.intent_id:
            raise ValueError("lease resource must equal render intent ID")

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._assert_live_lease(conn, lease)
            current_row = conn.execute("SELECT * FROM intents WHERE intent_id=?", (submitted.intent_id,)).fetchone()
            current = _intent_from_row(current_row)
            if current != expected_current:
                conn.execute("ROLLBACK")
                raise RuntimeError("persisted render intent changed before submission")
            if current_row is not None and int(current_row["fencing_token"]) > lease.fencing_token:
                conn.execute("ROLLBACK")
                raise RuntimeError("write rejected by newer fencing token")
            duplicate = conn.execute(
                "SELECT evidence_id FROM submission_evidence WHERE intent_id=? AND retry_count=?",
                (submitted.intent_id, submitted.retry_count),
            ).fetchone()
            if duplicate is not None:
                conn.execute("ROLLBACK")
                raise RuntimeError("submission generation already has durable request evidence; reconcile instead")

            now = _iso(_utcnow())
            evidence = SubmissionEvidence(
                evidence_id=_submission_evidence_id(
                    intent_id=submitted.intent_id,
                    retry_count=submitted.retry_count,
                    provider_id=provider_id,
                    callback_id=callback_id,
                    request_sha256=request_sha256,
                    request_bytes=request_bytes,
                ),
                intent_id=submitted.intent_id,
                retry_count=submitted.retry_count,
                provider_id=provider_id,
                callback_id=callback_id,
                request_sha256=request_sha256,
                request_bytes=request_bytes,
                fencing_token=lease.fencing_token,
                created_at=now,
            )
            conn.execute(
                "INSERT INTO intents(intent_id,content_id,profile_id,script_hash,state,estimated_credits,provider_job_id,retry_count,fencing_token,updated_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(intent_id) DO UPDATE SET "
                "state=excluded.state,estimated_credits=excluded.estimated_credits,provider_job_id=excluded.provider_job_id,"
                "retry_count=excluded.retry_count,fencing_token=excluded.fencing_token,updated_at=excluded.updated_at",
                (
                    submitted.intent_id,
                    submitted.content_id,
                    submitted.profile_id,
                    submitted.script_hash,
                    submitted.state.value,
                    submitted.estimated_credits,
                    submitted.provider_job_id,
                    submitted.retry_count,
                    lease.fencing_token,
                    now,
                ),
            )
            conn.execute(
                "INSERT INTO submission_evidence(evidence_id,intent_id,retry_count,provider_id,callback_id,request_sha256,request_bytes,fencing_token,created_at) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    evidence.evidence_id,
                    evidence.intent_id,
                    evidence.retry_count,
                    evidence.provider_id,
                    evidence.callback_id,
                    evidence.request_sha256,
                    evidence.request_bytes,
                    evidence.fencing_token,
                    evidence.created_at,
                ),
            )
            event_payload = submitted.to_dict()
            event_payload["submission_evidence"] = evidence.to_dict()
            conn.execute(
                "INSERT INTO events(intent_id,state,fencing_token,payload_json,created_at) VALUES(?,?,?,?,?)",
                (
                    submitted.intent_id,
                    submitted.state.value,
                    lease.fencing_token,
                    json.dumps(event_payload, sort_keys=True, separators=(",", ":")),
                    now,
                ),
            )
            conn.execute("COMMIT")
        return evidence

    def get_intent(self, intent_id: str) -> RenderIntent | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM intents WHERE intent_id=?", (intent_id,)).fetchone()
        return _intent_from_row(row)

    def get_submission_evidence(self, intent_id: str, retry_count: int) -> SubmissionEvidence | None:
        if not isinstance(intent_id, str) or not intent_id:
            raise ValueError("intent_id required")
        if isinstance(retry_count, bool) or not isinstance(retry_count, int) or retry_count < 0:
            raise ValueError("retry_count must be a non-negative integer")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM submission_evidence WHERE intent_id=? AND retry_count=?",
                (intent_id, retry_count),
            ).fetchone()
        return _submission_evidence_from_row(row)

    def submission_evidence_count(self, intent_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM submission_evidence WHERE intent_id=?",
                (intent_id,),
            ).fetchone()
        return int(row["n"])

    def event_count(self, intent_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM events WHERE intent_id=?", (intent_id,)).fetchone()
        return int(row["n"])

    def current_fencing_token(self, resource_id: str) -> int | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT last_fencing_token FROM lease_generations WHERE resource_id=?", (resource_id,)
            ).fetchone()
        return int(row["last_fencing_token"]) if row is not None else None
