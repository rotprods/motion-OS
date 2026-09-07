import pytest

from src.compilers.remotion_graph import compile_editing_graph_to_remotion
from src.graph.editing_graph import TypedEditingGraph
from src.graph.model import Edge


def _graph_with_semantic_relations():
    graph = TypedEditingGraph("g:remotion-rel", "p:remotion-rel")
    for scene_id, start_ms, end_ms in (("scene:a", 0, 1000), ("scene:b", 1000, 2000)):
        graph.add_node(
            graph.typed_node(
                scene_id,
                "Scene",
                data={"start_ms": start_ms, "end_ms": end_ms},
                provenance_refs=["fixture"],
            )
        )
        layer_id = f"layer:{scene_id[-1]}"
        camera_id = f"camera:{scene_id[-1]}"
        graph.add_node(
            graph.typed_node(
                layer_id,
                "Layer",
                data={"layer_class": "SUBJECT", "renderer_support": ["remotion"]},
                provenance_refs=[scene_id],
            )
        )
        graph.add_node(
            graph.typed_node(
                camera_id,
                "CameraRig",
                data={"motion": "micro_drift", "framing": "medium"},
                provenance_refs=[scene_id],
            )
        )
        graph.add_edge(Edge(scene_id, layer_id, "CONTAINS", {"id": f"e:{scene_id}:layer"}))
        graph.add_edge(Edge(scene_id, camera_id, "USES", {"id": f"e:{scene_id}:camera"}))

    transition_id = "transition:a:b"
    graph.add_node(
        graph.typed_node(
            transition_id,
            "Transition",
            data={
                "type": "match_geometry_or_existing_element",
                "from_scene": "scene:a",
                "to_scene": "scene:b",
            },
            provenance_refs=["scene:a", "scene:b"],
        )
    )
    graph.add_edge(Edge("scene:a", transition_id, "EXITS_VIA", {"id": "e:exit"}))
    graph.add_edge(Edge("scene:b", transition_id, "ENTERS_VIA", {"id": "e:enter"}))
    return graph


def test_canonical_camera_and_transition_relationships_survive_compilation():
    spec = compile_editing_graph_to_remotion(_graph_with_semantic_relations(), fps=30)
    first, second = spec.scenes

    assert first["camera"]["id"] == "camera:a"
    assert second["camera"]["id"] == "camera:b"
    assert first["transitionIn"] is None
    assert first["transitionOut"]["id"] == "transition:a:b"
    assert second["transitionIn"]["id"] == "transition:a:b"
    assert second["transitionOut"] is None
    assert first["transitionOut"]["type"] == "match_geometry_or_existing_element"
    assert second["transitionIn"]["type"] == "match_geometry_or_existing_element"


def test_legacy_contained_camera_and_transition_remain_supported():
    graph = TypedEditingGraph("g:legacy", "p:legacy")
    graph.add_node(graph.typed_node("scene", "Scene", data={"start_ms": 0, "end_ms": 1000}))
    graph.add_node(graph.typed_node("camera", "CameraRig", data={"motion": "static"}))
    graph.add_node(
        graph.typed_node(
            "transition",
            "Transition",
            data={"direction": "out", "type": "legacy_wipe"},
        )
    )
    graph.add_edge(Edge("scene", "camera", "CONTAINS", {"id": "e:camera"}))
    graph.add_edge(Edge("scene", "transition", "CONTAINS", {"id": "e:transition"}))

    scene = compile_editing_graph_to_remotion(graph).scenes[0]
    assert scene["camera"]["id"] == "camera"
    assert scene["transitionOut"]["id"] == "transition"
    assert scene["transitionOut"]["type"] == "legacy_wipe"


def test_multiple_explicit_outgoing_transitions_fail_closed():
    graph = _graph_with_semantic_relations()
    graph.add_node(graph.typed_node("transition:other", "Transition", data={"type": "cut"}))
    graph.add_edge(Edge("scene:a", "transition:other", "EXITS_VIA", {"id": "e:other"}))
    with pytest.raises(ValueError, match="multiple Transition nodes via EXITS_VIA"):
        compile_editing_graph_to_remotion(graph)


def test_transition_relation_targeting_non_transition_fails_closed():
    graph = _graph_with_semantic_relations()
    graph.add_edge(Edge("scene:a", "layer:a", "ENTERS_VIA", {"id": "e:bad"}))
    with pytest.raises(ValueError, match="ENTERS_VIA must target Transition"):
        compile_editing_graph_to_remotion(graph)


def test_multiple_explicit_camera_rigs_fail_closed():
    graph = _graph_with_semantic_relations()
    graph.add_node(graph.typed_node("camera:extra", "CameraRig", data={"motion": "static"}))
    graph.add_edge(Edge("scene:a", "camera:extra", "USES", {"id": "e:extra-camera"}))
    with pytest.raises(ValueError, match="multiple CameraRig nodes via USES"):
        compile_editing_graph_to_remotion(graph)


def test_conflicting_legacy_and_explicit_camera_fails_closed():
    graph = _graph_with_semantic_relations()
    graph.add_node(graph.typed_node("camera:legacy", "CameraRig", data={"motion": "static"}))
    graph.add_edge(Edge("scene:a", "camera:legacy", "CONTAINS", {"id": "e:legacy-camera"}))
    with pytest.raises(ValueError, match="conflicting legacy/explicit camera"):
        compile_editing_graph_to_remotion(graph)
