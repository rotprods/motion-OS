from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any

from .integrity import sha256_json


class ReplicaStatus(str, Enum):
    MATCH = "MATCH"
    STALE_REPLICA = "STALE_REPLICA"
    CONFLICT = "CONFLICT"
    MISSING = "MISSING"


@dataclass(frozen=True)
class ReplicaDigest:
    replica: str
    revision: int | None
    content_hash: str | None
    available: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_replica_digest(replica: str, payload: Any | None, *, revision: int | None) -> ReplicaDigest:
    if payload is None:
        return ReplicaDigest(replica=replica, revision=revision, content_hash=None, available=False)
    return ReplicaDigest(replica=replica, revision=revision, content_hash=sha256_json(payload), available=True)


def reconcile(canonical: ReplicaDigest, replica: ReplicaDigest) -> ReplicaStatus:
    if not replica.available:
        return ReplicaStatus.MISSING
    if not canonical.available:
        raise ValueError("canonical replica unavailable; automatic reconciliation forbidden")
    if replica.content_hash == canonical.content_hash:
        return ReplicaStatus.MATCH
    if canonical.revision is not None and replica.revision is not None:
        if replica.revision < canonical.revision:
            return ReplicaStatus.STALE_REPLICA
        if replica.revision > canonical.revision:
            return ReplicaStatus.CONFLICT
    return ReplicaStatus.CONFLICT


def reconciliation_report(canonical: ReplicaDigest, replicas: list[ReplicaDigest]) -> dict[str, Any]:
    states = {r.replica: reconcile(canonical, r).value for r in replicas}
    refresh_candidates = [
        name
        for name, state in states.items()
        if state in {ReplicaStatus.STALE_REPLICA.value, ReplicaStatus.MISSING.value}
    ]
    conflicts = [name for name, state in states.items() if state == ReplicaStatus.CONFLICT.value]

    # A stale/missing replica is only "safe" to consider for an explicitly authorized
    # refresh when the reconciliation set contains no conflicting newer/divergent claim.
    # The report itself remains advisory and never performs a write.
    safe_to_refresh = [] if conflicts else list(refresh_candidates)

    return {
        "canonical": canonical.to_dict(),
        "replicas": [r.to_dict() for r in replicas],
        "states": states,
        "refresh_candidates": refresh_candidates,
        "safe_to_refresh": safe_to_refresh,
        "conflicts": conflicts,
        # Reconciliation is evidence/advice only. A caller must explicitly authorize
        # any Drive/Library/GitHub mutation after reviewing the report.
        "automatic_write_allowed": False,
        "write_requires_explicit_authorization": True,
    }
