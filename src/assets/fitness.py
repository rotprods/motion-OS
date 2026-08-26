from __future__ import annotations

from dataclasses import dataclass

from src.providers.contracts import ProviderCandidate
from src.providers.policy import policy_for_provider


@dataclass(frozen=True)
class AssetFitness:
    semantic_match: float
    style_match: float
    technical_fit: float
    licensing_confidence: float
    resolution: float = 1.0
    transparency_quality: float = 1.0

    def __post_init__(self):
        for name in ('semantic_match', 'style_match', 'technical_fit', 'licensing_confidence', 'resolution', 'transparency_quality'):
            value = getattr(self, name)
            if not 0 <= value <= 1:
                raise ValueError(f'{name} must be within [0,1]')

    @property
    def aggregate_score(self) -> float:
        score = (
            0.25 * self.semantic_match
            + 0.20 * self.style_match
            + 0.20 * self.technical_fit
            + 0.15 * self.resolution
            + 0.10 * self.transparency_quality
            + 0.10 * self.licensing_confidence
        )
        return round(score, 6)


@dataclass(frozen=True)
class AssetGateDecision:
    status: str
    score: float
    reasons: tuple[str, ...]


def evaluate_asset_candidate(
    candidate: ProviderCandidate,
    fitness: AssetFitness,
    *,
    final_asset_threshold: float = 0.78,
    reference_threshold: float = 0.60,
) -> AssetGateDecision:
    policy = policy_for_provider(candidate.provider)
    score = fitness.aggregate_score
    reasons: list[str] = []

    if candidate.usage_class == 'reference_only' or policy.default_usage_class == 'reference_only':
        if score < reference_threshold:
            reasons.append('reference_fitness_below_threshold')
            return AssetGateDecision('rejected', score, tuple(reasons))
        if candidate.license_state in {'restricted'}:
            reasons.append('license_restricted')
            return AssetGateDecision('rejected', score, tuple(reasons))
        reasons.append('reference_only_policy')
        return AssetGateDecision('approved_reference', score, tuple(reasons))

    if candidate.license_state not in {'permitted', 'owned'}:
        reasons.append('license_not_verified')
    if candidate.sha256 is None:
        reasons.append('sha256_missing')
    if fitness.technical_fit < 0.7:
        reasons.append('technical_fit_low')
    if fitness.semantic_match < 0.65:
        reasons.append('semantic_fit_low')
    if score < final_asset_threshold:
        reasons.append('aggregate_fitness_below_threshold')

    if reasons:
        return AssetGateDecision('quarantined', score, tuple(reasons))
    return AssetGateDecision('approved_asset', score, ())
