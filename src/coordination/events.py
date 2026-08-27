from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping
from uuid import UUID, uuid4


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ProvenanceRef:
    source_type: str
    source_id: str
    revision: str | None = None
    sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.source_type or not self.source_id:
            raise ValueError("provenance source_type/source_id are required")
        if self.sha256 is not None:
            if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256):
                raise ValueError("provenance sha256 must be lowercase hex")


@dataclass(frozen=True, slots=True)
class CoordinationEvent:
    """Canonical immutable coordination event v1.

    Aggregate revision/idempotency are state-store guarantees. Event transport is
    deliberately separate. `provenance_hash` seals the complete event envelope;
    `logical_command_hash` excludes generated IDs/timestamps and is used to detect
    unsafe idempotency-key reuse.
    """

    event_type: str
    aggregate_type: str
    aggregate_id: str
    aggregate_revision: int
    project_id: str
    agent_id: str
    session_id: str
    correlation_id: str
    idempotency_key: str
    payload: Mapping[str, Any]
    provenance: tuple[ProvenanceRef, ...]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: str = "1.0.0"
    workstream_id: str | None = None
    run_id: str | None = None
    causation_id: str | None = None
    parent_event_ids: tuple[str, ...] = ()
    resource_scope: tuple[str, ...] = ()
    expected_revision: int | None = None
    occurred_at: str = field(default_factory=_utc_now_iso)
    recorded_at: str = field(default_factory=_utc_now_iso)
    git: Mapping[str, Any] | None = None
    evidence_refs: tuple[str, ...] = ()
    sensitivity: str = "INTERNAL"
    provenance_hash: str = ""

    def __post_init__(self) -> None:
        UUID(self.event_id)
        if self.schema_version != "1.0.0":
            raise ValueError("unsupported CoordinationEvent schema_version")
        if not self.event_type or self.event_type.upper() != self.event_type:
            raise ValueError("event_type must be upper-case")
        if self.aggregate_revision < 1:
            raise ValueError("aggregate_revision must be >= 1")
        if self.expected_revision is not None and self.expected_revision < 0:
            raise ValueError("expected_revision must be >= 0")
        if not self.idempotency_key:
            raise ValueError("idempotency_key is required")
        if not self.project_id.startswith("motion://project/"):
            raise ValueError("project_id must be a canonical motion://project URI")
        if not self.agent_id.startswith("motion://agent/"):
            raise ValueError("agent_id must be a canonical motion://agent URI")
        if not self.session_id.startswith("motion://session/"):
            raise ValueError("session_id must be a canonical motion://session URI")
        if self.workstream_id is not None and not self.workstream_id.startswith("motion://workstream/"):
            raise ValueError("workstream_id must be a canonical motion://workstream URI")
        if self.sensitivity not in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
            raise ValueError("invalid sensitivity")
        if not self.provenance:
            raise ValueError("at least one provenance reference is required")
        if len(set(self.parent_event_ids)) != len(self.parent_event_ids):
            raise ValueError("parent_event_ids must be unique")
        if len(set(self.resource_scope)) != len(self.resource_scope):
            raise ValueError("resource_scope entries must be unique")
        expected = canonical_event_hash(self)
        if self.provenance_hash:
            if self.provenance_hash != expected:
                raise ValueError("provenance_hash does not match canonical event content")
        else:
            object.__setattr__(self, "provenance_hash", expected)

    @property
    def payload_hash(self) -> str:
        return _sha256(dict(self.payload))

    @property
    def logical_command_hash(self) -> str:
        return _sha256(
            {
                "schema_version": self.schema_version,
                "event_type": self.event_type,
                "aggregate_type": self.aggregate_type,
                "aggregate_id": self.aggregate_id,
                "project_id": self.project_id,
                "agent_id": self.agent_id,
                "session_id": self.session_id,
                "workstream_id": self.workstream_id,
                "correlation_id": self.correlation_id,
                "causation_id": self.causation_id,
                "parent_event_ids": list(self.parent_event_ids),
                "resource_scope": list(self.resource_scope),
                "expected_revision": self.expected_revision,
                "payload_hash": self.payload_hash,
                "sensitivity": self.sensitivity,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        raw["payload_hash"] = self.payload_hash
        return raw


def canonical_event_hash(event: CoordinationEvent) -> str:
    raw = asdict(event)
    raw["provenance_hash"] = ""
    return _sha256(raw)
