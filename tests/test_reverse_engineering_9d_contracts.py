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
MANIFEST = ROOT / "forensics/references/screenrecording_20260826/golden/aggregate_9d/golden_output_fidelity_manifest_v2.json"
HISTORICAL_V1 = ROOT / "forensics/references/screenrecording_20260826/golden/aggregate_9d/golden_evidence_manifest.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def output_claim(data: dict, claim_id: str) -> dict:
    return next(item for item in data["output_claims"] if item["claim_id"] == claim_id)


def provenance_claim(data: dict, claim_id: str) -> dict:
    return next(item for item in data["provenance_claims"] if item["claim_id"] == claim_id)


def requirement(data: dict, dimension: str) -> dict:
    return next(item for item in data["requirements"] if item["dimension"] == dimension)


def test_v2_manifest_validates_and_remains_fail_closed():
    data = load_manifest()
    validate_qualification_manifest(data)
    result = compile_qualification_manifest(data)
    assert set(result["output_dimensions"]) == {
        "temporal","motion","camera","typography","depth","color","fx","audio","retention"
    }
    assert result["output_dimensions"]["temporal"]["qualified"] is True
    assert result["output_dimensions"]["retention"]["qualified"] is True
    assert result["output_fidelity_9d_validated"] is False
    assert result["canonical_template"] is False
    assert result["diagnostic_coverage_ratio_is_promotion_authority"] is False
    assert result["output_defect_frontier"]


def test_historical_v1_is_not_current_executable_authority():
    data = json.loads(HISTORICAL_V1.read_text())
    with pytest.raises(QualificationError, match="unsupported manifest schema"):
        validate_qualification_manifest(data)


def test_stale_scene_evidence_requires_explicit_output_equivalence():
    data = copy.deepcopy(load_manifest())
    ref = next(item for item in data["evidence"] if item["evidence_id"] == "S11_SOURCE_QUAL")
    ref.pop("equivalence_proof_id")
    with pytest.raises(QualificationError, match="without equivalence proof"):
        validate_qualification_manifest(data)


def test_qualified_output_claim_cannot_be_inference_authority():
    data = copy.deepcopy(load_manifest())
    item = output_claim(data, "S04_TIMING")
    item["authority"] = "EVIDENCE_BOUND_INFERENCE"
    with pytest.raises(QualificationError, match="requires PHYSICALLY_MEASURED"):
        validate_qualification_manifest(data)


def test_authoring_provenance_cannot_enter_output_promotion_graph():
    data = copy.deepcopy(load_manifest())
    requirement(data, "audio")["claim_ids"] = ["PROV_ORIGINAL_STEMS"]
    with pytest.raises(QualificationError, match="authoring provenance claim"):
        validate_qualification_manifest(data)


def test_typography_layout_box_cannot_redefine_visible_glyph_fidelity():
    data = copy.deepcopy(load_manifest())
    item = output_claim(data, "S04_GLYPHS")
    item["claim_kind"] = "layout_proxy"
    requirement(data, "typography")["claim_ids"] = ["S04_GLYPHS"]
    for other in data["output_claims"]:
        if other["dimension"] == "typography" and other["claim_id"] != "S04_GLYPHS":
            other["required"] = False
    with pytest.raises(QualificationError, match="semantically laundered"):
        validate_qualification_manifest(data)


def test_audio_onset_only_cannot_redefine_audio_event_grammar():
    data = copy.deepcopy(load_manifest())
    item = output_claim(data, "PROGRAM_AUDIO_GRAMMAR")
    item["claim_kind"] = "onset_timing_proxy"
    with pytest.raises(QualificationError, match="semantically laundered"):
        validate_qualification_manifest(data)


def test_required_output_claim_cannot_be_orphaned():
    data = copy.deepcopy(load_manifest())
    requirement(data, "motion")["claim_ids"].remove("S11_KINEMATICS")
    with pytest.raises(QualificationError, match="required output claims missing"):
        validate_qualification_manifest(data)


def test_required_dimension_cannot_be_removed():
    data = copy.deepcopy(load_manifest())
    data["requirements"] = [r for r in data["requirements"] if r["dimension"] != "fx"]
    with pytest.raises(QualificationError, match="missing dimensions"):
        validate_qualification_manifest(data)


def test_blocked_provenance_does_not_create_output_defects():
    data = load_manifest()
    result = compile_qualification_manifest(data)
    output_ids = {item["claim_id"] for item in result["output_defect_frontier"]}
    assert "PROV_ORIGINAL_AE_GRAPH" not in output_ids
    assert "PROV_ORIGINAL_STEMS" not in output_ids
    assert result["authoring_provenance_complete"] is False
    assert result["authoring_provenance_is_output_fidelity_gate"] is False


def test_output_equivalence_bridges_revision_only_not_semantic_strength():
    result = compile_qualification_manifest(load_manifest())
    assert result["scene_heads"]["S11_UI_LIST"] == "988e91893cb498f720b9c2656b3d6d85f2d56300"
    assert result["scene_heads"]["S14_AUDIO_VISUAL_TEXTO"] == "12592bd8f8149767fafcb0ad0aa6036250ce540c"
    assert result["output_dimensions"]["typography"]["qualified"] is False
    assert result["output_dimensions"]["fx"]["qualified"] is False


def test_retention_grammar_is_observable_not_intent_claim():
    data = load_manifest()
    claim = output_claim(data, "PROGRAM_RETENTION_OUTPUT")
    assert claim["status"] == "QUALIFIED"
    assert claim["authority"] == "PHYSICALLY_MEASURED"
    intent = provenance_claim(data, "PROV_EDITOR_RETENTION_INTENT")
    assert intent["status"] == "NOT_MEASURED"
    result = compile_qualification_manifest(data)
    assert result["output_dimensions"]["retention"]["qualified"] is True


def test_diagnostic_coverage_never_promotes_partial_program():
    result = compile_qualification_manifest(load_manifest())
    assert result["diagnostic_output_claim_coverage_ratio"] > 0
    assert result["diagnostic_coverage_ratio_is_promotion_authority"] is False
    assert result["output_fidelity_9d_validated"] is False
    assert result["promotion_state"] == "OUTPUT_FIDELITY_PARTIAL"
