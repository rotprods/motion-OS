from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any, Mapping

from .context import ContextPack, ContextPackCompiler, ContextSourceRef


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _parse_dt(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class CoordinationSnapshot:
    raw: Mapping[str, Any]
    snapshot_sha256: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "CoordinationSnapshot":
        required = {"schema_version", "project_id", "captured_at", "main_sha", "active_prs", "active_agents", "contracts", "checkpoints", "source_refs"}
        missing = sorted(required - set(raw))
        if missing:
            raise ValueError(f"coordination snapshot missing required keys: {missing}")
        if int(raw["schema_version"]) < 1:
            raise ValueError("schema_version must be >= 1")
        project_id = str(raw["project_id"])
        if not project_id.startswith("motion://project/"):
            raise ValueError("project_id must be canonical")
        _parse_dt(str(raw["captured_at"]))
        digest = hashlib.sha256(_canonical_json(raw).encode("utf-8")).hexdigest()
        return cls(raw=dict(raw), snapshot_sha256=digest)

    def compile_context_pack(
        self,
        *,
        agent_id: str,
        session_id: str,
        allowed_write_scopes: list[str],
        forbidden_write_scopes: list[str] | None = None,
        goal_summary: str,
        ttl_seconds: int = 900,
        dependency_neighborhood: list[Mapping[str, Any]] | None = None,
    ) -> ContextPack:
        if ttl_seconds < 30:
            raise ValueError("ttl_seconds must be >= 30")
        captured_at = _parse_dt(str(self.raw["captured_at"]))
        generated_at = captured_at
        stale_after = generated_at + timedelta(seconds=ttl_seconds)

        projection = self.raw.get("projection") or {}
        projection_version = int(projection.get("version", 1))
        projection_hash = str(projection.get("hash") or hashlib.sha256(b"EMPTY_PROJECTION").hexdigest())

        source_refs = tuple(
            ContextSourceRef(
                uri=str(item["uri"]),
                revision=str(item["revision"]),
                sha256=str(item["sha256"]),
                sensitivity=str(item.get("sensitivity", "INTERNAL")),
            )
            for item in self.raw.get("source_refs", [])
        )

        expected_revisions: dict[str, str | int] = {
            str(item["uri"]): item["revision"] for item in self.raw.get("contracts", []) if "uri" in item and "revision" in item
        }
        expected_revisions["git:main"] = str(self.raw["main_sha"])
        expected_revisions["snapshot:coordination"] = self.snapshot_sha256

        compiler = ContextPackCompiler()
        return compiler.compile(
            context_pack_id=f"cp:{session_id}:{self.snapshot_sha256[:16]}",
            project_id=str(self.raw["project_id"]),
            agent_id=agent_id,
            session_id=session_id,
            generated_at=generated_at,
            stale_after=stale_after,
            main_sha=str(self.raw["main_sha"]),
            projection_version=projection_version,
            projection_hash=projection_hash,
            goal_summary=goal_summary,
            release_gates=tuple(self.raw.get("release_gates", [])),
            active_prs=tuple(self.raw.get("active_prs", [])),
            active_agents=tuple(self.raw.get("active_agents", [])),
            active_leases=tuple(self.raw.get("active_leases", [])),
            dependency_neighborhood=tuple(dependency_neighborhood or self.raw.get("tasks", [])),
            relevant_decisions=tuple(self.raw.get("decisions", [])),
            relevant_contracts=tuple(self.raw.get("contracts", [])),
            unresolved_conflicts=tuple(self.raw.get("conflicts", [])),
            checkpoint_refs=tuple(str(x.get("checkpoint_id", x)) if isinstance(x, Mapping) else str(x) for x in self.raw.get("checkpoints", [])),
            allowed_write_scopes=tuple(allowed_write_scopes),
            forbidden_write_scopes=tuple(forbidden_write_scopes or []),
            expected_revisions=expected_revisions,
            source_refs=source_refs,
        )
