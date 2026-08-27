from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping

from .context import ContextSourceRef


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class PRLifecycle(str, Enum):
    OPEN = "OPEN"
    OPEN_DRAFT = "OPEN_DRAFT"
    MERGED = "MERGED"
    CLOSED_UNMERGED = "CLOSED_UNMERGED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True, order=True)
class PullRequestSnapshot:
    number: int
    head_branch: str
    head_sha: str
    base_branch: str
    state: PRLifecycle
    title: str = ""
    replacement_pr: int | None = None

    @classmethod
    def from_github(cls, raw: Mapping[str, Any], *, superseded_by: int | None = None) -> "PullRequestSnapshot":
        number = int(raw["number"])
        merged = bool(raw.get("merged", False) or raw.get("merged_at"))
        state_raw = str(raw.get("state", "open")).lower()
        draft = bool(raw.get("draft", False))
        if superseded_by is not None:
            state = PRLifecycle.SUPERSEDED
        elif merged:
            state = PRLifecycle.MERGED
        elif state_raw == "closed":
            state = PRLifecycle.CLOSED_UNMERGED
        elif draft:
            state = PRLifecycle.OPEN_DRAFT
        else:
            state = PRLifecycle.OPEN

        head_branch = str(raw.get("head") or raw.get("head_branch") or raw.get("branch") or "")
        head_sha = str(raw.get("head_sha") or raw.get("sha") or "")
        base_branch = str(raw.get("base") or raw.get("base_branch") or "main")
        if not head_branch or not head_sha:
            raise ValueError(f"PR #{number} requires head branch and SHA")
        return cls(
            number=number,
            head_branch=head_branch,
            head_sha=head_sha,
            base_branch=base_branch,
            state=state,
            title=str(raw.get("title") or ""),
            replacement_pr=superseded_by,
        )

    @property
    def is_active(self) -> bool:
        return self.state in {PRLifecycle.OPEN, PRLifecycle.OPEN_DRAFT}

    def to_context_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "branch": self.head_branch,
            "head_sha": self.head_sha,
            "base": self.base_branch,
            "state": self.state.value,
            "title": self.title,
            "replacement_pr": self.replacement_pr,
        }


@dataclass(frozen=True, slots=True)
class GitHubLifecycleSnapshot:
    repository: str
    main_sha: str
    prs: tuple[PullRequestSnapshot, ...]
    revision_hash: str

    @classmethod
    def build(
        cls,
        *,
        repository: str,
        main_sha: str,
        prs: Iterable[Mapping[str, Any]],
        supersessions: Mapping[int, int] | None = None,
    ) -> "GitHubLifecycleSnapshot":
        if "/" not in repository:
            raise ValueError("repository must be owner/name")
        if len(main_sha) < 7:
            raise ValueError("main_sha is required")
        supersessions = supersessions or {}
        snapshots = tuple(sorted(
            (
                PullRequestSnapshot.from_github(raw, superseded_by=supersessions.get(int(raw["number"])))
                for raw in prs
            ),
            key=lambda item: item.number,
        ))
        payload = {
            "repository": repository,
            "main_sha": main_sha,
            "prs": [asdict(item) for item in snapshots],
        }
        revision_hash = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
        return cls(repository=repository, main_sha=main_sha, prs=snapshots, revision_hash=revision_hash)

    def active_prs(self) -> tuple[dict[str, Any], ...]:
        return tuple(item.to_context_dict() for item in self.prs if item.is_active)

    def all_prs(self) -> tuple[dict[str, Any], ...]:
        return tuple(item.to_context_dict() for item in self.prs)

    def source_ref(self) -> ContextSourceRef:
        return ContextSourceRef(
            uri=f"github://{self.repository}/lifecycle",
            revision=self.revision_hash,
            sha256=self.revision_hash,
            sensitivity="INTERNAL",
        )
