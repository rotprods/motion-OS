from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _tree_prefix(uri: str) -> str | None:
    if not uri.startswith("tree:"):
        return None
    raw = uri[len("tree:"):]
    for suffix in ("/**", "/*"):
        if raw.endswith(suffix):
            raw = raw[: -len(suffix)]
            break
    return raw.rstrip("/")


def resources_overlap(left: str, right: str) -> bool:
    """Return whether two canonical resource scopes can address the same mutable unit.

    Exact semantic resources (`contract:`, `schema:`, `capability:`...) overlap only
    when equal. `tree:` scopes overlap descendant `file:`/`tree:` paths.
    """
    if left == right:
        return True

    ltree = _tree_prefix(left)
    rtree = _tree_prefix(right)
    lfile = left[len("file:"):] if left.startswith("file:") else None
    rfile = right[len("file:"):] if right.startswith("file:") else None

    def contains(prefix: str, path: str) -> bool:
        prefix = prefix.rstrip("/")
        path = path.rstrip("/")
        return path == prefix or path.startswith(prefix + "/")

    if ltree is not None and rfile is not None:
        return contains(ltree, rfile)
    if rtree is not None and lfile is not None:
        return contains(rtree, lfile)
    if ltree is not None and rtree is not None:
        return contains(ltree, rtree) or contains(rtree, ltree)
    return False


@dataclass(frozen=True, slots=True)
class Lease:
    lease_id: str
    resource_uri: str
    scope: str
    agent_id: str
    session_id: str
    fencing_token: int
    acquired_at: datetime
    expires_at: datetime
    heartbeat_at: datetime
    expected_revision: str | int | None = None
    status: str = "ACTIVE"

    @property
    def is_writer(self) -> bool:
        return self.scope in {"WRITE", "EXCLUSIVE_WRITE"}

    def expired(self, now: datetime | None = None) -> bool:
        now = now or utc_now()
        return self.status == "ACTIVE" and now >= self.expires_at


class LeaseConflict(RuntimeError):
    pass


class StaleFencingToken(RuntimeError):
    pass


class ReferenceLeaseAuthority:
    """Thread-safe lease/fencing semantics for local contract tests.

    Not a multi-host authority. Production implementation must persist lease rows
    and fencing generations transactionally in PostgreSQL.
    """

    authority_level = "REFERENCE_TEST_ONLY"

    def __init__(self) -> None:
        self._lock = RLock()
        self._leases: dict[str, Lease] = {}
        self._generation: dict[str, int] = {}

    def _expire_locked(self, now: datetime) -> None:
        for lease_id, lease in tuple(self._leases.items()):
            if lease.expired(now):
                self._leases[lease_id] = replace(lease, status="EXPIRED")

    def active(self, now: datetime | None = None) -> tuple[Lease, ...]:
        now = now or utc_now()
        with self._lock:
            self._expire_locked(now)
            return tuple(l for l in self._leases.values() if l.status == "ACTIVE")

    def acquire(
        self,
        *,
        resource_uri: str,
        scope: str,
        agent_id: str,
        session_id: str,
        ttl_seconds: int = 300,
        expected_revision: str | int | None = None,
        now: datetime | None = None,
    ) -> Lease:
        if scope not in {"READ", "WRITE", "EXCLUSIVE_WRITE"}:
            raise ValueError("invalid lease scope")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be > 0")
        now = now or utc_now()

        with self._lock:
            self._expire_locked(now)
            for active in self._leases.values():
                if active.status != "ACTIVE" or not resources_overlap(active.resource_uri, resource_uri):
                    continue
                if scope == "READ" and active.scope != "EXCLUSIVE_WRITE":
                    continue
                if active.scope == "READ" and scope != "EXCLUSIVE_WRITE":
                    continue
                if active.agent_id == agent_id and active.session_id == session_id:
                    raise LeaseConflict("same session already holds an overlapping active lease; renew or release it")
                raise LeaseConflict(
                    f"resource overlaps active {active.scope} lease {active.lease_id} held by {active.agent_id}"
                )

            generation_key = resource_uri
            token = self._generation.get(generation_key, 0) + 1
            self._generation[generation_key] = token
            lease = Lease(
                lease_id=str(uuid4()),
                resource_uri=resource_uri,
                scope=scope,
                agent_id=agent_id,
                session_id=session_id,
                fencing_token=token,
                acquired_at=now,
                expires_at=now + timedelta(seconds=ttl_seconds),
                heartbeat_at=now,
                expected_revision=expected_revision,
            )
            self._leases[lease.lease_id] = lease
            return lease

    def heartbeat(self, lease_id: str, fencing_token: int, *, ttl_seconds: int = 300, now: datetime | None = None) -> Lease:
        now = now or utc_now()
        with self._lock:
            self._expire_locked(now)
            lease = self._leases.get(lease_id)
            if lease is None or lease.status != "ACTIVE":
                raise StaleFencingToken("lease is not active")
            if lease.fencing_token != fencing_token:
                raise StaleFencingToken("fencing token mismatch")
            updated = replace(lease, heartbeat_at=now, expires_at=now + timedelta(seconds=ttl_seconds))
            self._leases[lease_id] = updated
            return updated

    def release(self, lease_id: str, fencing_token: int, *, now: datetime | None = None) -> Lease:
        now = now or utc_now()
        with self._lock:
            self._expire_locked(now)
            lease = self._leases.get(lease_id)
            if lease is None or lease.status != "ACTIVE":
                raise StaleFencingToken("lease is not active")
            if lease.fencing_token != fencing_token:
                raise StaleFencingToken("fencing token mismatch")
            released = replace(lease, status="RELEASED", heartbeat_at=now, expires_at=now)
            self._leases[lease_id] = released
            return released

    def assert_write_authorized(self, lease_id: str, fencing_token: int, resource_uri: str, *, now: datetime | None = None) -> Lease:
        now = now or utc_now()
        with self._lock:
            self._expire_locked(now)
            lease = self._leases.get(lease_id)
            if lease is None or lease.status != "ACTIVE" or not lease.is_writer:
                raise StaleFencingToken("active write lease required")
            if lease.fencing_token != fencing_token:
                raise StaleFencingToken("fencing token mismatch")
            if not resources_overlap(lease.resource_uri, resource_uri):
                raise StaleFencingToken("lease does not cover requested resource")
            return lease


@dataclass(frozen=True, slots=True)
class RevisionedValue:
    value: Any
    revision: int


class RevisionConflict(RuntimeError):
    pass


class ReferenceCASStore:
    """Minimal optimistic-concurrency reference model for contract tests."""

    authority_level = "REFERENCE_TEST_ONLY"

    def __init__(self) -> None:
        self._lock = RLock()
        self._values: dict[str, RevisionedValue] = {}

    def read(self, key: str) -> RevisionedValue | None:
        with self._lock:
            return self._values.get(key)

    def compare_and_set(self, key: str, value: Any, *, expected_revision: int) -> RevisionedValue:
        with self._lock:
            current = self._values.get(key)
            actual = 0 if current is None else current.revision
            if expected_revision != actual:
                raise RevisionConflict(f"expected revision {expected_revision}, actual {actual}")
            updated = RevisionedValue(value=value, revision=actual + 1)
            self._values[key] = updated
            return updated
