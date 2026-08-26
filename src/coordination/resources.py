from __future__ import annotations

from dataclasses import dataclass
import posixpath
import re
from typing import Iterable


_ALLOWED_KINDS = {
    "file", "tree", "contract", "schema", "phase", "capability", "evidence",
    "resource", "plan", "issue", "pr", "artifact", "task",
}
_SEMANTIC_TOKEN = re.compile(r"^[A-Za-z0-9._/@+-]+$")


class InvalidResourceURI(ValueError):
    pass


@dataclass(frozen=True, slots=True, order=True)
class CanonicalResource:
    kind: str
    value: str

    @property
    def uri(self) -> str:
        return f"{self.kind}:{self.value}"

    @property
    def lock_key(self) -> str:
        """Exact transactional lock key.

        Hierarchical conflicts are resolved before lock acquisition. The database
        receives one canonical exact key per claimed scope, never a raw alias.
        """
        return self.uri


def _normalize_repo_path(value: str, *, tree: bool) -> str:
    raw = value.replace("\\", "/").strip()
    if tree:
        raw = raw.removesuffix("/**").removesuffix("/*")
    raw = raw.lstrip("/")
    normalized = posixpath.normpath(raw)
    if normalized in {"", "."}:
        raise InvalidResourceURI("empty repository path")
    if normalized == ".." or normalized.startswith("../"):
        raise InvalidResourceURI("repository path cannot escape root")
    if "//" in normalized:
        raise InvalidResourceURI("non-canonical path")
    return normalized.rstrip("/")


def canonicalize_resource(uri: str) -> CanonicalResource:
    if ":" not in uri:
        raise InvalidResourceURI("resource URI must contain kind:value")
    kind, value = uri.split(":", 1)
    kind = kind.strip().lower()
    value = value.strip()
    if kind not in _ALLOWED_KINDS:
        raise InvalidResourceURI(f"unsupported resource kind: {kind}")
    if not value:
        raise InvalidResourceURI("resource value is required")

    if kind == "file":
        value = _normalize_repo_path(value, tree=False)
    elif kind == "tree":
        value = _normalize_repo_path(value, tree=True)
    else:
        if not _SEMANTIC_TOKEN.fullmatch(value):
            raise InvalidResourceURI(f"non-canonical semantic resource value: {value}")

    return CanonicalResource(kind=kind, value=value)


def resource_overlap(left: CanonicalResource, right: CanonicalResource) -> bool:
    if left == right:
        return True

    if left.kind not in {"file", "tree"} or right.kind not in {"file", "tree"}:
        return False

    def contains(tree_value: str, other_value: str) -> bool:
        return other_value == tree_value or other_value.startswith(tree_value + "/")

    if left.kind == "tree" and contains(left.value, right.value):
        return True
    if right.kind == "tree" and contains(right.value, left.value):
        return True
    return False


def collision_pairs(scopes: Iterable[str]) -> tuple[tuple[str, str], ...]:
    canonical = [canonicalize_resource(scope) for scope in scopes]
    found: list[tuple[str, str]] = []
    for idx, left in enumerate(canonical):
        for right in canonical[idx + 1:]:
            if resource_overlap(left, right):
                pair = tuple(sorted((left.uri, right.uri)))
                if pair[0] != pair[1]:
                    found.append(pair)
    return tuple(sorted(set(found)))


def conflicts_with_any(requested: Iterable[str], active: Iterable[str]) -> tuple[tuple[str, str], ...]:
    req = [canonicalize_resource(x) for x in requested]
    act = [canonicalize_resource(x) for x in active]
    conflicts: list[tuple[str, str]] = []
    for left in req:
        for right in act:
            if resource_overlap(left, right):
                conflicts.append((left.uri, right.uri))
    return tuple(sorted(set(conflicts)))
