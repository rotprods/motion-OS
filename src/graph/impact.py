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


# Causal direction answers: "if dependency changes, what must be recomputed?"
# forward: edge.source affects edge.target
# reverse: edge.target affects edge.source
# both: synchronization or coupled relationship
INVALIDATION_DIRECTION: dict[str, str] = {
    'DRIVES': 'forward',
    'SHAPES': 'forward',
    'MATERIALIZES_AS': 'forward',
    'CONTAINS': 'forward',
    'CONDITIONS': 'forward',
    'COMPILES_TO': 'forward',
    'GENERATES': 'forward',
    'INVALIDATES': 'forward',

    'REQUIRES': 'reverse',
    'DEPENDS_ON': 'reverse',
    'USES': 'reverse',
    'ANIMATED_BY': 'reverse',
    'CONSTRAINED_BY': 'reverse',
    'ENTERS_VIA': 'reverse',
    'EXITS_VIA': 'reverse',
    'SOURCED_FROM': 'reverse',
    'SUPPORTED_BY': 'reverse',
    'DERIVED_FROM': 'reverse',
    'RENDERED_BY': 'reverse',
    'REQUIRES_SKILL': 'reverse',
    'PRODUCED_BY': 'reverse',
    'ROUTES_TO': 'reverse',
    'EVALUATES': 'reverse',

    'SYNC_WITH': 'both',
}

DEFAULT_INVALIDATION_RELATIONS = frozenset(INVALIDATION_DIRECTION)


@dataclass(frozen=True)
class InvalidationResult:
    roots: tuple[str, ...]
    invalidated: tuple[str, ...]
    preserved: tuple[str, ...]
    traversal_edges: tuple[tuple[str, str, str], ...]


def _causal_neighbors(graph, node_id: str, allowed: set[str]):
    for edge in graph.edges:
        if edge.kind not in allowed:
            continue
        direction = INVALIDATION_DIRECTION.get(edge.kind)
        if direction in {'forward', 'both'} and edge.source == node_id:
            yield edge.target, (edge.source, edge.kind, edge.target)
        if direction in {'reverse', 'both'} and edge.target == node_id:
            yield edge.source, (edge.source, edge.kind, edge.target)


def descendant_invalidation(
    graph,
    roots: Iterable[str],
    *,
    relation_kinds: Iterable[str] = DEFAULT_INVALIDATION_RELATIONS,
    stop_kinds: Iterable[str] = (),
) -> InvalidationResult:
    """Return causal dependents that must be recomputed after root mutation.

    Traversal direction is relation-aware. Example: `Layer USES TypographyRole`
    means a TypographyRole mutation invalidates Layer, not the reverse.
    """
    root_set = set(roots)
    for root in root_set:
        graph.node(root)
    allowed = set(relation_kinds)
    stop = set(stop_kinds)
    seen = set(root_set)
    queue = deque(sorted(root_set))
    traversed: list[tuple[str, str, str]] = []
    while queue:
        current = queue.popleft()
        for neighbor, evidence_edge in _causal_neighbors(graph, current, allowed):
            traversed.append(evidence_edge)
            if neighbor in seen:
                continue
            seen.add(neighbor)
            target = graph.node(neighbor)
            if target.kind not in stop:
                queue.append(neighbor)
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
