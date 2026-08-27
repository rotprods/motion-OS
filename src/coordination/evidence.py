from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping

from .context import ContextSourceRef


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class EvidenceArtifact:
    artifact_id: str
    provider: str
    provider_file_id: str
    revision: str
    sha256: str
    mime_type: str | None = None
    title: str | None = None
    sensitivity: str = "INTERNAL"
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.artifact_id.startswith("motion://artifact/"):
            raise ValueError("artifact_id must be canonical")
        if not self.provider or not self.provider_file_id or not self.revision:
            raise ValueError("provider, provider_file_id and revision are required")
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256):
            raise ValueError("sha256 must be lowercase hex")
        if self.sensitivity not in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
            raise ValueError("invalid sensitivity")

    @property
    def source_uri(self) -> str:
        return f"{self.provider}://{self.provider_file_id}"

    def context_source_ref(self) -> ContextSourceRef:
        return ContextSourceRef(
            uri=self.source_uri,
            revision=self.revision,
            sha256=self.sha256,
            sensitivity=self.sensitivity,
        )


@dataclass(frozen=True, slots=True)
class EvidenceManifest:
    manifest_version: int
    artifacts: tuple[EvidenceArtifact, ...]
    manifest_hash: str

    @classmethod
    def build(cls, artifacts: Iterable[EvidenceArtifact], *, manifest_version: int = 1) -> "EvidenceManifest":
        if manifest_version < 1:
            raise ValueError("manifest_version must be >= 1")
        ordered = tuple(sorted(artifacts, key=lambda item: item.artifact_id))
        ids = [item.artifact_id for item in ordered]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate artifact_id")
        payload = {
            "manifest_version": manifest_version,
            "artifacts": [asdict(item) for item in ordered],
        }
        digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
        return cls(manifest_version=manifest_version, artifacts=ordered, manifest_hash=digest)

    def verify_hash(self) -> bool:
        payload = {
            "manifest_version": self.manifest_version,
            "artifacts": [asdict(item) for item in self.artifacts],
        }
        return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest() == self.manifest_hash

    def source_refs(self) -> tuple[ContextSourceRef, ...]:
        return tuple(item.context_source_ref() for item in self.artifacts)

    def changed_since(self, previous: "EvidenceManifest") -> tuple[str, ...]:
        old = {item.artifact_id: (item.revision, item.sha256) for item in previous.artifacts}
        new = {item.artifact_id: (item.revision, item.sha256) for item in self.artifacts}
        return tuple(sorted(key for key in set(old) | set(new) if old.get(key) != new.get(key)))
