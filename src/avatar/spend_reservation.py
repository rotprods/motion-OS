from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from numbers import Real
from pathlib import Path
import hashlib
import json
import math
import sqlite3

from .render_guard import RenderIntent, RenderState, SpendPolicy
from .transactional_store import Lease, SQLiteTransactionalRenderStore


@dataclass(frozen=True, slots=True)
class SpendReservation:
    reservation_id: str
    intent_id: str
    retry_count: int
    estimated_credits: float
    spend_day: str
    active: bool
    created_at: str


class SQLitePaidRenderAuthorityStore(SQLiteTransactionalRenderStore):
    """Single-host paid-render authority with durable global spend/capacity reservations.

    Reservations are committed before provider I/O and are global across all intents
    sharing this SQLite authority. The ledger is deliberately conservative: a reserved
    submission generation continues to count toward the daily budget even if a later
    local step fails, because a crash/ambiguous boundary must never create permission to
    spend the same budget again. Active concurrency is released only after durable state
    proves the provider generation is no longer active (completed, final-failed, or
    explicitly safe-to-retry).
    """

    _NONACTIVE_STATES = frozenset({
        RenderState.COMPLETED,
        RenderState.FAILED_FINAL,
        RenderState.FAILED_RETRYABLE,
    })

    def _init_db(self) -> None:
        super()._init_db()
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS spend_reservations (
                    reservation_id TEXT PRIMARY KEY,
                    intent_id TEXT NOT NULL,
                    retry_count INTEGER NOT NULL,
                    estimated_credits REAL NOT NULL,
                    spend_day TEXT NOT NULL,
                    active INTEGER NOT NULL CHECK(active IN (0,1)),
                    created_at TEXT NOT NULL,
                    released_at TEXT,
                    UNIQUE(intent_id, retry_count)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_spend_reservations_day ON spend_reservations(spend_day)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_spend_reservations_active ON spend_reservations(active)"
            )

    @staticmethod
    def _stable_identity(intent: RenderIntent) -> tuple[object, ...]:
        return (
            intent.intent_id,
            intent.content_id,
            intent.profile_id,
            intent.script_hash,
            intent.estimated_credits,
        )

    def put_intent(self, intent: RenderIntent, lease: Lease) -> None:
        """Persist state without allowing identity drift; non-active states free capacity.

        `intent_id` is a content/profile/script-derived identity. Reusing it with changed
        stable fields would make the row and append-only event payload disagree. The
        paid authority store rejects that mutation before the parent store writes it.
        A FAILED_RETRYABLE generation is explicitly safe to retry and therefore cannot
        continue occupying a provider concurrency slot; ambiguous outcomes remain in
        RECONCILE_REQUIRED and deliberately keep their reservation active.
        """
        existing = self.get_intent(intent.intent_id)
        if existing is not None and self._stable_identity(existing) != self._stable_identity(intent):
            raise RuntimeError("render intent stable identity changed")
        super().put_intent(intent, lease)
        if intent.state in self._NONACTIVE_STATES:
            self.release_inactive_concurrency(intent)

    @staticmethod
    def _finite_nonnegative(value: object, name: str) -> float:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{name} must be a finite non-negative number")
        normalized = float(value)
        if not math.isfinite(normalized) or normalized < 0:
            raise ValueError(f"{name} must be a finite non-negative number")
        return normalized

    @staticmethod
    def _nonnegative_int(value: object, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
        return value

    @staticmethod
    def _reservation_id(intent: RenderIntent, spend_day: str) -> str:
        payload = {
            "intent_id": intent.intent_id,
            "retry_count": intent.retry_count,
            "estimated_credits": intent.estimated_credits,
            "spend_day": spend_day,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()
        return "SPEND_" + digest[:24].upper()

    def reserve_spend(
        self,
        intent: RenderIntent,
        *,
        policy: SpendPolicy,
        observed_spent_today: float,
        observed_concurrent_renders: int,
    ) -> SpendReservation:
        if not isinstance(intent, RenderIntent) or intent.state != RenderState.AUTHORIZED:
            raise ValueError("spend reservation requires AUTHORIZED render intent")
        if not isinstance(policy, SpendPolicy):
            raise ValueError("policy must be a SpendPolicy")
        credits = self._finite_nonnegative(intent.estimated_credits, "estimated_credits")
        observed_spent = self._finite_nonnegative(observed_spent_today, "observed_spent_today")
        observed_concurrent = self._nonnegative_int(
            observed_concurrent_renders, "observed_concurrent_renders"
        )
        retry_count = self._nonnegative_int(intent.retry_count, "retry_count")
        if credits > policy.max_credits_per_render:
            raise RuntimeError("per-render credit budget exceeded")

        now = datetime.now(timezone.utc)
        spend_day = now.date().isoformat()
        created_at = now.isoformat()
        reservation_id = self._reservation_id(intent, spend_day)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            duplicate = conn.execute(
                "SELECT reservation_id FROM spend_reservations WHERE intent_id=? AND retry_count=?",
                (intent.intent_id, retry_count),
            ).fetchone()
            if duplicate is not None:
                conn.execute("ROLLBACK")
                raise RuntimeError("submission generation already has a durable spend reservation")

            row = conn.execute(
                "SELECT COALESCE(SUM(estimated_credits),0.0) AS spent FROM spend_reservations WHERE spend_day=?",
                (spend_day,),
            ).fetchone()
            durable_spent = float(row["spent"])
            row = conn.execute(
                "SELECT COUNT(*) AS active_count FROM spend_reservations WHERE active=1"
            ).fetchone()
            durable_concurrent = int(row["active_count"])
            effective_spent = max(durable_spent, observed_spent)
            effective_concurrent = max(durable_concurrent, observed_concurrent)

            if effective_concurrent >= policy.max_concurrent_renders:
                conn.execute("ROLLBACK")
                raise RuntimeError("concurrent render limit reached")
            if effective_spent + credits > policy.max_credits_per_day:
                conn.execute("ROLLBACK")
                raise RuntimeError("daily credit budget exceeded")

            conn.execute(
                "INSERT INTO spend_reservations(reservation_id,intent_id,retry_count,estimated_credits,spend_day,active,created_at) "
                "VALUES(?,?,?,?,?,1,?)",
                (reservation_id, intent.intent_id, retry_count, credits, spend_day, created_at),
            )
            conn.execute("COMMIT")
        return SpendReservation(
            reservation_id=reservation_id,
            intent_id=intent.intent_id,
            retry_count=retry_count,
            estimated_credits=credits,
            spend_day=spend_day,
            active=True,
            created_at=created_at,
        )

    def release_spend_concurrency(self, reservation: SpendReservation) -> None:
        if not isinstance(reservation, SpendReservation):
            raise ValueError("reservation must be SpendReservation")
        released_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM spend_reservations WHERE reservation_id=?",
                (reservation.reservation_id,),
            ).fetchone()
            if row is None:
                conn.execute("ROLLBACK")
                raise RuntimeError("spend reservation missing")
            if (
                row["intent_id"] != reservation.intent_id
                or int(row["retry_count"]) != reservation.retry_count
                or float(row["estimated_credits"]) != reservation.estimated_credits
                or row["spend_day"] != reservation.spend_day
            ):
                conn.execute("ROLLBACK")
                raise RuntimeError("spend reservation identity mismatch")
            if int(row["active"]) == 1:
                conn.execute(
                    "UPDATE spend_reservations SET active=0,released_at=? WHERE reservation_id=?",
                    (released_at, reservation.reservation_id),
                )
            conn.execute("COMMIT")

    def release_inactive_concurrency(self, intent: RenderIntent) -> None:
        if not isinstance(intent, RenderIntent) or intent.state not in self._NONACTIVE_STATES:
            raise ValueError("concurrency release requires a non-active RenderIntent state")
        retry_count = self._nonnegative_int(intent.retry_count, "retry_count")
        released_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE spend_reservations SET active=0,released_at=? "
                "WHERE intent_id=? AND retry_count=? AND active=1",
                (released_at, intent.intent_id, retry_count),
            )
            conn.execute("COMMIT")

    def spent_for_day(self, spend_day: str | None = None) -> float:
        day = spend_day or datetime.now(timezone.utc).date().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(estimated_credits),0.0) AS spent FROM spend_reservations WHERE spend_day=?",
                (day,),
            ).fetchone()
        return float(row["spent"])

    def active_spend_reservation_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS active_count FROM spend_reservations WHERE active=1"
            ).fetchone()
        return int(row["active_count"])

    def spend_reservation_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM spend_reservations").fetchone()
        return int(row["n"])
