from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable
import json


class EvidenceClass(str, Enum):
    OBSERVATIONAL = "OBSERVATIONAL"
    CONTROLLED_TEST = "CONTROLLED_TEST"
    REPLICATED_TEST = "REPLICATED_TEST"
    APPROVED_RULE = "APPROVED_RULE"


@dataclass(frozen=True)
class ProductionObservation:
    production_id: str
    topic_family: str
    primary_driver: str
    icp_id: str
    predicted_duration_s: float
    actual_duration_s: float
    clarity_score: float
    hook_score: float
    cta_score: float
    pronunciation_errors: int
    claim_violations: int
    evidence_class: EvidenceClass = EvidenceClass.OBSERVATIONAL

    @property
    def normalized_duration_error(self) -> float:
        if self.actual_duration_s <= 0:
            raise ValueError("actual duration must be positive")
        return abs(self.predicted_duration_s - self.actual_duration_s) / self.actual_duration_s


class AppendOnlyCalibrationCorpus:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, observation: ProductionObservation) -> None:
        if not observation.production_id or not observation.topic_family or not observation.icp_id:
            raise ValueError("production_id, topic_family and icp_id required")
        if observation.primary_driver not in {"MONEY", "LOVE", "HEALTH", "PERSONAL_GROWTH"}:
            raise ValueError("unknown primary driver")
        if observation.predicted_duration_s <= 0 or observation.actual_duration_s <= 0:
            raise ValueError("durations must be positive")
        payload = asdict(observation)
        payload["evidence_class"] = observation.evidence_class.value
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")


def summarize_qualification(observations: Iterable[ProductionObservation]) -> dict[str, object]:
    rows = list(observations)
    if not rows:
        return {"qualified": False, "reasons": ["no_productions"]}
    topic_families = {row.topic_family for row in rows}
    drivers = {row.primary_driver for row in rows}
    mean_duration_error = sum(row.normalized_duration_error for row in rows) / len(rows)
    mean_clarity = sum(row.clarity_score for row in rows) / len(rows)
    mean_hook = sum(row.hook_score for row in rows) / len(rows)
    mean_cta = sum(row.cta_score for row in rows) / len(rows)
    pronunciation_rate = sum(row.pronunciation_errors for row in rows) / len(rows)
    claim_violations = sum(row.claim_violations for row in rows)
    reasons: list[str] = []
    if len(rows) < 30: reasons.append("production_count_lt_30")
    if len(topic_families) < 5: reasons.append("topic_families_lt_5")
    if drivers != {"MONEY", "LOVE", "HEALTH", "PERSONAL_GROWTH"}: reasons.append("driver_coverage_incomplete")
    if mean_duration_error > 0.07: reasons.append("duration_error_gt_7pct")
    if mean_clarity < 9: reasons.append("clarity_lt_9")
    if mean_hook < 9: reasons.append("hook_lt_9")
    if mean_cta < 8.5: reasons.append("cta_lt_8_5")
    if claim_violations != 0: reasons.append("claim_violations_nonzero")
    if pronunciation_rate > 0.01: reasons.append("pronunciation_error_rate_gt_1pct")
    return {
        "qualified": not reasons,
        "reasons": reasons,
        "production_count": len(rows),
        "topic_family_count": len(topic_families),
        "drivers": sorted(drivers),
        "mean_normalized_duration_error": mean_duration_error,
        "mean_clarity": mean_clarity,
        "mean_hook": mean_hook,
        "mean_cta": mean_cta,
        "pronunciation_errors_per_production": pronunciation_rate,
        "claim_violations": claim_violations,
        "automatic_rule_promotion": False,
    }
