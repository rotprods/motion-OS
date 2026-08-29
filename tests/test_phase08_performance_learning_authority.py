import pytest

from src.content.performance_learning import (
    EvidenceStage,
    LearningHypothesis,
    PerformanceRecord,
    approve_promoted_rule,
    attach_attribution,
    duration_mae,
    normalized_duration_error,
    promote_hypothesis,
)


def _ids(count: int) -> tuple[str, ...]:
    return tuple(f"content-{i}" for i in range(count))


def test_performance_record_rejects_negative_nonfinite_and_impossible_metrics():
    with pytest.raises(ValueError, match="views"):
        PerformanceRecord("c1", "instagram", views=-1)
    with pytest.raises(ValueError, match="views"):
        PerformanceRecord("c1", "instagram", views=True)
    with pytest.raises(ValueError, match="completion_rate"):
        PerformanceRecord("c1", "instagram", completion_rate=1.01)
    with pytest.raises(ValueError, match="retention_3s"):
        PerformanceRecord("c1", "instagram", retention_3s=float("nan"))
    with pytest.raises(ValueError, match="average_watch_time_s"):
        PerformanceRecord("c1", "instagram", average_watch_time_s=float("inf"))


def test_attribution_fails_closed_on_content_identity_mismatch():
    perf = PerformanceRecord("content-a", "instagram", views=100)
    with pytest.raises(ValueError, match="does not match"):
        attach_attribution({"content_id": "content-b"}, perf)
    with pytest.raises(ValueError, match="manifest.content_id"):
        attach_attribution({}, perf)


def test_attribution_is_explicitly_correlation_not_causation():
    perf = PerformanceRecord("content-a", "instagram", views=100, completion_rate=0.5)
    result = attach_attribution({"content_id": "content-a", "semantic_beats": []}, perf)
    assert result["causal_status"] == EvidenceStage.OBSERVED_CORRELATION.value


def test_independent_example_count_must_be_bound_to_unique_supporting_ids():
    h = LearningHypothesis("H1", "hypothesis", EvidenceStage.OBSERVED_CORRELATION, _ids(2))
    with pytest.raises(ValueError, match="must equal"):
        promote_hypothesis(h, independent_examples=200)
    with pytest.raises(ValueError, match="independent_examples"):
        promote_hypothesis(h, independent_examples=True)


def test_duplicate_supporting_ids_cannot_inflate_evidence_count():
    with pytest.raises(ValueError, match="unique"):
        LearningHypothesis("H1", "hypothesis", EvidenceStage.OBSERVED_CORRELATION, ("a", "a", "b", "b"))


def test_controlled_test_cannot_bypass_repeated_pattern_or_exist_without_test_id():
    h = LearningHypothesis("H1", "hypothesis", EvidenceStage.OBSERVED_CORRELATION, ("a",), controlled_test_id="ct-1")
    with pytest.raises(ValueError, match="cannot bypass"):
        promote_hypothesis(h, independent_examples=1, controlled_test_passed=True)

    enough_evidence_without_test_id = LearningHypothesis("H2", "hypothesis", EvidenceStage.OBSERVED_CORRELATION, _ids(4))
    with pytest.raises(ValueError, match="controlled_test_id"):
        promote_hypothesis(enough_evidence_without_test_id, independent_examples=4, controlled_test_passed=True)


def test_evidence_bound_path_can_reach_controlled_test_but_not_rule_automatically():
    evidence = _ids(4)
    h = LearningHypothesis(
        "H1",
        "hypothesis",
        EvidenceStage.OBSERVED_CORRELATION,
        evidence,
        controlled_test_id="ct-1",
    )
    tested = promote_hypothesis(h, independent_examples=4, controlled_test_passed=True)
    assert tested.stage == EvidenceStage.CONTROLLED_TEST
    with pytest.raises(PermissionError):
        approve_promoted_rule(tested, explicit_approval=False)
    with pytest.raises(PermissionError):
        approve_promoted_rule(tested, explicit_approval="true")
    with pytest.raises(ValueError, match="approval_evidence"):
        approve_promoted_rule(tested, explicit_approval=True)
    promoted = approve_promoted_rule(
        tested,
        explicit_approval=True,
        approval_evidence=("approval:human-review-42",),
    )
    assert promoted.stage == EvidenceStage.PROMOTED_RULE
    assert promoted.controlled_test_id == "ct-1"
    assert promoted.promotion_approval_evidence == ("approval:human-review-42",)


def test_direct_constructor_cannot_bypass_controlled_or_promoted_authority_requirements():
    with pytest.raises(ValueError, match="at least 4"):
        LearningHypothesis("H1", "hypothesis", EvidenceStage.CONTROLLED_TEST, ("a",), controlled_test_id="ct-1")
    with pytest.raises(ValueError, match="controlled_test_id"):
        LearningHypothesis("H1", "hypothesis", EvidenceStage.CONTROLLED_TEST, _ids(4))
    with pytest.raises(ValueError, match="PROMOTED_RULE"):
        LearningHypothesis("H1", "hypothesis", EvidenceStage.PROMOTED_RULE, _ids(4), controlled_test_id="ct-1")
    with pytest.raises(ValueError, match="valid only"):
        LearningHypothesis(
            "H1",
            "hypothesis",
            EvidenceStage.CONTROLLED_TEST,
            _ids(4),
            controlled_test_id="ct-1",
            promotion_approval_evidence=("approval:spoof",),
        )


def test_duration_metrics_reject_poisoned_nonfinite_or_zero_denominator_values():
    with pytest.raises(ValueError, match="duration_estimate_s"):
        duration_mae([{"duration_estimate_s": float("nan"), "render": {"actual_duration_s": 1.0}}])
    with pytest.raises(ValueError, match="actual_duration_s"):
        duration_mae([{"duration_estimate_s": 1.0, "render": {"actual_duration_s": float("inf")}}])
    with pytest.raises(ValueError, match="> 0"):
        normalized_duration_error([{"duration_estimate_s": 1.0, "render": {"actual_duration_s": 0.0}}])


def test_duration_metrics_preserve_valid_behavior():
    records = [
        {"duration_estimate_s": 10.0, "render": {"actual_duration_s": 8.0}},
        {"duration_estimate_s": 9.0, "render": {"actual_duration_s": 10.0}},
    ]
    assert duration_mae(records) == 1.5
    assert normalized_duration_error(records) == 0.175
