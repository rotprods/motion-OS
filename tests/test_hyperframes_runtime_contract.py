from __future__ import annotations

from copy import deepcopy

from scripts.build_hyperframes_runtime_fixture import fixture_graph
from scripts.verify_hyperframes_render import evaluate_probe
from src.compilers.hyperframes import (
    build_hyperframes_render_contract,
    compile_editing_graph_to_hyperframes,
    emit_hyperframes_project,
)


def test_emitter_matches_standalone_hyperframes_runtime_contract():
    spec = compile_editing_graph_to_hyperframes(fixture_graph(), width=640, height=360, fps=30)
    files = emit_hyperframes_project(spec)
    html = files["index.html"]
    js = files["motion.js"]

    assert 'data-composition-id="motion-os-master"' in html
    assert 'data-start="0"' in html
    assert 'data-duration="3.000000"' in html
    assert 'data-track-index="0"' in html
    assert 'data-width="640"' in html
    assert 'data-height="360"' in html
    assert "window.__timelines=window.__timelines||{}" in js
    assert "window.__timelines['motion-os-master']=tl" in js
    assert "timeline({paused:true})" in js
    assert "fetch(" not in js
    assert "Math.random" not in js
    assert "Date.now" not in js
    assert "repeat:-1" not in js.replace(" ", "")


def test_hyperframes_render_contract_uses_frame_count_as_visual_authority():
    spec = compile_editing_graph_to_hyperframes(fixture_graph(), width=640, height=360, fps=30)
    contract = build_hyperframes_render_contract(spec)
    assert contract["expected_frames"] == 90
    assert contract["visual_duration_authority"] == "frame_count/fps"
    assert contract["authority"] == "compiler_ready"


def _good_probe() -> dict:
    return {
        "codec": "h264",
        "width": 640,
        "height": 360,
        "fps_fraction": "30/1",
        "fps": 30.0,
        "frames": 90,
        "visual_duration_s": 3.0,
        "container_duration_s": 3.033,
        "bytes": 12345,
        "sha256": "a" * 64,
    }


def test_physical_verifier_accepts_bounded_mux_tail_without_using_it_as_duration_authority():
    verdict = evaluate_probe(
        _good_probe(), expected_width=640, expected_height=360, expected_fps=30, expected_frames=90
    )
    assert verdict["ok"] is True
    assert verdict["visual_duration_authority"] == "frame_count/fps"
    assert 0 < verdict["mux_tail_seconds"] < verdict["mux_tail_tolerance_s"]


def test_physical_verifier_rejects_wrong_frame_count_even_if_container_duration_looks_correct():
    media = deepcopy(_good_probe())
    media["frames"] = 89
    media["visual_duration_s"] = 89 / 30
    media["container_duration_s"] = 3.0
    verdict = evaluate_probe(
        media, expected_width=640, expected_height=360, expected_fps=30, expected_frames=90
    )
    assert verdict["ok"] is False
    assert "frame_count_mismatch" in verdict["errors"]
    assert "visual_duration_mismatch" in verdict["errors"]


def test_physical_verifier_rejects_excess_mux_tail_independently():
    media = deepcopy(_good_probe())
    media["container_duration_s"] = 3.25
    verdict = evaluate_probe(
        media, expected_width=640, expected_height=360, expected_fps=30, expected_frames=90
    )
    assert verdict["ok"] is False
    assert verdict["errors"] == ["mux_tail_out_of_bounds"]
