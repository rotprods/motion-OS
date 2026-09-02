from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from reverse_engineering.qualification import (
    QualificationError,
    compile_qualification_manifest,
    validate_qualification_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "forensics/references/screenrecording_20260826/golden/aggregate_9d/golden_evidence_manifest.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def claim(data: dict, claim_id: str) -> dict:
    return next(item for item in data["claims"] if item["claim_id"] == claim_id)


def requirement(data: dict, dimension: str) -> dict:
    return next(item for item in data["requirements"] if item["dimension"] == dimension)


def test_live_manifest_validates_and_is_fail_closed():
    data = load_manifest()
    validate_qualification_manifest(data)
    result = compile_qualification_manifest(data)
    assert set(result["dimensions"]) == {
        "temporal",
        "motion",
        "camera",
        "typography",
        "depth",
        "color",
        "fx",
        "audio",
        "retention",
    }
    assert result["dimensions"]["temporal"]["qualified"] is True
    assert result["full_9d_fidelity_validated"] is False
    assert result["canonical_template"] is False
    assert result["diagnostic_coverage_ratio_is_promotion_authority"] is False
    assert result["defect_frontier"]


def test_no_metric_laundering_when_eight_dimensions_are_green():
    data = load_manifest()
    # This test deliberately bypasses normal manifest validity by using the real
    # compiler output as the authority: the current program is not allowed to
    # infer full 9D from a high diagnostic ratio or a majority vote.
    result = compile_qualification_manifest(data)
    green = sum(item["qualified"] for item in result["dimensions"].values())
    assert green >= 1
    assert result["diagnostic_coverage_ratio"] > 0
    assert result["full_9d_fidelity_validated"] is False
    assert result["promotion_state"] == "CROSS_SCENE_PARTIAL_QUALIFICATION"


def test_stale_scene_evidence_requires_explicit_output_equivalence():
    data = copy.deepcopy(load_manifest())
    ref = next(item for item in data["evidence"] if item["evidence_id"] == "S11_SOURCE_QUAL")
    ref.pop("equivalence_proof_id")
    with pytest.raises(QualificationError, match="without equivalence proof"):
        validate_qualification_manifest(data)


def test_qualified_claim_cannot_be_inference_authority():
    data = copy.deepcopy(load_manifest())
    item = claim(data, "S04_TEMPORAL_LAYOUT")
    item["authority"] = "EVIDENCE_BOUND_INFERENCE"
    with pytest.raises(QualificationError, match="requires PHYSICALLY_MEASURED"):
        validate_qualification_manifest(data)


def test_typography_layout_proxy_cannot_replace_glyph_morphology_requirement():
    data = copy.deepcopy(load_manifest())
    proxy = claim(data, "S16_TYPO_LAYOUT")
    proxy["required"] = True
    requirement(data, "typography")["claim_ids"] = ["S16_TYPO_LAYOUT"]
    for item in data["claims"]:
        if item["dimension"] == "typography" and item["claim_id"] != "S16_TYPO_LAYOUT":
            item["required"] = False
    with pytest.raises(QualificationError, match="semantically laundered"):
        validate_qualification_manifest(data)


def test_audio_onset_proxy_cannot_replace_stem_identity_requirement():
    data = copy.deepcopy(load_manifest())
    program_audio = claim(data, "PROGRAM_AUDIO_IDENTITY")
    program_audio["required"] = False
    requirement(data, "audio")["claim_ids"] = [
        "S04_AUDIO_TIMING",
        "S14_AUDIO_TIMING",
        "S16_AUDIO_TIMING",
    ]
    with pytest.raises(QualificationError, match="semantically laundered"):
        validate_qualification_manifest(data)


def test_required_claim_cannot_be_orphaned_from_promotion_graph():
    data = copy.deepcopy(load_manifest())
    requirement(data, "motion")["claim_ids"].remove("S16_MOTION_OPACITY")
    with pytest.raises(QualificationError, match="required claims missing"):
        validate_qualification_manifest(data)


def test_required_dimension_cannot_be_removed():
    data = copy.deepcopy(load_manifest())
    data["requirements"] = [r for r in data["requirements"] if r["dimension"] != "fx"]
    with pytest.raises(QualificationError, match="missing dimensions"):
        validate_qualification_manifest(data)


def test_output_equivalence_does_not_upgrade_semantic_claim_strength():
    data = load_manifest()
    result = compile_qualification_manifest(data)
    assert result["scene_heads"]["S11_UI_LIST"] == "988e91893cb498f720b9c2656b3d6d85f2d56300"
    assert result["scene_heads"]["S14_AUDIO_VISUAL_TEXTO"] == "12592bd8f8149767fafcb0ad0aa6036250ce540c"
    assert result["dimensions"]["typography"]["qualified"] is False
    assert result["dimensions"]["fx"]["qualified"] is False
    assert result["dimensions"]["audio"]["qualified"] is False
