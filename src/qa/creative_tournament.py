from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Iterable

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

_MAX_PROVIDER_LEN = 128
_MAX_RUN_ID_LEN = 256
_MAX_ATTESTATION_ID_LEN = 256
_MAX_CANDIDATE_ID_LEN = 256


def _strict_identity(value: Any, field_name: str, *, max_length: int) -> str:
    if not isinstance(value, str):
        raise CreativeTournamentError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise CreativeTournamentError(f"{field_name} must be non-empty and have no surrounding whitespace")
    if len(value) > max_length:
        raise CreativeTournamentError(f"{field_name} exceeds maximum length {max_length}")
    return value


def _strict_sha256(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise CreativeTournamentError(f"{field_name} must be a string")
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
        raise CreativeTournamentError(f"{field_name} must be a 64-character hex digest")
    return value


def _strict_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise CreativeTournamentError(f"{field_name} must be a literal boolean")
    return value


def _strict_score(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CreativeTournamentError(f"{field_name} must be a finite numeric scalar, not a boolean or string")
    result = float(value)
    if not math.isfinite(result):
        raise CreativeTournamentError(f"{field_name} must be finite")
    if not 0.0 <= result <= 10.0:
        raise CreativeTournamentError("creative dimensions must be in [0, 10]")
    return result


def _validated_dimensions(dimensions: Any) -> dict[str, float]:
    if not isinstance(dimensions, dict):
        raise CreativeTournamentError("creative dimensions must be an object")
    missing = REQUIRED_DIMENSIONS - set(dimensions)
    if missing:
        raise CreativeTournamentError(f"missing creative dimensions: {sorted(missing)}")
    unknown = set(dimensions) - REQUIRED_DIMENSIONS
    if unknown:
        raise CreativeTournamentError(f"unknown creative dimensions: {sorted(unknown)}")
    return {
        key: _strict_score(dimensions[key], f"creative dimension {key}")
        for key in REQUIRED_DIMENSIONS
    }


@dataclass(frozen=True)
class CreativeReview:
    media_sha256: str
    provider: str
    provider_run_id: str | None
    dimensions: dict[str, float]
    provider_attested_media_review: bool
    provider_attestation_id: str | None = None
    full_video_scope: bool = False

    def __post_init__(self) -> None:
        _strict_sha256(self.media_sha256, "creative review media_sha256")
        _strict_identity(self.provider, "creative review provider", max_length=_MAX_PROVIDER_LEN)
        if self.provider_run_id is not None:
            _strict_identity(
                self.provider_run_id,
                "creative review provider_run_id",
                max_length=_MAX_RUN_ID_LEN,
            )
        _strict_bool(self.provider_attested_media_review, "provider_attested_media_review")
        _strict_bool(self.full_video_scope, "full_video_scope")
        if self.provider_attestation_id is not None:
            _strict_identity(
                self.provider_attestation_id,
                "provider_attestation_id",
                max_length=_MAX_ATTESTATION_ID_LEN,
            )
        normalized = _validated_dimensions(self.dimensions)
        object.__setattr__(self, "dimensions", normalized)

    @property
    def authoritative_evidence(self) -> bool:
        return bool(
            self.provider not in {"unbound", "fixture"}
            and self.provider_run_id
            and self.full_video_scope is True
            and self.provider_attestation_id
        )

    def content_hash(self) -> str:
        payload = {
            "media_sha256": self.media_sha256,
            "provider": self.provider,
            "provider_run_id": self.provider_run_id,
            "provider_attested_media_review": self.provider_attested_media_review,
            "provider_attestation_id": self.provider_attestation_id,
            "full_video_scope": self.full_video_scope,
            "dimensions": {key: round(self.dimensions[key], 6) for key in sorted(self.dimensions)},
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def creative_review_from_provider_payload(
    *,
    expected_media_sha256: str,
    expected_provider: str,
    expected_provider_run_id: str,
    payload: dict[str, Any],
) -> CreativeReview:
    """Parse untrusted provider output and bind authority to one exact candidate."""
    expected_media_sha256 = _strict_sha256(expected_media_sha256, "expected_media_sha256")
    expected_provider = _strict_identity(
        expected_provider, "expected_provider", max_length=_MAX_PROVIDER_LEN
    )
    expected_provider_run_id = _strict_identity(
        expected_provider_run_id,
        "expected_provider_run_id",
        max_length=_MAX_RUN_ID_LEN,
    )
    if expected_provider in {"unbound", "fixture"}:
        raise CreativeTournamentError("expected_provider must identify a real provider")
    if not isinstance(payload, dict):
        raise CreativeTournamentError("creative provider payload must be an object")

    requested_authority = _strict_bool(payload.get("authoritative", False), "authoritative")
    if requested_authority:
        required = {
            "provider",
            "provider_run_id",
            "media_sha256",
            "full_video_scope",
            "provider_attestation_id",
            "dimensions",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise CreativeTournamentError(
                "authoritative creative payload missing required fields: " + ", ".join(missing)
            )

    provider = expected_provider
    if "provider" in payload:
        provider = _strict_identity(payload["provider"], "provider", max_length=_MAX_PROVIDER_LEN)
        if provider != expected_provider:
            raise CreativeTournamentError("provider identity does not match expected creative provider")

    provider_run_id: str | None = None
    if "provider_run_id" in payload:
        provider_run_id = _strict_identity(
            payload["provider_run_id"], "provider_run_id", max_length=_MAX_RUN_ID_LEN
        )
        if provider_run_id != expected_provider_run_id:
            raise CreativeTournamentError(
                "provider_run_id does not match expected creative provider run"
            )

    provider_media_sha256: str | None = None
    if "media_sha256" in payload:
        provider_media_sha256 = _strict_sha256(payload["media_sha256"], "media_sha256")
        if provider_media_sha256 != expected_media_sha256:
            raise CreativeTournamentError(
                "media_sha256 does not match expected creative review candidate"
            )

    full_video_scope = False
    if "full_video_scope" in payload:
        full_video_scope = _strict_bool(payload["full_video_scope"], "full_video_scope")

    provider_attestation_id: str | None = None
    if "provider_attestation_id" in payload:
        provider_attestation_id = _strict_identity(
            payload["provider_attestation_id"],
            "provider_attestation_id",
            max_length=_MAX_ATTESTATION_ID_LEN,
        )

    if "provider_attested_media_review" in payload:
        _strict_bool(payload["provider_attested_media_review"], "provider_attested_media_review")

    dimensions = _validated_dimensions(payload.get("dimensions", {}))

    if requested_authority:
        if provider != expected_provider:
            raise CreativeTournamentError("provider identity does not match expected creative provider")
        if provider_run_id != expected_provider_run_id:
            raise CreativeTournamentError(
                "provider_run_id does not match expected creative provider run"
            )
        if provider_media_sha256 != expected_media_sha256:
            raise CreativeTournamentError(
                "media_sha256 does not match expected creative review candidate"
            )
        if full_video_scope is not True:
            raise CreativeTournamentError(
                "full_video_scope must be literal true for creative provider authority"
            )
        if provider_attestation_id is None:
            raise CreativeTournamentError(
                "provider_attestation_id is required for creative provider authority"
            )

    return CreativeReview(
        media_sha256=expected_media_sha256,
        provider=provider,
        provider_run_id=provider_run_id,
        dimensions=dimensions,
        provider_attested_media_review=False,
        provider_attestation_id=provider_attestation_id if requested_authority else None,
        full_video_scope=full_video_scope if requested_authority else False,
    )


@dataclass(frozen=True)
class CreativeCandidate:
    candidate_id: str
    media_sha256: str
    temporal: TemporalCritique
    creative: CreativeReview

    def __post_init__(self) -> None:
        _strict_identity(self.candidate_id, "candidate_id", max_length=_MAX_CANDIDATE_ID_LEN)
        _strict_sha256(self.media_sha256, "media_sha256")
        if self.media_sha256 != self.temporal.media_sha256:
            raise CreativeTournamentError(
                "creative candidate media_sha256 must match temporal critique media_sha256"
            )
        if self.media_sha256 != self.creative.media_sha256:
            raise CreativeTournamentError(
                "creative candidate media_sha256 must match creative review media_sha256"
            )

    @property
    def dimensions(self) -> dict[str, float]:
        return self.creative.dimensions

    @property
    def mean_score(self) -> float:
        return sum(self.dimensions[key] for key in REQUIRED_DIMENSIONS) / len(REQUIRED_DIMENSIONS)

    @property
    def threshold_failures(self) -> dict[str, tuple[float, float]]:
        return {
            key: (self.dimensions[key], target)
            for key, target in THRESHOLDS.items()
            if self.dimensions[key] < target
        }

    @property
    def release_ready(self) -> bool:
        return bool(
            self.creative.authoritative_evidence
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
    if not candidate.creative.authoritative_evidence:
        reasons.append("NON_AUTHORITATIVE_CREATIVE_REVIEW")
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

    ranked = sorted(
        items,
        key=lambda candidate: (
            candidate.release_ready,
            candidate.temporal.authoritative,
            candidate.creative.authoritative_evidence,
            round(candidate.mean_score, 6),
            round(candidate.temporal.score, 6),
            candidate.candidate_id,
        ),
        reverse=True,
    )
    reasons = {candidate.candidate_id: _reasons(candidate) for candidate in items}
    blocked = tuple(
        sorted(candidate.candidate_id for candidate in items if reasons[candidate.candidate_id])
    )
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
