from __future__ import annotations

from copy import deepcopy
import hashlib
import json

from scripts.build_hyperframes_runtime_fixture import fixture_graph
from scripts.verify_hyperframes_render import evaluate_probe, verify_compiler_provenance
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
    verdict = evaluate_probe(_good_probe(), expected_width=640, expected_height=360, expected_fps=30, expected_frames=90)
    assert verdict["ok"] is True
    assert verdict["visual_duration_authority"] == "frame_count/fps"
    assert 0 < verdict["mux_tail_seconds"] < verdict["mux_tail_tolerance_s"]


def test_physical_verifier_rejects_wrong_frame_count_even_if_container_duration_looks_correct():
    media = deepcopy(_good_probe())
    media["frames"] = 89
    media["visual_duration_s"] = 89 / 30
    media["container_duration_s"] = 3.0
    verdict = evaluate_probe(media, expected_width=640, expected_height=360, expected_fps=30, expected_frames=90)
    assert verdict["ok"] is False
    assert "frame_count_mismatch" in verdict["errors"]
    assert "visual_duration_mismatch" in verdict["errors"]


def test_physical_verifier_rejects_excess_mux_tail_independently():
    media = deepcopy(_good_probe())
    media["container_duration_s"] = 3.25
    verdict = evaluate_probe(media, expected_width=640, expected_height=360, expected_fps=30, expected_frames=90)
    assert verdict["ok"] is False
    assert verdict["errors"] == ["mux_tail_out_of_bounds"]


def _write_compiler_evidence(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    files = {"index.html":"<html>bound</html>", "motion.js":"const bound=true;"}
    hashes = {}
    for name, content in files.items():
        path = project / name
        path.write_text(content, encoding="utf-8")
        hashes[name] = hashlib.sha256(content.encode()).hexdigest()
    evidence = tmp_path / "compiler_evidence.json"
    evidence.write_text(json.dumps({"spec_sha256":"b"*64,"emitted_sha256":hashes}), encoding="utf-8")
    return project, evidence


def test_compiler_provenance_binds_exact_emitted_project_runtime_and_run(tmp_path):
    project, evidence = _write_compiler_evidence(tmp_path)
    result = verify_compiler_provenance(
        evidence, project_dir=project, runtime_version="0.8.17",
        run_id="33290000000", source_revision="c"*40,
    )
    assert result["ok"] is True
    assert result["spec_sha256"] == "b"*64
    assert result["runtime_run_id"] == "33290000000"
    assert result["source_revision"] == "c"*40
    assert set(result["verified_emitted_sha256"]) == {"index.html","motion.js"}


def test_foreign_or_mutated_project_cannot_satisfy_provenance(tmp_path):
    project, evidence = _write_compiler_evidence(tmp_path)
    (project / "motion.js").write_text("const foreign=true;", encoding="utf-8")
    result = verify_compiler_provenance(
        evidence, project_dir=project, runtime_version="0.8.17",
        run_id="33290000000", source_revision="c"*40,
    )
    assert result["ok"] is False
    assert "emitted_file_hash_mismatch:motion.js" in result["errors"]


def test_missing_runtime_run_or_wrong_version_blocks_verified_authority(tmp_path):
    project, evidence = _write_compiler_evidence(tmp_path)
    result = verify_compiler_provenance(
        evidence, project_dir=project, runtime_version="0.8.18",
        run_id=None, source_revision="c"*40,
    )
    assert result["ok"] is False
    assert "hyperframes_version_mismatch" in result["errors"]
    assert "runtime_run_id_missing" in result["errors"]


def test_invalid_source_revision_blocks_provenance(tmp_path):
    project, evidence = _write_compiler_evidence(tmp_path)
    result = verify_compiler_provenance(
        evidence, project_dir=project, runtime_version="0.8.17",
        run_id="run", source_revision="not-a-sha",
    )
    assert result["ok"] is False
    assert "source_revision_missing_or_invalid" in result["errors"]
