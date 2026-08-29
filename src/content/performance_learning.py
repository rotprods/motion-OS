from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from numbers import Real
from statistics import mean
from typing import Any, Iterable
import math


class EvidenceStage(str, Enum):
    OBSERVED_CORRELATION = "OBSERVED_CORRELATION"
    CANDIDATE_HYPOTHESIS = "CANDIDATE_HYPOTHESIS"
    REPEATED_PATTERN = "REPEATED_PATTERN"
    CONTROLLED_TEST = "CONTROLLED_TEST"
    PROMOTED_RULE = "PROMOTED_RULE"


def _nonnegative_int(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _finite_nonnegative(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite non-negative number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return normalized


def _rate(value: object, *, name: str) -> float:
    normalized = _finite_nonnegative(value, name=name)
    if normalized > 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _nonempty_id(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


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

    def __post_init__(self) -> None:
        _nonempty_id(self.content_id, name="content_id")
        _nonempty_id(self.platform, name="platform")
        for name in ("views", "rewatches", "saves", "shares", "comments", "cta_conversions", "follows"):
            value = getattr(self, name)
            if value is not None:
                _nonnegative_int(value, name=name)
        for name in ("retention_3s", "retention_5s", "completion_rate"):
            value = getattr(self, name)
            if value is not None:
                _rate(value, name=name)
        if self.average_watch_time_s is not None:
            _finite_nonnegative(self.average_watch_time_s, name="average_watch_time_s")


@dataclass(frozen=True)
class LearningHypothesis:
    hypothesis_id: str
    statement: str
    stage: EvidenceStage
    supporting_content_ids: tuple[str, ...]
    confounders: tuple[str, ...] = ()
    controlled_test_id: str | None = None

    def __post_init__(self) -> None:
        _nonempty_id(self.hypothesis_id, name="hypothesis_id")
        _nonempty_id(self.statement, name="statement")
        if not isinstance(self.stage, EvidenceStage):
            raise ValueError("stage must be an EvidenceStage")
        ids = tuple(_nonempty_id(item, name="supporting_content_id") for item in self.supporting_content_ids)
        if len(ids) != len(set(ids)):
            raise ValueError("supporting_content_ids must be unique")
        if self.stage in {EvidenceStage.CONTROLLED_TEST, EvidenceStage.PROMOTED_RULE}:
            _nonempty_id(self.controlled_test_id, name="controlled_test_id")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["stage"] = self.stage.value
        return data


def attach_attribution(manifest: dict[str, Any], perf: PerformanceRecord) -> dict[str, Any]:
    manifest_content_id = manifest.get("content_id")
    if not isinstance(perf, PerformanceRecord):
        raise TypeError("perf must be a validated PerformanceRecord")
    if not isinstance(manifest_content_id, str) or not manifest_content_id.strip():
        raise ValueError("manifest.content_id required for performance attribution")
    if manifest_content_id != perf.content_id:
        raise ValueError("performance content_id does not match manifest.content_id")
    return {
        "performance": asdict(perf),
        "attribution": {
            "content_id": manifest_content_id,
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
    if not isinstance(hypothesis, LearningHypothesis):
        raise TypeError("hypothesis must be a LearningHypothesis")
    examples = _nonnegative_int(independent_examples, name="independent_examples")
    evidence_count = len(set(hypothesis.supporting_content_ids))
    if examples != evidence_count:
        raise ValueError("independent_examples must equal unique supporting_content_ids evidence")
    if controlled_test_passed is not True and controlled_test_passed is not False:
        raise ValueError("controlled_test_passed must be boolean")

    stage = hypothesis.stage
    if stage == EvidenceStage.OBSERVED_CORRELATION and examples >= 2:
        stage = EvidenceStage.CANDIDATE_HYPOTHESIS
    if stage == EvidenceStage.CANDIDATE_HYPOTHESIS and examples >= 4:
        stage = EvidenceStage.REPEATED_PATTERN
    if controlled_test_passed:
        if stage != EvidenceStage.REPEATED_PATTERN:
            raise ValueError("controlled test cannot bypass repeated-pattern evidence stage")
        _nonempty_id(hypothesis.controlled_test_id, name="controlled_test_id")
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
    if explicit_approval is not True:
        raise PermissionError("explicit approval required to promote a performance rule")
    if hypothesis.stage != EvidenceStage.CONTROLLED_TEST:
        raise ValueError("only controlled-test hypotheses can become canonical rules")
    _nonempty_id(hypothesis.controlled_test_id, name="controlled_test_id")
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
            estimate = _finite_nonnegative(est, name="duration_estimate_s")
            observed = _finite_nonnegative(actual, name="actual_duration_s")
            errors.append(abs(estimate - observed))
    return round(mean(errors), 4) if errors else None


def normalized_duration_error(records: Iterable[dict[str, Any]]) -> float | None:
    errors = []
    for record in records:
        est = record.get("duration_estimate_s")
        actual = (record.get("render") or {}).get("actual_duration_s")
        if est is not None and actual is not None:
            estimate = _finite_nonnegative(est, name="duration_estimate_s")
            observed = _finite_nonnegative(actual, name="actual_duration_s")
            if observed == 0:
                raise ValueError("actual_duration_s must be > 0 for normalized duration error")
            errors.append(abs(estimate - observed) / observed)
    return round(mean(errors), 6) if errors else None
