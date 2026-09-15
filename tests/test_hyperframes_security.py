import pytest

from src.compilers.hyperframes import (
    HyperFramesSpec,
    compile_editing_graph_to_hyperframes,
    emit_hyperframes_project,
)
from src.graph.editing_graph import TypedEditingGraph
from src.graph.model import Edge


def test_hyperframes_project_keeps_graph_data_out_of_executable_script_and_remote_cdns():
    payload = "</script><script>globalThis.__PWNED__=true</script>"
    spec = HyperFramesSpec(
        width=640,
        height=360,
        fps=30,
        duration_ms=1000,
        scenes=(
            {
                "id": "scene",
                "startMs": 0,
                "endMs": 1000,
                "layers": [
                    {
                        "id": "layer",
                        "class": "TYPOGRAPHY",
                        "z": 1,
                        "attentionRole": "primary",
                        "data": {"text": payload},
                    }
                ],
            },
        ),
        timeline=(),
        provenance=(),
    )
    files = emit_hyperframes_project(spec)
    assert payload not in files["index.html"]
    assert payload not in files["motion.js"]
    assert payload in files["motion-spec.json"]
    assert "https://cdn.jsdelivr.net" not in files["index.html"]
    assert "import gsap from 'gsap'" in files["motion.js"]
    assert "./motion-spec.json" in files["motion.js"]


def _graph_with_channels(channels):
    graph = TypedEditingGraph("g:hf-security", "p:hf-security")
    graph.add_node(
        graph.typed_node(
            "scene",
            "Scene",
            data={"start_ms": 0, "end_ms": 1000},
            provenance_refs=["brief"],
        )
    )
    graph.add_node(
        graph.typed_node(
            "layer",
            "Layer",
            data={
                "layer_class": "TYPOGRAPHY",
                "z": 1,
                "attention_role": "primary",
                "text": "safe",
                "entry": {
                    "at_ms": 0,
                    "duration_ms": 250,
                    "ease": "power3.out",
                    "channels": channels,
                },
            },
            provenance_refs=["scene"],
        )
    )
    graph.add_edge(Edge("scene", "layer", "CONTAINS", {"id": "e"}))
    return graph


def test_hyperframes_rejects_dom_mutation_channels_from_graph_data():
    with pytest.raises(ValueError, match="unsupported HyperFrames animation channels"):
        compile_editing_graph_to_hyperframes(
            _graph_with_channels({"innerHTML": "<img src=x onerror=alert(1)>"}),
            width=640,
            height=360,
            fps=30,
        )


def test_hyperframes_accepts_bounded_transform_channels():
    spec = compile_editing_graph_to_hyperframes(
        _graph_with_channels({"x": 120, "scale": 1.05, "opacity": 0.8}),
        width=640,
        height=360,
        fps=30,
    )
    assert spec.timeline[0]["channels"] == {"x": 120, "scale": 1.05, "opacity": 0.8}


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), {"nested": 1}])
def test_hyperframes_rejects_unsafe_channel_value_types(value):
    with pytest.raises(ValueError, match="HyperFrames animation channel"):
        compile_editing_graph_to_hyperframes(
            _graph_with_channels({"x": value}),
            width=640,
            height=360,
            fps=30,
        )
