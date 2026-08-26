from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Protocol
import json
import sqlite3

from .render_guard import RenderIntent, RenderState


@dataclass(frozen=True)
class Lease:
    resource_id: str
    owner_id: str
    fencing_token: int
    expires_at: str


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


class SQLiteTransactionalRenderStore:
    """Transactional single-authority store with leases and monotonically increasing fencing tokens.

    SQLite is appropriate for one shared host / filesystem authority. It is intentionally
    *not* advertised as safe across independent hosts or network filesystems. Multi-host
    deployments must implement RenderStateStore against a real transactional database
    (e.g. Postgres) while preserving the fencing semantics in this contract.
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
                """
            )

    def acquire_lease(self, resource_id: str, owner_id: str, ttl_s: float = 30.0) -> Lease:
        if not resource_id or not owner_id or ttl_s <= 0:
            raise ValueError("resource_id, owner_id and positive ttl required")
        now = _utcnow()
        expires = now + timedelta(seconds=ttl_s)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM leases WHERE resource_id=?", (resource_id,)).fetchone()
            if row is not None:
                current_expiry = datetime.fromisoformat(row["expires_at"])
                if current_expiry > now and row["owner_id"] != owner_id:
                    conn.execute("ROLLBACK")
                    raise RuntimeError("resource lease already held")
                token = int(row["fencing_token"]) + 1
            else:
                token = 1
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

    def get_intent(self, intent_id: str) -> RenderIntent | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM intents WHERE intent_id=?", (intent_id,)).fetchone()
        return _intent_from_row(row)

    def event_count(self, intent_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM events WHERE intent_id=?", (intent_id,)).fetchone()
        return int(row["n"])
