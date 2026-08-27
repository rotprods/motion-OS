from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from .content_lineage import ContentLineageSnapshot
from .projection import ProjectionSnapshot


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _parse_properties(value: str, *, node_id: str, node_type: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid properties_json for {node_id} [{node_type}]") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"properties_json must be an object for {node_id} [{node_type}]")
    return parsed


def _merge_value(left: Any, right: Any, *, path: str) -> Any:
    """Deterministically merge compatible claims and reject contradictory ones.

    Dicts are recursively enriched. Scalars/lists may be repeated only when equal.
    This keeps a canonical node identity while preventing one projection from silently
    overwriting a claim made by another authority plane.
    """
    if left == right:
        return left
    if isinstance(left, dict) and isinstance(right, dict):
        merged: dict[str, Any] = {}
        for key in sorted(set(left) | set(right)):
            if key not in left:
                merged[key] = right[key]
            elif key not in right:
                merged[key] = left[key]
            else:
                merged[key] = _merge_value(left[key], right[key], path=f"{path}.{key}")
        return merged
    raise ValueError(f"contradictory node property at {path}: {left!r} != {right!r}")


def _merge_node(existing: "UnifiedNode", candidate: "UnifiedNode") -> "UnifiedNode":
    if existing.node_id != candidate.node_id or existing.node_type != candidate.node_type:
        raise ValueError("cannot merge nodes with different identities")
    left = _parse_properties(existing.properties_json, node_id=existing.node_id, node_type=existing.node_type)
    right = _parse_properties(candidate.properties_json, node_id=candidate.node_id, node_type=candidate.node_type)
    merged = _merge_value(left, right, path=f"{existing.node_id}[{existing.node_type}]")
    return UnifiedNode(existing.node_id, existing.node_type, _canonical_json(merged))


@dataclass(frozen=True, slots=True, order=True)
class UnifiedNode:
    node_id: str
    node_type: str
    properties_json: str


@dataclass(frozen=True, slots=True, order=True)
class UnifiedEdge:
    source: str
    relation: str
    target: str
    properties_json: str


@dataclass(frozen=True, slots=True)
class UnifiedMotionGraphSnapshot:
    graph_version: int
    coordination_projection_hash: str
    content_lineage_hashes: tuple[str, ...]
    nodes: tuple[UnifiedNode, ...]
    edges: tuple[UnifiedEdge, ...]
    graph_hash: str

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "graph_version": self.graph_version,
            "coordination_projection_hash": self.coordination_projection_hash,
            "content_lineage_hashes": list(self.content_lineage_hashes),
            "nodes": [asdict(node) for node in self.nodes],
            "edges": [asdict(edge) for edge in self.edges],
        }

    def verify_hash(self) -> bool:
        return hashlib.sha256(_canonical_json(self.canonical_payload()).encode("utf-8")).hexdigest() == self.graph_hash


class UnifiedMotionGraphCompiler:
    """Union coordination and product-domain projections without merging authority.

    The result is a rebuildable query snapshot. Source hashes are retained so a
    consumer can prove which coordination and content projections produced it.
    Canonical node identities are enriched only by compatible properties; conflicting
    claims fail closed instead of being overwritten.
    """

    def compile(
        self,
        *,
        coordination: ProjectionSnapshot,
        content_lineages: tuple[ContentLineageSnapshot, ...] = (),
        graph_version: int = 1,
    ) -> UnifiedMotionGraphSnapshot:
        if graph_version < 1:
            raise ValueError("graph_version must be >= 1")
        if not coordination.verify_hash():
            raise ValueError("coordination projection hash invalid")
        if any(not lineage.verify_hash() for lineage in content_lineages):
            raise ValueError("content lineage hash invalid")

        nodes: dict[tuple[str, str], UnifiedNode] = {}
        edges: dict[tuple[str, str, str, str], UnifiedEdge] = {}

        for node in coordination.nodes:
            candidate = UnifiedNode(node.node_id, node.node_type, node.properties_json)
            key = (candidate.node_id, candidate.node_type)
            existing = nodes.get(key)
            nodes[key] = candidate if existing is None else _merge_node(existing, candidate)
        for edge in coordination.edges:
            edges[(edge.source, edge.relation, edge.target, edge.properties_json)] = UnifiedEdge(
                edge.source, edge.relation, edge.target, edge.properties_json
            )

        for lineage in sorted(content_lineages, key=lambda item: item.snapshot_hash):
            for node in lineage.nodes:
                key = (node.node_id, node.node_type)
                candidate = UnifiedNode(node.node_id, node.node_type, node.properties_json)
                existing = nodes.get(key)
                nodes[key] = candidate if existing is None else _merge_node(existing, candidate)
            for edge in lineage.edges:
                candidate = UnifiedEdge(edge.source, edge.relation, edge.target, edge.properties_json)
                edges[(edge.source, edge.relation, edge.target, edge.properties_json)] = candidate

        sorted_nodes = tuple(sorted(nodes.values()))
        sorted_edges = tuple(sorted(edges.values()))
        lineage_hashes = tuple(sorted(lineage.snapshot_hash for lineage in content_lineages))
        payload = {
            "graph_version": graph_version,
            "coordination_projection_hash": coordination.projection_hash,
            "content_lineage_hashes": list(lineage_hashes),
            "nodes": [asdict(node) for node in sorted_nodes],
            "edges": [asdict(edge) for edge in sorted_edges],
        }
        digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
        return UnifiedMotionGraphSnapshot(
            graph_version=graph_version,
            coordination_projection_hash=coordination.projection_hash,
            content_lineage_hashes=lineage_hashes,
            nodes=sorted_nodes,
            edges=sorted_edges,
            graph_hash=digest,
        )
