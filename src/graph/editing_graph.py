from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from typing import Any
import json

from src.graph.model import MotionGraph, Node, Edge
from src.graph.ontology import (
    GraphLevel,
    NodeKind,
    RelationKind,
    canonical_kind,
    level_for_kind,
    relation_is_legal,
)


SCHEMA_VERSION = "1.0.0"


class EditingGraphValidationError(ValueError):
    pass


class TypedEditingGraph(MotionGraph):
    """Backward-compatible typed graph for the Studio Engine.

    Existing MotionGraph remains valid for legacy pipelines. New Studio Engine
    code should use TypedEditingGraph so node kinds, graph levels and relation
    legality are enforced before execution/rendering.
    """

    def __init__(self, graph_id: str, project_id: str, graph_revision: int = 1, nodes=None, edges=None):
        super().__init__(nodes=list(nodes or []), edges=list(edges or []))
        self.graph_id = graph_id
        self.project_id = project_id
        self.graph_revision = graph_revision

    @staticmethod
    def typed_node(
        node_id: str,
        kind: str | NodeKind,
        *,
        data: dict[str, Any] | None = None,
        authority: str = "inferred",
        provenance_refs: list[str] | None = None,
        continuity_id: str | None = None,
    ) -> Node:
        canonical = canonical_kind(kind)
        attrs = {
            "level": level_for_kind(canonical).value,
            "authority": authority,
            "provenance_refs": list(provenance_refs or []),
            "continuity_id": continuity_id,
            "data": dict(data or {}),
        }
        return Node(node_id, canonical.value, attrs)

    def add_node(self, node: Node):
        canonical = canonical_kind(node.kind)
        expected_level = level_for_kind(canonical).value
        level = node.attrs.get("level")
        if level is None:
            node.attrs["level"] = expected_level
        elif level != expected_level:
            raise EditingGraphValidationError(
                f"Node {node.id} kind={canonical.value} must be {expected_level}, got {level}"
            )
        node.kind = canonical.value
        node.attrs.setdefault("authority", "inferred")
        node.attrs.setdefault("provenance_refs", [])
        node.attrs.setdefault("continuity_id", None)
        node.attrs.setdefault("data", {})
        return super().add_node(node)

    def add_edge(self, edge: Edge):
        source = self.node(edge.source)
        target = self.node(edge.target)
        try:
            relation = RelationKind(edge.kind)
        except ValueError as exc:
            raise EditingGraphValidationError(f"Unknown relation: {edge.kind}") from exc
        if edge.source == edge.target:
            raise EditingGraphValidationError(f"Self-edge is not legal: {edge.source}")
        if not relation_is_legal(relation, source.kind, target.kind):
            raise EditingGraphValidationError(
                f"Illegal relation {relation.value}: {source.kind} -> {target.kind}"
            )
        edge.kind = relation.value
        edge.attrs.setdefault("required", True)
        edge.attrs.setdefault("data", {})
        return super().add_edge(edge)

    def validate_typed(self) -> dict[str, Any]:
        base = super().validate()
        errors: list[str] = []
        seen_edges: set[str] = set()
        for node in self.nodes:
            try:
                canonical = canonical_kind(node.kind)
                expected = level_for_kind(canonical).value
                if node.attrs.get("level") != expected:
                    errors.append(f"node-level:{node.id}:{node.attrs.get('level')}!={expected}")
            except ValueError as exc:
                errors.append(f"node-kind:{node.id}:{exc}")
        for index, edge in enumerate(self.edges):
            edge_id = str(edge.attrs.get("id", f"edge_{index}"))
            if edge_id in seen_edges:
                errors.append(f"duplicate-edge-id:{edge_id}")
            seen_edges.add(edge_id)
            try:
                source = self.node(edge.source)
                target = self.node(edge.target)
                if not relation_is_legal(edge.kind, source.kind, target.kind):
                    errors.append(f"illegal-edge:{edge.source}:{edge.kind}:{edge.target}")
            except (ValueError, KeyError) as exc:
                errors.append(f"edge:{index}:{exc}")
        return {**base, "typed_errors": errors, "ok": not base["broken_edges"] and base["dependency_cycle"] is None and not errors}

    def to_contract_dict(self) -> dict[str, Any]:
        nodes = []
        for node in sorted(self.nodes, key=lambda item: item.id):
            attrs = node.attrs
            nodes.append(
                {
                    "id": node.id,
                    "kind": node.kind,
                    "level": attrs.get("level", level_for_kind(node.kind).value),
                    "continuity_id": attrs.get("continuity_id"),
                    "authority": attrs.get("authority", "inferred"),
                    "provenance_refs": sorted(set(attrs.get("provenance_refs", []))),
                    "data": attrs.get("data", {}),
                }
            )
        edges = []
        for index, edge in enumerate(sorted(self.edges, key=lambda item: (item.source, item.kind, item.target))):
            attrs = edge.attrs
            edges.append(
                {
                    "id": str(attrs.get("id", f"edge_{index:04d}")),
                    "source": edge.source,
                    "target": edge.target,
                    "relation": edge.kind,
                    "required": bool(attrs.get("required", True)),
                    "data": attrs.get("data", {}),
                }
            )
        return {
            "schema_version": SCHEMA_VERSION,
            "graph_id": self.graph_id,
            "project_id": self.project_id,
            "graph_revision": self.graph_revision,
            "nodes": nodes,
            "edges": edges,
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_contract_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def content_hash(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_contract_dict(cls, data: dict[str, Any]) -> "TypedEditingGraph":
        if data.get("schema_version") != SCHEMA_VERSION:
            raise EditingGraphValidationError(f"Unsupported schema_version: {data.get('schema_version')}")
        graph = cls(
            graph_id=data["graph_id"],
            project_id=data["project_id"],
            graph_revision=int(data.get("graph_revision", 1)),
        )
        for raw in data.get("nodes", []):
            graph.add_node(
                graph.typed_node(
                    raw["id"],
                    raw["kind"],
                    data=raw.get("data", {}),
                    authority=raw.get("authority", "inferred"),
                    provenance_refs=raw.get("provenance_refs", []),
                    continuity_id=raw.get("continuity_id"),
                )
            )
        for raw in data.get("edges", []):
            graph.add_edge(
                Edge(
                    raw["source"],
                    raw["target"],
                    raw["relation"],
                    {
                        "id": raw["id"],
                        "required": raw.get("required", True),
                        "data": raw.get("data", {}),
                    },
                )
            )
        return graph

    @classmethod
    def from_legacy(
        cls,
        legacy: MotionGraph,
        *,
        graph_id: str,
        project_id: str,
        default_authority: str = "inferred",
    ) -> "TypedEditingGraph":
        graph = cls(graph_id=graph_id, project_id=project_id)
        for node in legacy.nodes:
            canonical = canonical_kind(node.kind)
            payload = dict(node.attrs)
            graph.add_node(
                graph.typed_node(
                    node.id,
                    canonical,
                    data=payload,
                    authority=default_authority,
                    provenance_refs=[f"legacy:{node.id}"],
                    continuity_id=node.id,
                )
            )
        for index, edge in enumerate(legacy.edges):
            relation = edge.kind
            if relation == "PRECEDES":
                relation = RelationKind.DEPENDS_ON.value
                source, target = edge.target, edge.source
            else:
                source, target = edge.source, edge.target
            graph.add_edge(Edge(source, target, relation, {"id": f"legacy_edge_{index:04d}", "data": dict(edge.attrs)}))
        return graph
