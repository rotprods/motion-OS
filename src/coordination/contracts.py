from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable

PROJECT_ID = "motion://project/motion-os"
SCHEMA_VERSION = "1.0.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Stable JSON representation used for evidence/event hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def require_uri(value: str, prefix: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.startswith(prefix):
        raise ValueError(f"{field_name} must start with {prefix!r}")


@dataclass(frozen=True)
class ProvenanceRef:
    source_type: str
    source_id: str
    revision: str | None = None
    sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.source_type or not self.source_id:
            raise ValueError("provenance source_type/source_id are required")
        if self.sha256 is not None and (len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256)):
            raise ValueError("provenance sha256 must be lowercase hex")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "revision": self.revision,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class AgentEvent:
    event_id: str
    actor_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    aggregate_revision: int
    correlation_id: str
    idempotency_key: str
    payload: dict[str, Any]
    provenance: tuple[ProvenanceRef, ...]
    session_id: str | None = None
    expected_revision: int | None = None
    causation_id: str | None = None
    parent_event_ids: tuple[str, ...] = ()
    workstream_id: str | None = None
    resource_scope: tuple[str, ...] = ()
    observed_at: str | None = None
    recorded_at: str = field(default_factory=utc_now_iso)
    project_id: str = PROJECT_ID
    schema_version: str = SCHEMA_VERSION
    sensitivity: str = "INTERNAL"
    evidence: tuple[str, ...] = ()
    git: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        require_uri(self.project_id, "motion://project/", "project_id")
        require_uri(self.actor_id, "motion://agent/", "actor_id")
        if self.session_id is not None:
            require_uri(self.session_id, "motion://session/", "session_id")
        if not self.event_id or not self.correlation_id or not self.idempotency_key:
            raise ValueError("event_id, correlation_id and idempotency_key are required")
        if self.aggregate_revision < 0:
            raise ValueError("aggregate_revision cannot be negative")
        if self.expected_revision is not None and self.expected_revision < 0:
            raise ValueError("expected_revision cannot be negative")
        if not self.event_type or self.event_type.upper() != self.event_type:
            raise ValueError("event_type must be upper-case")
        if not self.provenance:
            raise ValueError("at least one provenance reference is required")
        if self.sensitivity not in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
            raise ValueError("invalid sensitivity")
        if len(set(self.parent_event_ids)) != len(self.parent_event_ids):
            raise ValueError("parent_event_ids must be unique")

    @property
    def payload_hash(self) -> str:
        return sha256_json(self.payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "project_id": self.project_id,
            "actor_id": self.actor_id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "aggregate_revision": self.aggregate_revision,
            "expected_revision": self.expected_revision,
            "causation_id": self.causation_id,
            "correlation_id": self.correlation_id,
            "parent_event_ids": list(self.parent_event_ids),
            "workstream_id": self.workstream_id,
            "resource_scope": list(self.resource_scope),
            "git": self.git,
            "observed_at": self.observed_at,
            "recorded_at": self.recorded_at,
            "idempotency_key": self.idempotency_key,
            "payload_hash": self.payload_hash,
            "payload": self.payload,
            "provenance": [p.to_dict() for p in self.provenance],
            "sensitivity": self.sensitivity,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class LeaseToken:
    lease_id: str
    resource_key: str
    owner_agent_id: str
    session_id: str
    workstream_id: str
    generation: int
    acquired_at: str
    expires_at: str
    expected_state_version: int | None = None

    def __post_init__(self) -> None:
        require_uri(self.owner_agent_id, "motion://agent/", "owner_agent_id")
        require_uri(self.session_id, "motion://session/", "session_id")
        if self.generation < 1:
            raise ValueError("lease generation must be >= 1")
        if not self.resource_key:
            raise ValueError("resource_key is required")


def semantic_resource(namespace: str, *parts: str) -> str:
    clean = [p.strip("/") for p in parts if p]
    return ":".join([namespace.strip(":"), *clean])


def normalize_scopes(scopes: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({scope.strip() for scope in scopes if scope and scope.strip()}))
