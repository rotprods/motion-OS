from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "qualification/golden_9d/golden_9d_matrix.json"
COMPILER_PATH = ROOT / "qualification/golden_9d/compile_readiness.py"
FAILURES_PATH = ROOT / "qualification/golden_9d/escaped_failure_families.json"


def load_compiler():
    spec = importlib.util.spec_from_file_location("golden_9d_compile_readiness", COMPILER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def matrix():
    return json.loads(MATRIX_PATH.read_text())


def test_matrix_has_exactly_nine_dimensions_and_four_golden_scenes():
    m = matrix()
    assert m["dimensions"] == ["temporal", "motion", "camera", "typography", "depth", "color", "fx", "audio", "retention"]
    assert set(m["scenes"]) == {"S04_CIENTIFICAMENTE", "S11_UI_LIST", "S14_AUDIO_VISUAL_TEXTO", "S16_FACTOR_X"}


def test_live_heads_and_exact_head_ci_are_bound_into_projection():
    m = matrix()
    expected = {
        "S04_CIENTIFICAMENTE": "8ec35a259399d7b196b40627d782315a019e65e2",
        "S11_UI_LIST": "988e91893cb498f720b9c2656b3d6d85f2d56300",
        "S14_AUDIO_VISUAL_TEXTO": "12592bd8f8149767fafcb0ad0aa6036250ce540c",
        "S16_FACTOR_X": "8e6fcb79d0d7958c0f023f128297059c97a7e674",
    }
    for scene, head in expected.items():
        assert m["scenes"][scene]["head_sha"] == head
        assert m["scenes"][scene]["ci"]["remotion_result"] == "SUCCESS"
        assert m["scenes"][scene]["ci"]["merge_safe_result"] == "SUCCESS"
        assert m["scenes"][scene]["artifact"]["digest"].startswith("sha256:")


def test_exact_and_structural_authority_are_not_conflated():
    m = matrix()
    s16 = m["scenes"]["S16_FACTOR_X"]["dimensions"]["typography"]
    assert s16["reconstruct_exact"]["state"] == "PARTIAL"
    assert "exact Factor X font" in s16["reconstruct_exact"]["blocked_aspects"]
    assert s16["structural_template"]["state"] == "QUALIFIED"

    s14_audio = m["scenes"]["S14_AUDIO_VISUAL_TEXTO"]["dimensions"]["audio"]
    assert s14_audio["reconstruct_exact"]["state"] == "PARTIAL"
    assert s14_audio["structural_template"]["state"] == "QUALIFIED"


def test_w2_projection_binds_exact_qualified_evidence_and_preserves_scene_limits():
    m = matrix()
    w2 = m["generated_from"]["t08_w2"]
    assert w2 == {
        "qualification_head": "80d8926f49873dabc64cc381e22806fc92740194",
        "workflow_run": 34600058526,
        "artifact_id": 10263503237,
        "artifact_digest": "sha256:d9994c23d4915273d41ac14ffed1452bc696abae69c4cb1d8815398695633a78",
        "drive_artifact_id": "11P40ZMe2khhyHOKep3vGh3Q9Xe86u-Ro",
        "drive_evidence_summary_id": "1CCGajR2_ysAm6jqVh8HSbRMkTymywJK7",
        "drive_qualification_id": "1rlNiPy70UzTVm-EzIlozRwgpXUkRJtQ7",
    }

    s04 = m["scenes"]["S04_CIENTIFICAMENTE"]["dimensions"]
    assert s04["camera"]["reconstruct_exact"]["state"] == "PARTIAL"
    assert s04["camera"]["structural_template"]["state"] == "PARTIAL"
    assert any("subject-precomp" in x for x in s04["camera"]["reconstruct_exact"]["blocked_aspects"])
    assert s04["depth"]["structural_template"]["state"] == "PARTIAL"

    for scene_id in ("S11_UI_LIST", "S14_AUDIO_VISUAL_TEXTO", "S16_FACTOR_X"):
        dims = m["scenes"][scene_id]["dimensions"]
        assert dims["camera"]["reconstruct_exact"]["state"] == "PARTIAL"
        assert dims["camera"]["structural_template"]["state"] == "QUALIFIED"
        assert dims["camera"]["structural_template"]["blocked_aspects"] == []
        assert dims["depth"]["reconstruct_exact"]["state"] == "PARTIAL"
        assert dims["depth"]["structural_template"]["state"] == "PARTIAL"

    assert m["aggregate"]["reconstruct_exact"]["camera"] == "PARTIAL_ACROSS_ALL_GOLDENS"
    assert m["aggregate"]["reconstruct_exact"]["depth"] == "PARTIAL_ACROSS_ALL_GOLDENS"
    assert m["aggregate"]["structural_template"]["camera"] == "MIXED_QUALIFIED_PARTIAL_S04_CAUSAL_LIMIT"
    assert m["aggregate"]["structural_template"]["depth"] == "PARTIAL_ACROSS_ALL_GOLDENS"


def test_visible_layout_success_does_not_promote_full_9d():
    m = matrix()
    assert m["promotion"]["full_9d_fidelity_validated"] is False
    assert m["promotion"]["structural_template_9d_validated"] is False
    assert m["promotion"]["canonical_template"] is False
    assert m["barriers"]["issue_48_open"] is True


def test_readiness_compiler_fails_closed_without_weighted_score():
    module = load_compiler()
    r = module.compile_readiness(matrix())
    assert r["modes"]["reconstruct_exact"]["all_9d_qualified"] is False
    assert r["modes"]["structural_template"]["all_9d_qualified"] is False
    assert r["promotion"]["canonical_template_eligible"] is False
    assert "No weighted or averaged score" in r["law"]


def test_qualified_dimension_cannot_hide_blocked_aspects():
    module = load_compiler()
    m = matrix()
    bad = json.loads(json.dumps(m))
    q = bad["scenes"]["S04_CIENTIFICAMENTE"]["dimensions"]["temporal"]["reconstruct_exact"]
    q["blocked_aspects"] = ["hidden blocker"]
    try:
        module.compile_readiness(bad)
    except ValueError as exc:
        assert "qualified state still declares blockers" in str(exc)
    else:
        raise AssertionError("compiler accepted a QUALIFIED state with hidden blockers")


def test_escaped_failure_corpus_contains_cross_scene_oracle_and_projection_invariants():
    d = json.loads(FAILURES_PATH.read_text())
    families = {x["family"] for x in d["families"]}
    assert "MEASUREMENT_TARGET_IDENTITY_NOT_ISOLATED" in families
    assert "HAND_AUTHORED_SPARSE_PROJECTION_NOT_MECHANICALLY_DERIVED_FROM_FULL_FRAME_AUTHORITY" in families
    assert "CROSS_AUTHORITY_GEOMETRY_COMPARISON" in families
    assert "DESCENDING_PHYSICAL_AXIS_USED_DIRECTLY_AS_MONOTONIC_INTERPOLATION_DOMAIN" in families
    assert "CONVERSATIONAL_EXECUTION_CLAIM_WITHOUT_DURABLE_PROVIDER_EVIDENCE" in families
