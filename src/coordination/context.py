from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, Mapping


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class ContextSourceRef:
    uri: str
    revision: str
    sha256: str
    sensitivity: str = "INTERNAL"


@dataclass(frozen=True, slots=True)
class ContextPack:
    context_pack_id: str
    project_id: str
    agent_id: str
    session_id: str
    generated_at: str
    stale_after: str
    main_sha: str
    projection_version: int
    projection_hash: str
    goal_summary: str
    release_gates: tuple[str, ...]
    active_prs: tuple[Mapping[str, Any], ...]
    active_agents: tuple[Mapping[str, Any], ...]
    active_leases: tuple[Mapping[str, Any], ...]
    dependency_neighborhood: tuple[Mapping[str, Any], ...]
    relevant_decisions: tuple[Mapping[str, Any], ...]
    relevant_contracts: tuple[Mapping[str, Any], ...]
    unresolved_conflicts: tuple[Mapping[str, Any], ...]
    checkpoint_refs: tuple[str, ...]
    allowed_write_scopes: tuple[str, ...]
    forbidden_write_scopes: tuple[str, ...]
    expected_revisions: Mapping[str, str | int]
    source_refs: tuple[ContextSourceRef, ...]
    seal_sha256: str

    def canonical_payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["seal_sha256"] = ""
        return data

    def verify_seal(self) -> bool:
        expected = hashlib.sha256(_canonical_json(self.canonical_payload()).encode("utf-8")).hexdigest()
        return expected == self.seal_sha256

    def is_stale(self, *, now: datetime, main_sha: str, projection_version: int, projection_hash: str, current_source_revisions: Mapping[str, str]) -> bool:
        now_iso = _iso(now)
        if now_iso >= self.stale_after:
            return True
        if main_sha != self.main_sha:
            return True
        if projection_version != self.projection_version or projection_hash != self.projection_hash:
            return True
        for source in self.source_refs:
            if current_source_revisions.get(source.uri) != source.revision:
                return True
        return False


class ContextPackCompiler:
    """Deterministic compiler for bounded cross-session agent context."""

    def compile(
        self,
        *,
        context_pack_id: str,
        project_id: str,
        agent_id: str,
        session_id: str,
        generated_at: datetime,
        stale_after: datetime,
        main_sha: str,
        projection_version: int,
        projection_hash: str,
        goal_summary: str,
        release_gates: Iterable[str] = (),
        active_prs: Iterable[Mapping[str, Any]] = (),
        active_agents: Iterable[Mapping[str, Any]] = (),
        active_leases: Iterable[Mapping[str, Any]] = (),
        dependency_neighborhood: Iterable[Mapping[str, Any]] = (),
        relevant_decisions: Iterable[Mapping[str, Any]] = (),
        relevant_contracts: Iterable[Mapping[str, Any]] = (),
        unresolved_conflicts: Iterable[Mapping[str, Any]] = (),
        checkpoint_refs: Iterable[str] = (),
        allowed_write_scopes: Iterable[str] = (),
        forbidden_write_scopes: Iterable[str] = (),
        expected_revisions: Mapping[str, str | int] | None = None,
        source_refs: Iterable[ContextSourceRef] = (),
    ) -> ContextPack:
        if not project_id.startswith("motion://project/"):
            raise ValueError("project_id must be canonical")
        if not agent_id.startswith("motion://agent/"):
            raise ValueError("agent_id must be canonical")
        if not session_id.startswith("motion://session/"):
            raise ValueError("session_id must be canonical")
        if stale_after <= generated_at:
            raise ValueError("stale_after must be after generated_at")
        if projection_version < 1:
            raise ValueError("projection_version must be >= 1")
        if len(projection_hash) != 64:
            raise ValueError("projection_hash must be SHA-256 hex")

        draft = ContextPack(
            context_pack_id=context_pack_id,
            project_id=project_id,
            agent_id=agent_id,
            session_id=session_id,
            generated_at=_iso(generated_at),
            stale_after=_iso(stale_after),
            main_sha=main_sha,
            projection_version=projection_version,
            projection_hash=projection_hash,
            goal_summary=goal_summary,
            release_gates=tuple(sorted(set(release_gates))),
            active_prs=tuple(sorted((dict(x) for x in active_prs), key=lambda x: _canonical_json(x))),
            active_agents=tuple(sorted((dict(x) for x in active_agents), key=lambda x: _canonical_json(x))),
            active_leases=tuple(sorted((dict(x) for x in active_leases), key=lambda x: _canonical_json(x))),
            dependency_neighborhood=tuple(sorted((dict(x) for x in dependency_neighborhood), key=lambda x: _canonical_json(x))),
            relevant_decisions=tuple(sorted((dict(x) for x in relevant_decisions), key=lambda x: _canonical_json(x))),
            relevant_contracts=tuple(sorted((dict(x) for x in relevant_contracts), key=lambda x: _canonical_json(x))),
            unresolved_conflicts=tuple(sorted((dict(x) for x in unresolved_conflicts), key=lambda x: _canonical_json(x))),
            checkpoint_refs=tuple(sorted(set(checkpoint_refs))),
            allowed_write_scopes=tuple(sorted(set(allowed_write_scopes))),
            forbidden_write_scopes=tuple(sorted(set(forbidden_write_scopes))),
            expected_revisions=dict(sorted((expected_revisions or {}).items())),
            source_refs=tuple(sorted(source_refs, key=lambda x: x.uri)),
            seal_sha256="",
        )
        seal = hashlib.sha256(_canonical_json(draft.canonical_payload()).encode("utf-8")).hexdigest()
        return ContextPack(**{**asdict(draft), "source_refs": draft.source_refs, "seal_sha256": seal})
