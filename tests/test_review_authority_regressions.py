import math

import pytest

from src.graph.editing_graph import TypedEditingGraph
from src.graph.model import Edge
from src.qa.graph_repair import RepairCandidateSpec, RepairMutation, choose_candidate
from src.renderers.multirender import assign_renderers, render_manifest
from src.studio.inspector import inspect_project, recovery_manifest


def _candidate(candidate_id: str) -> RepairCandidateSpec:
    return RepairCandidateSpec(
        candidate_id=candidate_id,
        defect_id="defect:1",
        strategy="minimal",
        mutations=(RepairMutation("layer", "set", "x", 1, "test"),),
        affected_nodes=("layer",),
        regression_protected=(),
    )


def test_repair_tournament_rejects_truthy_non_boolean_regression_verdicts():
    candidate = _candidate("repair:1")
    with pytest.raises(ValueError, match="literal boolean"):
        choose_candidate(
            [candidate],
            {candidate.candidate_id: 0.9},
            regression_pass={candidate.candidate_id: "false"},
        )


@pytest.mark.parametrize("score", [True, math.nan, math.inf, -math.inf, "0.9"])
def test_repair_tournament_rejects_non_numeric_or_non_finite_scores(score):
    candidate = _candidate("repair:1")
    with pytest.raises(ValueError, match="score"):
        choose_candidate(
            [candidate],
            {candidate.candidate_id: score},
            regression_pass={candidate.candidate_id: True},
        )


def test_repair_tournament_rejects_duplicate_candidate_identity():
    candidate = _candidate("repair:dup")
    with pytest.raises(ValueError, match="unique"):
        choose_candidate(
            [candidate, candidate],
            {candidate.candidate_id: 0.9},
            regression_pass={candidate.candidate_id: True},
        )


def _graph():
    graph = TypedEditingGraph("g:authority-review", "p:authority-review")
    graph.add_node(
        graph.typed_node(
            "project",
            "Project",
            data={"duration_ms": 1000},
            authority="authoritative",
            provenance_refs=["brief"],
        )
    )
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
                "renderer_support": ["remotion"],
                "text_integrity": "strict",
            },
            provenance_refs=["scene"],
        )
    )
    graph.add_edge(Edge("scene", "layer", "CONTAINS", {"id": "e_scene_layer"}))
    return graph


def _valid_recovery_inputs(graph):
    assignments = assign_renderers(graph)
    manifest = render_manifest(
        graph,
        assignments,
        fps=30,
        width=1080,
        height=1920,
        duration_ms=1000,
    )
    return {
        "git_sha": "a" * 40,
        "asset_manifest_hash": "b" * 64,
        "render_manifest": manifest,
        "qa_summary": {"decision": "PASS"},
        "artifact_refs": ["drive:file:1"],
    }


def test_recovery_ready_requires_qa_pass_not_merely_nonempty_summary():
    graph = _graph()
    inputs = _valid_recovery_inputs(graph)
    inputs["qa_summary"] = {"decision": "FAIL", "note": "non-empty but not passing"}
    manifest = recovery_manifest(graph, **inputs)
    assert manifest["zero_context_requirements"]["qa_summary_present"] is True
    assert manifest["zero_context_requirements"]["qa_summary_passed"] is False
    assert manifest["recovery_ready"] is False


def test_recovery_ready_recomputes_render_manifest_hash_instead_of_trusting_shape():
    graph = _graph()
    inputs = _valid_recovery_inputs(graph)
    inputs["render_manifest"] = dict(inputs["render_manifest"])
    inputs["render_manifest"]["fps"] = 60
    manifest = recovery_manifest(graph, **inputs)
    assert manifest["zero_context_requirements"]["render_manifest_hash_valid"] is False
    assert manifest["recovery_ready"] is False


def test_unknown_render_assignment_cannot_hide_unresolved_graph_state():
    graph = _graph()
    inputs = _valid_recovery_inputs(graph)
    tampered = dict(inputs["render_manifest"])
    tampered["assignments"] = list(tampered["assignments"]) + [
        {"node_id": "phantom", "renderer": "remotion", "reason": "spoof", "fallback": None}
    ]
    with pytest.raises(ValueError, match="unknown layer"):
        inspect_project(graph, render_manifest=tampered)
