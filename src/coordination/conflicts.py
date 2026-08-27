from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping

from .resources import canonicalize_resource, resource_overlap


class ConflictClass(str, Enum):
    NONE = "NONE"
    PATH_OVERLAP = "PATH_OVERLAP"
    SEMANTIC_OVERLAP = "SEMANTIC_OVERLAP"
    DEPENDENCY_RISK = "DEPENDENCY_RISK"
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"


@dataclass(frozen=True, slots=True)
class ConflictFinding:
    classification: ConflictClass
    requested: tuple[str, ...]
    active: tuple[str, ...]
    details: tuple[str, ...] = ()

    @property
    def blocked(self) -> bool:
        return self.classification in {
            ConflictClass.SEMANTIC_OVERLAP,
            ConflictClass.AUTHORITY_CONFLICT,
        }


def _is_path(kind: str) -> bool:
    return kind in {"file", "tree"}


def classify_conflict(
    *,
    requested_scopes: Iterable[str],
    active_scopes: Iterable[str],
    dependency_edges: Mapping[str, Iterable[str]] | None = None,
    requested_authority: Iterable[str] = (),
    active_authority: Iterable[str] = (),
) -> ConflictFinding:
    requested = tuple(canonicalize_resource(x) for x in requested_scopes)
    active = tuple(canonicalize_resource(x) for x in active_scopes)
    details: list[str] = []

    requested_authority_set = {canonicalize_resource(x).uri for x in requested_authority}
    active_authority_set = {canonicalize_resource(x).uri for x in active_authority}
    authority_overlap = requested_authority_set & active_authority_set
    if authority_overlap:
        return ConflictFinding(
            ConflictClass.AUTHORITY_CONFLICT,
            tuple(x.uri for x in requested),
            tuple(x.uri for x in active),
            tuple(sorted(authority_overlap)),
        )

    path_overlap = False
    semantic_overlap = False
    for left in requested:
        for right in active:
            if not resource_overlap(left, right):
                continue
            details.append(f"{left.uri}<->{right.uri}")
            if _is_path(left.kind) or _is_path(right.kind):
                path_overlap = True
            else:
                semantic_overlap = True

    # Exact semantic resources overlap through equality in resource_overlap().
    if semantic_overlap:
        return ConflictFinding(
            ConflictClass.SEMANTIC_OVERLAP,
            tuple(x.uri for x in requested),
            tuple(x.uri for x in active),
            tuple(sorted(set(details))),
        )
    if path_overlap:
        return ConflictFinding(
            ConflictClass.PATH_OVERLAP,
            tuple(x.uri for x in requested),
            tuple(x.uri for x in active),
            tuple(sorted(set(details))),
        )

    dependency_edges = dependency_edges or {}
    active_uris = {x.uri for x in active}
    dependency_hits: set[str] = set()
    for resource in requested:
        for dependency in dependency_edges.get(resource.uri, ()): 
            canonical_dep = canonicalize_resource(dependency).uri
            if canonical_dep in active_uris:
                dependency_hits.add(f"{resource.uri}->{canonical_dep}")
    if dependency_hits:
        return ConflictFinding(
            ConflictClass.DEPENDENCY_RISK,
            tuple(x.uri for x in requested),
            tuple(x.uri for x in active),
            tuple(sorted(dependency_hits)),
        )

    return ConflictFinding(
        ConflictClass.NONE,
        tuple(x.uri for x in requested),
        tuple(x.uri for x in active),
        (),
    )
