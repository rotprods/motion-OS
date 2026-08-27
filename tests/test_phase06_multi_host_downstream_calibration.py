from pathlib import Path
import tempfile

import pytest

from content.downstream_integrity import (
    DownstreamIntegrityError,
    require_verified_downstream_handoff,
    verify_downstream_handoff,
)
from content.production_calibration import (
    AppendOnlyCalibrationCorpus,
    EvidenceClass,
    ProductionObservation,
    summarize_qualification,
)


def _handoff():
    return {
        "provenance_root": "PRV_abc",
        "replay_fingerprint": "MNF_xyz",
        "semantic_beat_ids": ["B00_HOOK", "B01_PROOF"],
    }


def test_downstream_handoff_accepts_exact_authority_identity():
    result = verify_downstream_handoff(
        _handoff(),
        expected_provenance_root="PRV_abc",
        expected_replay_fingerprint="MNF_xyz",
        expected_beat_ids=["B00_HOOK", "B01_PROOF"],
    )
    assert result.ok
    assert result.errors == ()


@pytest.mark.parametrize("field,value", [
    ("provenance_root", "PRV_mutated"),
    ("replay_fingerprint", "MNF_mutated"),
    ("semantic_beat_ids", ["B01_PROOF", "B00_HOOK"]),
    ("semantic_beat_ids", ["B00_HOOK", "B00_HOOK"]),
])
def test_downstream_handoff_fails_closed_on_identity_mutation(field, value):
    handoff = _handoff()
    handoff[field] = value
    with pytest.raises(DownstreamIntegrityError):
        require_verified_downstream_handoff(
            handoff,
            expected_provenance_root="PRV_abc",
            expected_replay_fingerprint="MNF_xyz",
            expected_beat_ids=["B00_HOOK", "B01_PROOF"],
        )


def _observation(i: int, *, driver: str = "MONEY", topic: str = "ai") -> ProductionObservation:
    return ProductionObservation(
        production_id=f"P{i:03d}",
        topic_family=topic,
        primary_driver=driver,
        icp_id="ICP_ROT",
        predicted_duration_s=39.0,
        actual_duration_s=40.0,
        clarity_score=9.3,
        hook_score=9.2,
        cta_score=8.8,
        pronunciation_errors=0,
        pronunciation_checks=20,
        claim_violations=0,
        evidence_class=EvidenceClass.OBSERVATIONAL,
    )


def test_calibration_corpus_is_append_only_jsonl_and_does_not_promote_rules():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "observations.jsonl"
        corpus = AppendOnlyCalibrationCorpus(path)
        corpus.append(_observation(1))
        corpus.append(_observation(2))
        lines = path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        summary = summarize_qualification([_observation(1), _observation(2)])
        assert summary["qualified"] is False
        assert summary["automatic_rule_promotion"] is False
        assert summary["pronunciation_checks"] == 40
        assert summary["pronunciation_error_rate"] == 0.0


def test_calibration_corpus_rejects_duplicate_production_ids():
    with tempfile.TemporaryDirectory() as td:
        corpus = AppendOnlyCalibrationCorpus(Path(td) / "observations.jsonl")
        corpus.append(_observation(1))
        with pytest.raises(ValueError, match="duplicate production_id"):
            corpus.append(_observation(1))


def test_empirical_gate_requires_full_coverage_not_just_good_scores():
    drivers = ["MONEY", "LOVE", "HEALTH", "PERSONAL_GROWTH"]
    topics = ["ai", "marketing", "filmmaking", "agents", "product"]
    rows = [
        _observation(i, driver=drivers[i % len(drivers)], topic=topics[i % len(topics)])
        for i in range(30)
    ]
    summary = summarize_qualification(rows)
    assert summary["qualified"] is True
    assert summary["production_count"] == 30
    assert summary["topic_family_count"] == 5


def test_empirical_gate_uses_true_pronunciation_error_rate():
    rows = [_observation(i) for i in range(30)]
    rows[0] = ProductionObservation(**{**rows[0].__dict__, "pronunciation_errors": 7})
    summary = summarize_qualification(rows)
    assert summary["pronunciation_error_rate"] > 0.01
    assert "pronunciation_error_rate_gt_1pct" in summary["reasons"]
