import hashlib

import pytest

from src.benchmarks.authority import BenchmarkEvidenceError, BriefStatus
from src.benchmarks.physical_evidence import MECHANICAL_EVIDENCE_CLASS, MechanicalBenchmarkEvidence


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def payload(**overrides):
    base = {
        "brief_id": "browser-launch-01",
        "style_family": "industrial_white_product",
        "brief_sha256": sha("brief"),
        "runtime_spec_sha256": sha("spec"),
        "artifact_sha256": sha("artifact"),
        "test_run_id": "run-1",
        "source_commit": "abc123",
        "frame_count": 90,
        "fps": 30.0,
        "visual_duration_seconds": 3.0,
        "mechanical_pass": True,
        "creative_authority": "BLOCKED",
        "style_fidelity_authority": "BLOCKED",
        "evidence_class": MECHANICAL_EVIDENCE_CLASS,
    }
    base.update(overrides)
    return base


def test_mechanical_pass_maps_to_blocked_ledger_entry():
    evidence = MechanicalBenchmarkEvidence.from_payload(payload())
    entry = evidence.to_blocked_ledger_entry()
    assert entry.status is BriefStatus.BLOCKED
    assert entry.artifact_sha256 == sha("artifact")
    assert "mechanical_render_only" in entry.findings
    assert "creative_review_missing" in entry.findings
    assert "style_fidelity_review_missing" in entry.findings


def test_mechanical_evidence_cannot_claim_creative_authority():
    with pytest.raises(BenchmarkEvidenceError, match="creative or style-fidelity"):
        MechanicalBenchmarkEvidence.from_payload(payload(creative_authority="VERIFIED"))


def test_mechanical_evidence_cannot_claim_style_fidelity_authority():
    with pytest.raises(BenchmarkEvidenceError, match="creative or style-fidelity"):
        MechanicalBenchmarkEvidence.from_payload(payload(style_fidelity_authority="VERIFIED"))


def test_wrong_evidence_class_fails_closed():
    with pytest.raises(BenchmarkEvidenceError, match="class mismatch"):
        MechanicalBenchmarkEvidence.from_payload(payload(evidence_class="STYLE_VERIFIED"))


def test_visual_duration_must_use_frame_count_over_fps():
    with pytest.raises(BenchmarkEvidenceError, match="frame_count/fps"):
        MechanicalBenchmarkEvidence.from_payload(payload(visual_duration_seconds=3.1))


def test_string_boolean_cannot_spoof_mechanical_pass():
    with pytest.raises(BenchmarkEvidenceError, match="literal boolean"):
        MechanicalBenchmarkEvidence.from_payload(payload(mechanical_pass="true"))


def test_failed_mechanical_record_cannot_enter_adapter():
    with pytest.raises(BenchmarkEvidenceError, match="mechanically passing"):
        MechanicalBenchmarkEvidence.from_payload(payload(mechanical_pass=False))


def test_missing_field_fails_closed():
    data = payload()
    data.pop("artifact_sha256")
    with pytest.raises(BenchmarkEvidenceError, match="missing fields"):
        MechanicalBenchmarkEvidence.from_payload(data)
