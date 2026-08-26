from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Iterable


@dataclass
class ImpactRegion:
    roots: list
    nodes: list
    beats: list
    start: float | None
    end: float | None


# Legacy API retained for existing partial-render loops.
def affected_subgraph(g, roots, max_hops=2, padding=.25):
    kinds = {'USES', 'REQUIRES', 'DERIVED_FROM', 'PRECEDES', 'FAILS', 'PATCHED_BY'}
    seen = set(roots)
    frontier = [(r, 0) for r in roots]
    while frontier:
        u, h = frontier.pop(0)
        if h >= max_hops:
            continue
        for e in g.edges:
            if e.kind not in kinds:
                continue
            v = e.target if e.source == u else (e.source if e.target == u and e.kind in {'USES', 'REQUIRES', 'DERIVED_FROM'} else None)
            if v and v not in seen:
                seen.add(v)
                frontier.append((v, h + 1))
    beats, starts, ends = [], [], []
    for i in seen:
        n = g.node(i)
        if n.kind in {'Beat', 'NarrativeBeat'}:
            beats.append(i)
            timing = n.attrs.get('data', n.attrs)
            if 'start' in timing and 'end' in timing:
                starts.append(timing['start'])
                ends.append(timing['end'])
            elif 'start_ms' in timing and 'end_ms' in timing:
                starts.append(timing['start_ms'] / 1000)
                ends.append(timing['end_ms'] / 1000)
    return ImpactRegion(
        list(roots),
        sorted(seen),
        sorted(beats),
        max(0, min(starts) - padding) if starts else None,
        max(ends) + padding if ends else None,
    )


DEFAULT_INVALIDATION_RELATIONS = frozenset({
    'REQUIRES',
    'DEPENDS_ON',
    'DRIVES',
    'SHAPES',
    'MATERIALIZES_AS',
    'CONTAINS',
    'USES',
    'ANIMATED_BY',
    'CONSTRAINED_BY',
    'ENTERS_VIA',
    'EXITS_VIA',
    'SOURCED_FROM',
    'DERIVED_FROM',
    'CONDITIONS',
    'COMPILES_TO',
    'RENDERED_BY',
    'REQUIRES_SKILL',
    'SYNC_WITH',
    'GENERATES',
    'PRODUCED_BY',
    'ROUTES_TO',
    'EVALUATES',
})


@dataclass(frozen=True)
class InvalidationResult:
    roots: tuple[str, ...]
    invalidated: tuple[str, ...]
    preserved: tuple[str, ...]
    traversal_edges: tuple[tuple[str, str, str], ...]


def descendant_invalidation(
    graph,
    roots: Iterable[str],
    *,
    relation_kinds: Iterable[str] = DEFAULT_INVALIDATION_RELATIONS,
    stop_kinds: Iterable[str] = (),
) -> InvalidationResult:
    """Return causal descendants that must be recomputed after root mutation.

    Direction is source → target. This is intentionally different from the
    legacy bidirectional repair-neighborhood function above.
    """
    root_set = set(roots)
    for root in root_set:
        graph.node(root)  # explicit missing-root failure
    allowed = set(relation_kinds)
    stop = set(stop_kinds)
    seen = set(root_set)
    queue = deque(sorted(root_set))
    traversed: list[tuple[str, str, str]] = []
    while queue:
        source = queue.popleft()
        for edge in graph.edges:
            if edge.source != source or edge.kind not in allowed:
                continue
            traversed.append((edge.source, edge.kind, edge.target))
            if edge.target in seen:
                continue
            seen.add(edge.target)
            target = graph.node(edge.target)
            if target.kind not in stop:
                queue.append(edge.target)
    all_ids = {node.id for node in graph.nodes}
    return InvalidationResult(
        roots=tuple(sorted(root_set)),
        invalidated=tuple(sorted(seen)),
        preserved=tuple(sorted(all_ids - seen)),
        traversal_edges=tuple(sorted(set(traversed))),
    )


def assert_preserved(result: InvalidationResult, *node_ids: str) -> None:
    missing = sorted(set(node_ids) - set(result.preserved))
    if missing:
        raise AssertionError(f'Expected nodes to remain preserved, but invalidated: {missing}')


def assert_invalidated(result: InvalidationResult, *node_ids: str) -> None:
    missing = sorted(set(node_ids) - set(result.invalidated))
    if missing:
        raise AssertionError(f'Expected nodes to be invalidated: {missing}')
