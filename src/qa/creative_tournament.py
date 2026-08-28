from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.qa.temporal_multimodal import TemporalCritique, release_eligible


class CreativeTournamentError(ValueError):
    pass


REQUIRED_DIMENSIONS = {
    "composition",
    "hierarchy",
    "typography",
    "motion_choreography",
    "transition_quality",
    "asset_realism",
    "asset_integration",
    "depth",
    "lighting",
    "style_coherence",
    "originality",
    "narrative_clarity",
    "brand_alignment",
    "final_frame_memorability",
    "professional_finish",
}

THRESHOLDS = {
    "composition": 8.5,
    "typography": 9.0,
    "asset_realism": 8.5,
    "motion_choreography": 9.0,
    "transition_quality": 8.8,
    "professional_finish": 9.0,
}


@dataclass(frozen=True)
class CreativeCandidate:
    candidate_id: str
    media_sha256: str
    temporal: TemporalCritique
    dimensions: dict[str, float]
    evidence_bound: bool

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise CreativeTournamentError("candidate_id required")
        if len(self.media_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.media_sha256.lower()):
            raise CreativeTournamentError("media_sha256 must be a 64-character hex digest")
        missing = REQUIRED_DIMENSIONS - set(self.dimensions)
        if missing:
            raise CreativeTournamentError(f"missing creative dimensions: {sorted(missing)}")
        if any(not 0.0 <= float(score) <= 10.0 for score in self.dimensions.values()):
            raise CreativeTournamentError("creative dimensions must be in [0, 10]")

    @property
    def mean_score(self) -> float:
        return sum(float(self.dimensions[key]) for key in REQUIRED_DIMENSIONS) / len(REQUIRED_DIMENSIONS)

    @property
    def threshold_failures(self) -> dict[str, tuple[float, float]]:
        return {
            key: (float(self.dimensions[key]), target)
            for key, target in THRESHOLDS.items()
            if float(self.dimensions[key]) < target
        }

    @property
    def release_ready(self) -> bool:
        return bool(
            self.evidence_bound
            and release_eligible(self.temporal)
            and self.mean_score >= 9.0
            and not self.threshold_failures
        )


@dataclass(frozen=True)
class TournamentResult:
    winner_id: str | None
    ranked_candidate_ids: tuple[str, ...]
    release_candidate_id: str | None
    blocked_candidate_ids: tuple[str, ...]
    reasons: dict[str, tuple[str, ...]]


def _reasons(candidate: CreativeCandidate) -> tuple[str, ...]:
    reasons: list[str] = []
    if not candidate.evidence_bound:
        reasons.append("UNBOUND_CREATIVE_EVIDENCE")
    if not candidate.temporal.authoritative:
        reasons.append("NON_AUTHORITATIVE_TEMPORAL_CRITIC")
    if not release_eligible(candidate.temporal):
        reasons.append("TEMPORAL_RELEASE_GATE_FAILED")
    if candidate.mean_score < 9.0:
        reasons.append("CREATIVE_MEAN_BELOW_9")
    if candidate.threshold_failures:
        reasons.append("CREATIVE_THRESHOLD_FAILURE")
    return tuple(dict.fromkeys(reasons))


def run_tournament(candidates: Iterable[CreativeCandidate]) -> TournamentResult:
    items = tuple(candidates)
    if not items:
        raise CreativeTournamentError("tournament requires at least one candidate")
    ids = [candidate.candidate_id for candidate in items]
    if len(ids) != len(set(ids)):
        raise CreativeTournamentError("candidate_id values must be unique")
    hashes_by_id = {candidate.candidate_id: candidate.media_sha256 for candidate in items}
    if len(hashes_by_id) != len(items):
        raise CreativeTournamentError("duplicate candidate identity")

    ranked = sorted(
        items,
        key=lambda candidate: (
            candidate.release_ready,
            candidate.temporal.authoritative,
            round(candidate.mean_score, 6),
            round(candidate.temporal.score, 6),
            candidate.candidate_id,
        ),
        reverse=True,
    )
    reasons = {candidate.candidate_id: _reasons(candidate) for candidate in items}
    blocked = tuple(sorted(candidate.candidate_id for candidate in items if reasons[candidate.candidate_id]))
    release_ready = [candidate for candidate in ranked if candidate.release_ready]
    release_id = release_ready[0].candidate_id if release_ready else None
    winner_id = ranked[0].candidate_id if ranked else None
    return TournamentResult(
        winner_id=winner_id,
        ranked_candidate_ids=tuple(candidate.candidate_id for candidate in ranked),
        release_candidate_id=release_id,
        blocked_candidate_ids=blocked,
        reasons=reasons,
    )
