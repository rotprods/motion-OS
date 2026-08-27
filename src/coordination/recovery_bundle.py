from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class RecoverySource:
    uri: str
    revision: str
    sha256: str
    required: bool = True

    def __post_init__(self) -> None:
        if not self.uri or not self.revision:
            raise ValueError("recovery source uri/revision required")
        if len(self.sha256) != 64:
            raise ValueError("recovery source sha256 must be SHA-256 hex")


@dataclass(frozen=True, slots=True)
class RecoveryBundle:
    project_id: str
    main_sha: str
    event_watermark: int
    state_hash: str
    coordination_graph_hash: str
    unified_graph_hash: str
    cos_bundle_hash: str
    context_pack_sha256: str
    sources: tuple[RecoverySource, ...]
    bundle_sha256: str

    def canonical_payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["bundle_sha256"] = ""
        return data

    def verify(self) -> bool:
        expected = hashlib.sha256(_canonical_json(self.canonical_payload()).encode("utf-8")).hexdigest()
        return expected == self.bundle_sha256

    def validate_current_sources(self, current: Mapping[str, tuple[str, str]]) -> tuple[str, ...]:
        """Return deterministic drift/missing findings; empty tuple means recoverable."""
        findings: list[str] = []
        for source in self.sources:
            actual = current.get(source.uri)
            if actual is None:
                if source.required:
                    findings.append(f"MISSING:{source.uri}")
                continue
            revision, sha256 = actual
            if revision != source.revision:
                findings.append(f"REVISION_DRIFT:{source.uri}")
            if sha256 != source.sha256:
                findings.append(f"HASH_DRIFT:{source.uri}")
        return tuple(sorted(findings))


class RecoveryBundleCompiler:
    """Seal the minimum zero-chat recovery references without copying authority."""

    def compile(
        self,
        *,
        project_id: str,
        main_sha: str,
        event_watermark: int,
        state_hash: str,
        coordination_graph_hash: str,
        unified_graph_hash: str,
        cos_bundle_hash: str,
        context_pack_sha256: str,
        sources: Iterable[RecoverySource],
    ) -> RecoveryBundle:
        if not project_id.startswith("motion://project/"):
            raise ValueError("project_id must be canonical")
        if len(main_sha) < 7:
            raise ValueError("main_sha required")
        if event_watermark < 0:
            raise ValueError("event_watermark must be >= 0")
        hashes = {
            "state_hash": state_hash,
            "coordination_graph_hash": coordination_graph_hash,
            "unified_graph_hash": unified_graph_hash,
            "cos_bundle_hash": cos_bundle_hash,
            "context_pack_sha256": context_pack_sha256,
        }
        for name, value in hashes.items():
            if len(value) != 64:
                raise ValueError(f"{name} must be SHA-256 hex")
        normalized = tuple(sorted(tuple(sources), key=lambda item: item.uri))
        uris = [item.uri for item in normalized]
        if len(set(uris)) != len(uris):
            raise ValueError("recovery source URIs must be unique")
        if not normalized:
            raise ValueError("at least one recovery source is required")
        draft = RecoveryBundle(
            project_id=project_id,
            main_sha=main_sha,
            event_watermark=event_watermark,
            state_hash=state_hash,
            coordination_graph_hash=coordination_graph_hash,
            unified_graph_hash=unified_graph_hash,
            cos_bundle_hash=cos_bundle_hash,
            context_pack_sha256=context_pack_sha256,
            sources=normalized,
            bundle_sha256="",
        )
        digest = hashlib.sha256(_canonical_json(draft.canonical_payload()).encode("utf-8")).hexdigest()
        return RecoveryBundle(**{**asdict(draft), "sources": normalized, "bundle_sha256": digest})
