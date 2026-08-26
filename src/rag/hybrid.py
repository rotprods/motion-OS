from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from collections import deque
from typing import Sequence

from src.knowledge.memory_store import load_memories


DEFAULT_WEIGHTS = {
    'semantic': 0.25,
    'style': 0.20,
    'motion': 0.15,
    'composition': 0.10,
    'brand': 0.10,
    'historical_qa': 0.10,
    'user_approval': 0.10,
}


@dataclass(frozen=True)
class RetrievalQuery:
    vector: tuple[float, ...] | None = None
    memory_planes: frozenset[str] | None = None
    renderer: str | None = None
    asset_type: str | None = None
    aspect_ratio: str | None = None
    require_license: bool = True
    graph_anchor_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalResult:
    memory_id: str
    memory_plane: str
    score: float
    vector_similarity: float
    graph_proximity: float
    component_scores: dict[str, float]
    explanation: tuple[str, ...]
    payload: dict


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sqrt(sum(x * x for x in a))
    nb = sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _graph_proximity(graph, candidate_node_id: str | None, anchors: tuple[str, ...], max_hops: int = 4) -> float:
    if graph is None or not candidate_node_id or not anchors:
        return 0.0
    ids = {node.id for node in graph.nodes}
    if candidate_node_id not in ids:
        return 0.0
    anchor_set = set(anchors) & ids
    if not anchor_set:
        return 0.0
    # deque() consumes an iterable. The traversal state is one tuple, not the
    # two independent values that would otherwise expand the node id string.
    queue = deque([(candidate_node_id, 0)])
    seen = {candidate_node_id}
    while queue:
        current, hops = queue.popleft()
        if current in anchor_set:
            return 1.0 / (1.0 + hops)
        if hops >= max_hops:
            continue
        for edge in graph.edges:
            neighbor = None
            if edge.source == current:
                neighbor = edge.target
            elif edge.target == current:
                neighbor = edge.source
            if neighbor and neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, hops + 1))
    return 0.0


def hybrid_retrieve(
    conn,
    query: RetrievalQuery,
    *,
    graph=None,
    limit: int = 10,
    weights: dict[str, float] | None = None,
) -> list[RetrievalResult]:
    weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
    if abs(sum(weights.values()) - 1.0) > 1e-6:
        raise ValueError('retrieval weights must sum to 1.0')
    memories = load_memories(conn, memory_planes=set(query.memory_planes) if query.memory_planes else None)
    results: list[RetrievalResult] = []
    for memory in memories:
        if query.require_license and not memory['license_ok']:
            continue
        if query.renderer and query.renderer not in memory['renderer_support']:
            continue
        if query.asset_type and memory['asset_type'] != query.asset_type:
            continue
        if query.aspect_ratio and memory['aspect_ratio'] not in {None, query.aspect_ratio}:
            continue

        vector_similarity = 0.0
        if query.vector is not None and memory['vector'] is not None:
            vector_similarity = max(0.0, min(1.0, _cosine(query.vector, memory['vector'])))
        graph_score = _graph_proximity(graph, memory['node_id'], query.graph_anchor_ids)

        components = {
            'semantic': float(memory['semantic_score']),
            'style': float(memory['style_score']),
            'motion': float(memory['motion_score']),
            'composition': float(memory['composition_score']),
            'brand': float(memory['brand_score']),
            'historical_qa': float(memory['historical_qa']),
            'user_approval': float(memory['user_approval']),
        }
        weighted = sum(components[name] * weights[name] for name in weights)
        # Semantic vector and graph neighborhood refine, rather than replace, controlled scores.
        score = 0.75 * weighted + 0.15 * vector_similarity + 0.10 * graph_score
        explanation = [
            f"hard_filters:license={'pass' if memory['license_ok'] else 'fail'}",
            f"weighted_controlled={weighted:.4f}",
            f"vector_similarity={vector_similarity:.4f}",
            f"graph_proximity={graph_score:.4f}",
        ]
        results.append(RetrievalResult(
            memory_id=memory['id'],
            memory_plane=memory['memory_plane'],
            score=round(score, 6),
            vector_similarity=round(vector_similarity, 6),
            graph_proximity=round(graph_score, 6),
            component_scores=components,
            explanation=tuple(explanation),
            payload=memory['payload'],
        ))
    return sorted(results, key=lambda result: (result.score, result.memory_id), reverse=True)[:limit]
