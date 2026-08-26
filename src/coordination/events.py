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


@dataclass(frozen=True, slots=True)
class CoordinationEvent:
    """Immutable event envelope shared by all coordination backends.

    `provenance_hash` is derived from the event's canonical content excluding the
    hash itself. Backends may reject duplicate event IDs or duplicate provenance
    hashes, but must never mutate an already accepted event.
    """

    event_type: str
    aggregate_type: str
    aggregate_id: str
    project_id: str
    agent_id: str
    session_id: str
    correlation_id: str
    payload: Mapping[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: int = 1
    run_id: str | None = None
    causation_id: str | None = None
    expected_revision: str | int | None = None
    occurred_at: str = field(default_factory=_utc_now_iso)
    recorded_at: str = field(default_factory=_utc_now_iso)
    git: Mapping[str, Any] | None = None
    evidence_refs: tuple[str, ...] = ()
    sensitivity: str = "INTERNAL"
    provenance_hash: str = ""

    def __post_init__(self) -> None:
        UUID(self.event_id)
        if self.schema_version < 1:
            raise ValueError("schema_version must be >= 1")
        if not self.project_id.startswith("motion://project/"):
            raise ValueError("project_id must be a canonical motion://project URI")
        if not self.agent_id.startswith("motion://agent/"):
            raise ValueError("agent_id must be a canonical motion://agent URI")
        if not self.session_id.startswith("motion://session/"):
            raise ValueError("session_id must be a canonical motion://session URI")
        if self.sensitivity not in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
            raise ValueError("invalid sensitivity")
        expected = canonical_event_hash(self)
        if self.provenance_hash:
            if self.provenance_hash != expected:
                raise ValueError("provenance_hash does not match canonical event content")
        else:
            object.__setattr__(self, "provenance_hash", expected)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_event_hash(event: CoordinationEvent) -> str:
    raw = asdict(event)
    raw["provenance_hash"] = ""
    return hashlib.sha256(_canonical_json(raw).encode("utf-8")).hexdigest()
