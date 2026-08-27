from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any, Iterable, Mapping

from .context import ContextPack, ContextPackCompiler, ContextSourceRef
from .github_lifecycle import GitHubLifecycleSnapshot
from .snapshot import CoordinationSnapshot


class LiveContextCompiler:
    """Reconcile durable/bootstrap coordination state with fresh provider truth.

    Bootstrap snapshots remain recovery inputs, not lifecycle authority. Fresh
    GitHub lifecycle state overrides stale PR/main fields before a ContextPack is
    sealed. Additional source refs (Drive/event watermark/etc.) are preserved.
    """

    def compile(
        self,
        *,
        bootstrap: CoordinationSnapshot,
        github: GitHubLifecycleSnapshot,
        agent_id: str,
        session_id: str,
        goal_summary: str,
        generated_at: datetime,
        ttl_seconds: int = 900,
        allowed_write_scopes: Iterable[str] = (),
        forbidden_write_scopes: Iterable[str] = (),
        active_agents: Iterable[Mapping[str, Any]] | None = None,
        active_leases: Iterable[Mapping[str, Any]] | None = None,
        dependency_neighborhood: Iterable[Mapping[str, Any]] | None = None,
        unresolved_conflicts: Iterable[Mapping[str, Any]] | None = None,
        event_watermark: int | None = None,
        extra_source_refs: Iterable[ContextSourceRef] = (),
    ) -> ContextPack:
        if ttl_seconds < 30:
            raise ValueError("ttl_seconds must be >= 30")
        if github.repository != "rotprods/motion-OS":
            raise ValueError("lifecycle snapshot repository mismatch")

        raw = bootstrap.raw
        projection = raw.get("projection") or {}
        projection_version = int(projection.get("version", 1))
        projection_hash = str(projection.get("hash") or "0" * 64)
        if len(projection_hash) != 64:
            raise ValueError("projection hash must be SHA-256 hex")

        refs = [
            ContextSourceRef(
                uri=str(item["uri"]),
                revision=str(item["revision"]),
                sha256=str(item["sha256"]),
                sensitivity=str(item.get("sensitivity", "INTERNAL")),
            )
            for item in raw.get("source_refs", [])
        ]
        refs = [ref for ref in refs if not ref.uri.startswith("github://rotprods/motion-OS/lifecycle")]
        refs.append(github.source_ref())
        refs.extend(extra_source_refs)

        expected_revisions: dict[str, str | int] = {
            str(item["uri"]): item["revision"]
            for item in raw.get("contracts", [])
            if "uri" in item and "revision" in item
        }
        expected_revisions["git:main"] = github.main_sha
        expected_revisions["github:lifecycle"] = github.revision_hash
        expected_revisions["snapshot:coordination"] = bootstrap.snapshot_sha256
        if event_watermark is not None:
            if event_watermark < 0:
                raise ValueError("event_watermark must be >= 0")
            expected_revisions["event:watermark"] = event_watermark

        compiler = ContextPackCompiler()
        pack = compiler.compile(
            context_pack_id=f"cp:{session_id}:{github.revision_hash[:16]}",
            project_id=str(raw["project_id"]),
            agent_id=agent_id,
            session_id=session_id,
            generated_at=generated_at,
            stale_after=generated_at + timedelta(seconds=ttl_seconds),
            main_sha=github.main_sha,
            projection_version=projection_version,
            projection_hash=projection_hash,
            goal_summary=goal_summary,
            release_gates=tuple(raw.get("release_gates", [])),
            active_prs=github.active_prs(),
            active_agents=tuple(active_agents if active_agents is not None else raw.get("active_agents", [])),
            active_leases=tuple(active_leases if active_leases is not None else raw.get("active_leases", [])),
            dependency_neighborhood=tuple(
                dependency_neighborhood if dependency_neighborhood is not None else raw.get("tasks", [])
            ),
            relevant_decisions=tuple(raw.get("decisions", [])),
            relevant_contracts=tuple(raw.get("contracts", [])),
            unresolved_conflicts=tuple(
                unresolved_conflicts if unresolved_conflicts is not None else raw.get("conflicts", [])
            ),
            checkpoint_refs=tuple(
                str(item.get("checkpoint_id", item)) if isinstance(item, Mapping) else str(item)
                for item in raw.get("checkpoints", [])
            ),
            allowed_write_scopes=tuple(allowed_write_scopes),
            forbidden_write_scopes=tuple(forbidden_write_scopes),
            expected_revisions=expected_revisions,
            source_refs=refs,
        )
        return pack
