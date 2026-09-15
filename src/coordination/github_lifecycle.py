from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Any, Iterable, Mapping

from .context import ContextSourceRef


_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA64_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _strict_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a literal boolean")
    return value


def _strict_sha40(value: object, field: str) -> str:
    if not isinstance(value, str) or _SHA40_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a 40-character lowercase Git SHA")
    return value


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

    def __post_init__(self) -> None:
        if isinstance(self.number, bool) or not isinstance(self.number, int) or self.number < 1:
            raise ValueError("PR number must be a positive integer")
        if not isinstance(self.head_branch, str) or not self.head_branch.strip():
            raise ValueError("PR head branch is required")
        _strict_sha40(self.head_sha, "PR head_sha")
        if not isinstance(self.base_branch, str) or not self.base_branch.strip():
            raise ValueError("PR base branch is required")
        if not isinstance(self.state, PRLifecycle):
            raise ValueError("PR state must be PRLifecycle")
        if self.replacement_pr is not None and (
            isinstance(self.replacement_pr, bool)
            or not isinstance(self.replacement_pr, int)
            or self.replacement_pr < 1
        ):
            raise ValueError("replacement_pr must be a positive integer")

    @classmethod
    def from_github(cls, raw: Mapping[str, Any], *, superseded_by: int | None = None) -> "PullRequestSnapshot":
        number_raw = raw["number"]
        if isinstance(number_raw, bool) or not isinstance(number_raw, int) or number_raw < 1:
            raise ValueError("GitHub PR number must be a positive integer")
        number = number_raw

        merged_flag = _strict_bool(raw.get("merged", False), "GitHub PR merged")
        merged_at = raw.get("merged_at")
        if merged_at is not None and (not isinstance(merged_at, str) or not merged_at.strip()):
            raise ValueError("GitHub PR merged_at must be null or non-empty text")
        merged = merged_flag or merged_at is not None

        state_value = raw.get("state", "open")
        if not isinstance(state_value, str) or state_value.lower() not in {"open", "closed"}:
            raise ValueError("GitHub PR state must be open or closed")
        state_raw = state_value.lower()
        draft = _strict_bool(raw.get("draft", False), "GitHub PR draft")

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

        head_branch = raw.get("head") or raw.get("head_branch") or raw.get("branch") or ""
        head_sha = raw.get("head_sha") or raw.get("sha") or ""
        base_branch = raw.get("base") or raw.get("base_branch") or "main"
        if not isinstance(head_branch, str) or not head_branch.strip():
            raise ValueError(f"PR #{number} requires head branch")
        _strict_sha40(head_sha, f"PR #{number} head_sha")
        if not isinstance(base_branch, str) or not base_branch.strip():
            raise ValueError(f"PR #{number} requires base branch")
        title = raw.get("title") or ""
        if not isinstance(title, str):
            raise ValueError(f"PR #{number} title must be text")
        return cls(
            number=number,
            head_branch=head_branch,
            head_sha=head_sha,
            base_branch=base_branch,
            state=state,
            title=title,
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

    def __post_init__(self) -> None:
        if not isinstance(self.repository, str) or self.repository.count("/") != 1:
            raise ValueError("repository must be owner/name")
        _strict_sha40(self.main_sha, "main_sha")
        if not isinstance(self.prs, tuple) or any(not isinstance(item, PullRequestSnapshot) for item in self.prs):
            raise ValueError("prs must be a tuple of PullRequestSnapshot values")
        numbers = [item.number for item in self.prs]
        if numbers != sorted(numbers) or len(numbers) != len(set(numbers)):
            raise ValueError("PR snapshots must be unique and sorted by number")
        if not isinstance(self.revision_hash, str) or _SHA64_RE.fullmatch(self.revision_hash) is None:
            raise ValueError("revision_hash must be lowercase sha256")
        if self.revision_hash != self.compute_revision_hash():
            raise ValueError("GitHub lifecycle revision_hash does not match snapshot payload")

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "main_sha": self.main_sha,
            "prs": [asdict(item) for item in self.prs],
        }

    def compute_revision_hash(self) -> str:
        return hashlib.sha256(_canonical_json(self.canonical_payload()).encode("utf-8")).hexdigest()

    def verify_hash(self) -> bool:
        return self.revision_hash == self.compute_revision_hash()

    @classmethod
    def build(
        cls,
        *,
        repository: str,
        main_sha: str,
        prs: Iterable[Mapping[str, Any]],
        supersessions: Mapping[int, int] | None = None,
    ) -> "GitHubLifecycleSnapshot":
        if not isinstance(repository, str) or repository.count("/") != 1:
            raise ValueError("repository must be owner/name")
        _strict_sha40(main_sha, "main_sha")
        supersessions = supersessions or {}
        snapshots = tuple(sorted(
            (
                PullRequestSnapshot.from_github(raw, superseded_by=supersessions.get(raw["number"]))
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
