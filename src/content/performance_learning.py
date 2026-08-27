from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from statistics import mean
from typing import Any, Iterable


class EvidenceStage(str, Enum):
    OBSERVED_CORRELATION = "OBSERVED_CORRELATION"
    CANDIDATE_HYPOTHESIS = "CANDIDATE_HYPOTHESIS"
    REPEATED_PATTERN = "REPEATED_PATTERN"
    CONTROLLED_TEST = "CONTROLLED_TEST"
    PROMOTED_RULE = "PROMOTED_RULE"


@dataclass(frozen=True)
class PerformanceRecord:
    content_id: str
    platform: str
    views: int | None = None
    retention_3s: float | None = None
    retention_5s: float | None = None
    average_watch_time_s: float | None = None
    completion_rate: float | None = None
    rewatches: int | None = None
    saves: int | None = None
    shares: int | None = None
    comments: int | None = None
    cta_conversions: int | None = None
    follows: int | None = None
    published_at: str | None = None
    topic_heat: str | None = None
    distribution_notes: str | None = None


@dataclass(frozen=True)
class LearningHypothesis:
    hypothesis_id: str
    statement: str
    stage: EvidenceStage
    supporting_content_ids: tuple[str, ...]
    confounders: tuple[str, ...] = ()
    controlled_test_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["stage"] = self.stage.value
        return data


def attach_attribution(manifest: dict[str, Any], perf: PerformanceRecord) -> dict[str, Any]:
    return {
        "performance": asdict(perf),
        "attribution": {
            "content_id": manifest.get("content_id"),
            "viral_driver": manifest.get("viral_driver"),
            "secondary_driver": manifest.get("secondary_driver"),
            "hook": manifest.get("hook"),
            "hook_family": manifest.get("hook_family"),
            "cta_placement": (manifest.get("cta") or {}).get("placement"),
            "duration_target_s": manifest.get("duration_target_s"),
            "duration_actual_s": (manifest.get("render") or {}).get("actual_duration_s"),
            "topic_family": manifest.get("topic_family"),
            "avatar_profile": (manifest.get("avatar") or {}).get("profile_id"),
            "beat_count": len(manifest.get("semantic_beats", [])),
            "published_at": perf.published_at,
            "topic_heat": perf.topic_heat,
            "distribution_notes": perf.distribution_notes,
        },
        "causal_status": EvidenceStage.OBSERVED_CORRELATION.value,
    }


def promote_hypothesis(hypothesis: LearningHypothesis, *, independent_examples: int,
                       controlled_test_passed: bool = False) -> LearningHypothesis:
    stage = hypothesis.stage
    if stage == EvidenceStage.OBSERVED_CORRELATION and independent_examples >= 2:
        stage = EvidenceStage.CANDIDATE_HYPOTHESIS
    if stage == EvidenceStage.CANDIDATE_HYPOTHESIS and independent_examples >= 4:
        stage = EvidenceStage.REPEATED_PATTERN
    if controlled_test_passed:
        stage = EvidenceStage.CONTROLLED_TEST
    # Promotion to rule is deliberately not automatic. Human/explicit policy approval is required.
    return LearningHypothesis(
        hypothesis_id=hypothesis.hypothesis_id,
        statement=hypothesis.statement,
        stage=stage,
        supporting_content_ids=hypothesis.supporting_content_ids,
        confounders=hypothesis.confounders,
        controlled_test_id=hypothesis.controlled_test_id,
    )


def approve_promoted_rule(hypothesis: LearningHypothesis, *, explicit_approval: bool) -> LearningHypothesis:
    if not explicit_approval:
        raise PermissionError("explicit approval required to promote a performance rule")
    if hypothesis.stage != EvidenceStage.CONTROLLED_TEST:
        raise ValueError("only controlled-test hypotheses can become canonical rules")
    return LearningHypothesis(
        hypothesis_id=hypothesis.hypothesis_id,
        statement=hypothesis.statement,
        stage=EvidenceStage.PROMOTED_RULE,
        supporting_content_ids=hypothesis.supporting_content_ids,
        confounders=hypothesis.confounders,
        controlled_test_id=hypothesis.controlled_test_id,
    )


def duration_mae(records: Iterable[dict[str, Any]]) -> float | None:
    errors = []
    for record in records:
        est = record.get("duration_estimate_s")
        actual = (record.get("render") or {}).get("actual_duration_s")
        if est is not None and actual is not None:
            errors.append(abs(float(est) - float(actual)))
    return round(mean(errors), 4) if errors else None


def normalized_duration_error(records: Iterable[dict[str, Any]]) -> float | None:
    errors = []
    for record in records:
        est = record.get("duration_estimate_s")
        actual = (record.get("render") or {}).get("actual_duration_s")
        if est is not None and actual:
            errors.append(abs(float(est) - float(actual)) / float(actual))
    return round(mean(errors), 6) if errors else None
