from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "qualification/golden_9d/w2_camera_depth_evidence.json"
SCRIPT = ROOT / "qualification/golden_9d/compile_camera_depth.py"
spec = importlib.util.spec_from_file_location("w2cd", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def load():
    return json.loads(EVIDENCE.read_text())


def test_w2_compiles_fail_closed_and_preserves_partial_authority():
    result = mod.compile_camera_depth(load())
    assert result["w2_state"] == "COMPLETE_WITH_EXPLICIT_CAUSAL_AND_DEPTH_UNKNOWNS"
    assert result["cross_golden"]["camera_reconstruct_exact"] == "PARTIAL"
    assert result["cross_golden"]["depth_structural_template"] == "PARTIAL"
    assert result["cross_golden"]["original_camera_or_ae_parenting"] == "BLOCKED_OR_UNKNOWN"


def test_micro_motion_universe_is_exact_closed_partition():
    result = mod.compile_camera_depth(load())
    m = result["micro_motion"]
    assert m == {
        "candidate_count": 220,
        "directional_corroborated": 95,
        "activity_without_translation_authority": 81,
        "not_corroborated": 41,
        "source_lock_excluded": 3,
    }


def test_micro_motion_cannot_self_promote():
    data = load()
    data["micro_motion_cross_golden"]["promotion"] = "QUALIFIED_CAMERA_MOTION"
    with pytest.raises(ValueError, match="self-promoted"):
        mod.compile_camera_depth(data)


def test_static_camera_claim_requires_static_background_common_vector():
    data = load()
    data["scenes"]["S14_AUDIO_VISUAL_TEXTO"]["flow_summary"]["background_abs_vector_median"] = 0.8
    with pytest.raises(ValueError, match="static camera/canvas claim contradicts"):
        mod.compile_camera_depth(data)


def test_s04_historical_reframe_never_becomes_global_camera_authority():
    data = load()
    data["scenes"]["S04_CIENTIFICAMENTE"]["camera"]["historical_action_A026"] = "PROMOTED_CAMERA"
    with pytest.raises(ValueError, match="A026"):
        mod.compile_camera_depth(data)


def test_s14_foreground_parent_cannot_be_laundered_into_camera():
    data = load()
    data["scenes"]["S14_AUDIO_VISUAL_TEXTO"]["camera"]["shared_parent_hypothesis"] = "CAMERA_TRANSLATION_PROVEN"
    with pytest.raises(ValueError):
        mod.compile_camera_depth(data)


def test_s16_source_lock_reflow_is_permanent_boundary():
    data = load()
    data["scenes"]["S16_FACTOR_X"]["camera"]["late_reflow_policy"] = "STRUCTURAL_CAMERA_GRAMMAR"
    with pytest.raises(ValueError, match="SOURCE_LOCK"):
        mod.compile_camera_depth(data)


def test_depth_cycle_is_rejected():
    data = load()
    depth = data["scenes"]["S16_FACTOR_X"]["depth"]
    depth["edges"].append({"front": "SUBJECT_PLATE", "behind": "FACTOR_X", "authority": "TEST"})
    with pytest.raises(ValueError, match="cycle"):
        mod.compile_camera_depth(data)


def test_unknown_depth_relation_cannot_be_silently_ordered():
    data = load()
    depth = data["scenes"]["S16_FACTOR_X"]["depth"]
    depth["edges"].append({"front": "COLUMN", "behind": "QUESTION_MARK", "authority": "UNSUPPORTED"})
    with pytest.raises(ValueError, match="UNKNOWN depth relation"):
        mod.compile_camera_depth(data)


def test_exact_source_sha_and_live_scene_heads_are_pinned():
    data = load()
    assert data["source_video"]["sha256"] == mod.CANONICAL_SOURCE_SHA
    refs = {sid: row["source_ref"] for sid, row in data["scenes"].items()}
    assert refs == {
        "S04_CIENTIFICAMENTE": "8ec35a259399d7b196b40627d782315a019e65e2",
        "S11_UI_LIST": "988e91893cb498f720b9c2656b3d6d85f2d56300",
        "S14_AUDIO_VISUAL_TEXTO": "12592bd8f8149767fafcb0ad0aa6036250ce540c",
        "S16_FACTOR_X": "8e6fcb79d0d7958c0f023f128297059c97a7e674",
    }


def test_scene_evidence_cannot_hide_missing_depth_reason():
    data = load()
    data["scenes"]["S11_UI_LIST"]["depth"]["unknown_relations"][0]["reason"] = ""
    with pytest.raises(ValueError, match="invalid UNKNOWN depth relation"):
        mod.compile_camera_depth(data)
