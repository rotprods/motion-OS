import pytest

from src.graph.model import Edge, MotionGraph, Node
from src.graph.ontology import GraphLevel, NodeKind, RelationKind, level_for_kind, relation_is_legal
from src.graph.editing_graph import EditingGraphValidationError, TypedEditingGraph


def test_node_kind_maps_to_exact_graph_level():
    assert level_for_kind(NodeKind.BRIEF) == GraphLevel.L1_SEMANTIC
    assert level_for_kind(NodeKind.LAYER) == GraphLevel.L2_EDITING
    assert level_for_kind(NodeKind.RENDERER) == GraphLevel.L3_RENDER_EVIDENCE


def test_relation_matrix_rejects_semantically_invalid_materialization():
    assert relation_is_legal(RelationKind.MATERIALIZES_AS, NodeKind.NARRATIVE_BEAT, NodeKind.SCENE)
    assert not relation_is_legal(RelationKind.MATERIALIZES_AS, NodeKind.SCENE, NodeKind.RENDERER)


def build_graph():
    graph = TypedEditingGraph("graph_01", "project_01")
    graph.add_node(graph.typed_node("brief", "Brief", authority="authoritative", provenance_refs=["user:brief"]))
    graph.add_node(graph.typed_node("beat", "NarrativeBeat", provenance_refs=["brief"]))
    graph.add_node(graph.typed_node("scene", "Scene", provenance_refs=["beat"]))
    graph.add_node(graph.typed_node("layer", "Layer", provenance_refs=["scene"]))
    graph.add_node(graph.typed_node("primitive", "Primitive", provenance_refs=["motion_system"]))
    graph.add_node(graph.typed_node("renderer", "Renderer", authority="measured", provenance_refs=["runtime:remotion"]))
    graph.add_edge(Edge("brief", "beat", "DRIVES", {"id": "e01"}))
    graph.add_edge(Edge("beat", "scene", "MATERIALIZES_AS", {"id": "e02"}))
    graph.add_edge(Edge("scene", "layer", "CONTAINS", {"id": "e03"}))
    graph.add_edge(Edge("layer", "primitive", "ANIMATED_BY", {"id": "e04"}))
    graph.add_edge(Edge("layer", "renderer", "RENDERED_BY", {"id": "e05"}))
    return graph


def test_typed_editing_graph_round_trip_is_deterministic():
    graph = build_graph()
    assert graph.validate_typed()["ok"] is True
    before = graph.content_hash()
    restored = TypedEditingGraph.from_contract_dict(graph.to_contract_dict())
    assert restored.validate_typed()["ok"] is True
    assert restored.content_hash() == before
    assert restored.canonical_json() == graph.canonical_json()


def test_typed_graph_rejects_wrong_node_level():
    graph = TypedEditingGraph("g", "p")
    with pytest.raises(EditingGraphValidationError):
        graph.add_node(Node("x", "Layer", {"level": "L1_SEMANTIC", "data": {}}))


def test_typed_graph_rejects_illegal_relation():
    graph = TypedEditingGraph("g", "p")
    graph.add_node(graph.typed_node("scene", "Scene"))
    graph.add_node(graph.typed_node("renderer", "Renderer"))
    with pytest.raises(EditingGraphValidationError):
        graph.add_edge(Edge("scene", "renderer", "MATERIALIZES_AS"))


def test_legacy_motion_graph_can_migrate_without_rewriting_legacy_model():
    legacy = MotionGraph()
    legacy.add_node(Node("a", "Brief"))
    legacy.add_node(Node("b", "Beat"))
    legacy.add_edge(Edge("a", "b", "PRECEDES"))
    migrated = TypedEditingGraph.from_legacy(legacy, graph_id="legacy_g", project_id="legacy_p")
    assert migrated.node("b").kind == "NarrativeBeat"
    assert migrated.validate_typed()["ok"] is True
