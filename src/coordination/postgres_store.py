from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol, Sequence

from .events import CoordinationEvent


class CursorLike(Protocol):
    def execute(self, query: str, params: Sequence[Any] | None = None) -> Any: ...
    def fetchone(self) -> Any: ...
    def fetchall(self) -> list[Any]: ...
    def __enter__(self) -> "CursorLike": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...


class ConnectionLike(Protocol):
    def cursor(self) -> CursorLike: ...
    def __enter__(self) -> "ConnectionLike": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...


ConnectionFactory = Callable[[], ConnectionLike]


@dataclass(frozen=True, slots=True)
class AppendOutcome:
    event_id: str
    duplicate: bool


@dataclass(frozen=True, slots=True)
class OutboxItem:
    outbox_id: int
    event_id: str
    topic: str
    attempts: int
    lock_owner: str | None


class PostgresCoordinationStore:
    """Thin adapter over Phase07 PostgreSQL functions.

    The adapter deliberately delegates concurrency-critical semantics to SQL
    functions executed inside PostgreSQL transactions. It does not maintain
    process-local authority state.

    A concrete psycopg/asyncpg connection factory can be injected by the runtime;
    no database driver is forced into MOTION.OS core dependencies.
    """

    authority_level = "POSTGRES_MULTI_HOST_CANDIDATE_UNVERIFIED"

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def append_event(self, event: CoordinationEvent, *, topic: str = "motion.coordination") -> AppendOutcome:
        git = dict(event.git) if event.git else None
        params = (
            event.event_id,
            event.schema_version,
            event.event_type,
            event.aggregate_type,
            event.aggregate_id,
            event.project_id,
            event.run_id,
            event.session_id,
            event.agent_id,
            event.causation_id,
            event.correlation_id,
            None if event.expected_revision is None else str(event.expected_revision),
            event.occurred_at,
            dict(event.payload),
            list(event.evidence_refs),
            git,
            event.provenance_hash,
            event.sensitivity,
            topic,
        )
        sql = """
            select event_id::text, duplicate
              from append_coordination_event(
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,
                %s::jsonb,%s,%s,%s
              )
        """
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("append_coordination_event returned no row")
                return AppendOutcome(event_id=str(row[0]), duplicate=bool(row[1]))

    def read_events(
        self,
        *,
        project_id: str,
        after_recorded_at: str | None = None,
        after_event_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        if (after_recorded_at is None) != (after_event_id is None):
            raise ValueError("after_recorded_at and after_event_id must be supplied together")

        if after_recorded_at is None:
            sql = """
                select event_id::text, schema_version, event_type, aggregate_type,
                       aggregate_id, project_id, run_id, session_id, agent_id,
                       causation_id::text, correlation_id, expected_revision,
                       occurred_at, recorded_at, payload, evidence_refs, git_meta,
                       provenance_hash, sensitivity
                  from coordination_events
                 where project_id=%s
                 order by recorded_at, event_id
                 limit %s
            """
            params: tuple[Any, ...] = (project_id, limit)
        else:
            sql = """
                select event_id::text, schema_version, event_type, aggregate_type,
                       aggregate_id, project_id, run_id, session_id, agent_id,
                       causation_id::text, correlation_id, expected_revision,
                       occurred_at, recorded_at, payload, evidence_refs, git_meta,
                       provenance_hash, sensitivity
                  from coordination_events
                 where project_id=%s
                   and (recorded_at, event_id) > (%s::timestamptz, %s::uuid)
                 order by recorded_at, event_id
                 limit %s
            """
            params = (project_id, after_recorded_at, after_event_id, limit)

        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

        columns = (
            "event_id", "schema_version", "event_type", "aggregate_type",
            "aggregate_id", "project_id", "run_id", "session_id", "agent_id",
            "causation_id", "correlation_id", "expected_revision", "occurred_at",
            "recorded_at", "payload", "evidence_refs", "git_meta",
            "provenance_hash", "sensitivity",
        )
        return [dict(zip(columns, row, strict=True)) for row in rows]

    def acknowledge_consumer(
        self,
        *,
        consumer_id: str,
        project_id: str,
        recorded_at: str,
        event_id: str,
    ) -> None:
        sql = "select * from acknowledge_coordination_consumer(%s,%s,%s::timestamptz,%s::uuid)"
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (consumer_id, project_id, recorded_at, event_id))
                if cur.fetchone() is None:
                    raise RuntimeError("consumer acknowledgement returned no row")

    def acquire_lease(
        self,
        *,
        project_id: str,
        resource_uri: str,
        scope: str,
        agent_id: str,
        session_id: str,
        ttl_seconds: int = 300,
        expected_revision: str | None = None,
    ) -> tuple[str, int]:
        sql = """
            select lease_id::text, fencing_token
              from acquire_resource_lease(%s,%s,%s,%s,%s,%s,%s)
        """
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    project_id, resource_uri, scope, agent_id, session_id,
                    ttl_seconds, expected_revision,
                ))
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("lease acquisition returned no row")
                return str(row[0]), int(row[1])

    def heartbeat_lease(self, lease_id: str, fencing_token: int, *, ttl_seconds: int = 300) -> None:
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select lease_id from heartbeat_resource_lease(%s::uuid,%s,%s)",
                    (lease_id, fencing_token, ttl_seconds),
                )
                if cur.fetchone() is None:
                    raise RuntimeError("lease heartbeat returned no row")

    def release_lease(self, lease_id: str, fencing_token: int) -> None:
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select lease_id from release_resource_lease(%s::uuid,%s)",
                    (lease_id, fencing_token),
                )
                if cur.fetchone() is None:
                    raise RuntimeError("lease release returned no row")

    def claim_outbox(self, *, worker_id: str, limit: int = 100, lease_seconds: int = 30) -> list[OutboxItem]:
        sql = """
            select outbox_id, event_id::text, topic, attempts, lock_owner
              from claim_coordination_outbox(%s,%s,%s)
        """
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (worker_id, limit, lease_seconds))
                rows = cur.fetchall()
        return [OutboxItem(int(r[0]), str(r[1]), str(r[2]), int(r[3]), r[4]) for r in rows]

    def mark_outbox_published(self, *, worker_id: str, outbox_id: int) -> None:
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select outbox_id from mark_coordination_outbox_published(%s,%s)",
                    (worker_id, outbox_id),
                )
                if cur.fetchone() is None:
                    raise RuntimeError("outbox publish acknowledgement returned no row")

    def mark_outbox_failed(self, *, worker_id: str, outbox_id: int, error: str) -> None:
        with self._connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select outbox_id from mark_coordination_outbox_failed(%s,%s,%s)",
                    (worker_id, outbox_id, error),
                )
                if cur.fetchone() is None:
                    raise RuntimeError("outbox failure acknowledgement returned no row")
