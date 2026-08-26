from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import threading
from typing import Callable

from .contracts import AgentEvent, LeaseToken, utc_now_iso


class CoordinationError(RuntimeError):
    pass


class IdempotencyConflict(CoordinationError):
    pass


class RevisionConflict(CoordinationError):
    pass


class LeaseConflict(CoordinationError):
    pass


class StaleWriter(CoordinationError):
    pass


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReferenceCoordinationStore:
    """Thread-safe semantic reference for the future network event kernel.

    This class is intentionally process-local. It proves state-transition semantics
    and is NOT multi-host authority. Postgres/Supabase must preserve these contracts.
    """

    def __init__(self, now: Callable[[], datetime] = _utc_now) -> None:
        self._lock = threading.RLock()
        self._now = now
        self._events: list[AgentEvent] = []
        self._idempotency: dict[tuple[str, str], AgentEvent] = {}
        self._heads: dict[tuple[str, str, str], int] = {}
        self._leases: dict[tuple[str, str], LeaseToken] = {}
        self._lease_generations: dict[tuple[str, str], int] = {}

    def append_event(self, event: AgentEvent) -> AgentEvent:
        with self._lock:
            idem_key = (event.project_id, event.idempotency_key)
            existing = self._idempotency.get(idem_key)
            if existing is not None:
                if (
                    existing.event_type != event.event_type
                    or existing.aggregate_type != event.aggregate_type
                    or existing.aggregate_id != event.aggregate_id
                    or existing.payload_hash != event.payload_hash
                ):
                    raise IdempotencyConflict(
                        f"idempotency key {event.idempotency_key!r} reused with different logical command"
                    )
                return existing

            head_key = (event.project_id, event.aggregate_type, event.aggregate_id)
            current_revision = self._heads.get(head_key, 0)
            if event.expected_revision is not None and event.expected_revision != current_revision:
                raise RevisionConflict(
                    f"expected revision {event.expected_revision}, current {current_revision}"
                )
            required_revision = current_revision + 1
            if event.aggregate_revision != required_revision:
                raise RevisionConflict(
                    f"event revision {event.aggregate_revision}, required {required_revision}"
                )

            self._events.append(event)
            self._heads[head_key] = event.aggregate_revision
            self._idempotency[idem_key] = event
            return event

    def aggregate_revision(self, project_id: str, aggregate_type: str, aggregate_id: str) -> int:
        with self._lock:
            return self._heads.get((project_id, aggregate_type, aggregate_id), 0)

    def events(self) -> tuple[AgentEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def acquire_lease(
        self,
        *,
        project_id: str,
        resource_key: str,
        owner_agent_id: str,
        session_id: str,
        workstream_id: str,
        ttl_seconds: int,
        expected_state_version: int | None = None,
    ) -> LeaseToken:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be > 0")
        with self._lock:
            key = (project_id, resource_key)
            now = self._now()
            existing = self._leases.get(key)
            if existing is not None and _parse_ts(existing.expires_at) > now:
                raise LeaseConflict(
                    f"resource {resource_key!r} held by {existing.owner_agent_id} generation {existing.generation}"
                )

            generation = self._lease_generations.get(key, 0) + 1
            token = LeaseToken(
                lease_id=f"lease:{resource_key}:{generation}",
                resource_key=resource_key,
                owner_agent_id=owner_agent_id,
                session_id=session_id,
                workstream_id=workstream_id,
                generation=generation,
                acquired_at=now.isoformat().replace("+00:00", "Z"),
                expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z"),
                expected_state_version=expected_state_version,
            )
            self._leases[key] = token
            self._lease_generations[key] = generation
            return token

    def heartbeat_lease(
        self,
        *,
        project_id: str,
        resource_key: str,
        owner_agent_id: str,
        session_id: str,
        generation: int,
        ttl_seconds: int,
    ) -> LeaseToken:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be > 0")
        with self._lock:
            current = self._assert_fence_locked(
                project_id=project_id,
                resource_key=resource_key,
                owner_agent_id=owner_agent_id,
                session_id=session_id,
                generation=generation,
            )
            now = self._now()
            renewed = replace(
                current,
                expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z"),
            )
            self._leases[(project_id, resource_key)] = renewed
            return renewed

    def release_lease(
        self,
        *,
        project_id: str,
        resource_key: str,
        owner_agent_id: str,
        session_id: str,
        generation: int,
    ) -> None:
        with self._lock:
            self._assert_fence_locked(
                project_id=project_id,
                resource_key=resource_key,
                owner_agent_id=owner_agent_id,
                session_id=session_id,
                generation=generation,
                allow_expired=True,
            )
            self._leases.pop((project_id, resource_key), None)

    def assert_write_authority(
        self,
        *,
        project_id: str,
        resource_key: str,
        owner_agent_id: str,
        session_id: str,
        generation: int,
    ) -> LeaseToken:
        with self._lock:
            return self._assert_fence_locked(
                project_id=project_id,
                resource_key=resource_key,
                owner_agent_id=owner_agent_id,
                session_id=session_id,
                generation=generation,
            )

    def _assert_fence_locked(
        self,
        *,
        project_id: str,
        resource_key: str,
        owner_agent_id: str,
        session_id: str,
        generation: int,
        allow_expired: bool = False,
    ) -> LeaseToken:
        current = self._leases.get((project_id, resource_key))
        if current is None:
            raise StaleWriter(f"no active lease for {resource_key!r}")
        if current.generation != generation:
            raise StaleWriter(
                f"stale generation {generation}; current generation is {current.generation}"
            )
        if current.owner_agent_id != owner_agent_id or current.session_id != session_id:
            raise StaleWriter("lease owner/session mismatch")
        if not allow_expired and _parse_ts(current.expires_at) <= self._now():
            raise StaleWriter("lease expired")
        return current
