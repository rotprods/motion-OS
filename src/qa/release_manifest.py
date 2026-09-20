from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from src.qa.creative_tournament import CreativeCandidate, TournamentResult, run_tournament
from src.qa.provider_authority import (
    ProviderAuthorityClaim,
    ProviderAuthorityVerificationError,
    ProviderAuthorityVerifier,
    VerifiedProviderAuthority,
    verify_provider_authority,
)


class ReleaseManifestError(ValueError):
    pass


@dataclass(frozen=True)
class CreativeReleaseManifest:
    candidate_id: str
    media_sha256: str
    temporal_evidence_hash: str
    temporal_provider: str
    temporal_provider_run_id: str
    temporal_provider_attestation_id: str
    temporal_full_video_scope: bool
    temporal_authority_verifier_id: str
    temporal_authority_receipt_sha256: str
    creative_evidence_hash: str
    creative_provider: str
    creative_provider_run_id: str
    creative_provider_attestation_id: str
    creative_full_video_scope: bool
    creative_authority_verifier_id: str
    creative_authority_receipt_sha256: str
    temporal_score: float
    creative_mean_score: float
    ranked_candidate_ids: tuple[str, ...]
    manifest_sha256: str


def _claim_for_temporal(candidate: CreativeCandidate) -> ProviderAuthorityClaim:
    temporal = candidate.temporal
    if not temporal.provider_run_id:
        raise ReleaseManifestError("release candidate missing temporal provider run identity")
    if not temporal.provider_attestation_id:
        raise ReleaseManifestError("release candidate missing temporal provider attestation identity")
    if temporal.full_video_scope is not True:
        raise ReleaseManifestError("release candidate missing temporal full-video scope authority")
    return ProviderAuthorityClaim(
        purpose="temporal_multimodal",
        provider=temporal.provider,
        provider_run_id=temporal.provider_run_id,
        media_sha256=candidate.media_sha256,
        full_video_scope=True,
        provider_attestation_id=temporal.provider_attestation_id,
    )


def _claim_for_creative(candidate: CreativeCandidate) -> ProviderAuthorityClaim:
    creative = candidate.creative
    if not creative.provider_run_id:
        raise ReleaseManifestError("release candidate missing creative provider run identity")
    if not creative.provider_attestation_id:
        raise ReleaseManifestError("release candidate missing creative provider attestation identity")
    if creative.full_video_scope is not True:
        raise ReleaseManifestError("release candidate missing creative full-video scope authority")
    return ProviderAuthorityClaim(
        purpose="creative_review",
        provider=creative.provider,
        provider_run_id=creative.provider_run_id,
        media_sha256=candidate.media_sha256,
        full_video_scope=True,
        provider_attestation_id=creative.provider_attestation_id,
    )


def _verify_release_authority(
    candidate: CreativeCandidate,
    verifier: ProviderAuthorityVerifier | None,
) -> tuple[VerifiedProviderAuthority, VerifiedProviderAuthority]:
    try:
        temporal = verify_provider_authority(_claim_for_temporal(candidate), verifier)
        creative = verify_provider_authority(_claim_for_creative(candidate), verifier)
    except ProviderAuthorityVerificationError as exc:
        raise ReleaseManifestError(str(exc)) from exc
    return temporal, creative


def _payload(
    candidate: CreativeCandidate,
    result: TournamentResult,
    temporal_authority: VerifiedProviderAuthority,
    creative_authority: VerifiedProviderAuthority,
) -> dict:
    return {
        "candidate_id": candidate.candidate_id,
        "media_sha256": candidate.media_sha256,
        "temporal_evidence_hash": candidate.temporal.evidence_hash,
        "temporal_provider": candidate.temporal.provider,
        "temporal_provider_run_id": temporal_authority.claim.provider_run_id,
        "temporal_provider_attestation_id": temporal_authority.claim.provider_attestation_id,
        "temporal_full_video_scope": True,
        "temporal_authority_verifier_id": temporal_authority.verifier_id,
        "temporal_authority_receipt_sha256": temporal_authority.receipt_sha256,
        "creative_evidence_hash": candidate.creative.content_hash(),
        "creative_provider": candidate.creative.provider,
        "creative_provider_run_id": creative_authority.claim.provider_run_id,
        "creative_provider_attestation_id": creative_authority.claim.provider_attestation_id,
        "creative_full_video_scope": True,
        "creative_authority_verifier_id": creative_authority.verifier_id,
        "creative_authority_receipt_sha256": creative_authority.receipt_sha256,
        "temporal_score": round(candidate.temporal.score, 6),
        "creative_mean_score": round(candidate.mean_score, 6),
        "ranked_candidate_ids": list(result.ranked_candidate_ids),
    }


def build_release_manifest(
    result: TournamentResult,
    candidates: Iterable[CreativeCandidate],
    *,
    authority_verifier: ProviderAuthorityVerifier | None = None,
) -> CreativeReleaseManifest:
    """Build release authority only after independent provider-attestation verification.

    Provider payload fields and parser-level `authoritative` booleans are untrusted data.
    They can rank/describe a candidate, but they cannot mint a release manifest on their
    own. The verifier is an injected trusted adapter outside that payload trust domain.
    """
    items = tuple(candidates)
    if not items:
        raise ReleaseManifestError("candidate set is empty")
    ids = [candidate.candidate_id for candidate in items]
    if len(ids) != len(set(ids)):
        raise ReleaseManifestError("duplicate candidate identity")

    canonical = run_tournament(items)
    if result != canonical:
        raise ReleaseManifestError("tournament result does not match deterministic recomputation")
    if canonical.release_candidate_id is None:
        raise ReleaseManifestError("tournament has no release-eligible candidate")

    by_id = {candidate.candidate_id: candidate for candidate in items}
    candidate = by_id[canonical.release_candidate_id]
    if not candidate.release_ready:
        raise ReleaseManifestError("release candidate no longer satisfies release gates")

    temporal_authority, creative_authority = _verify_release_authority(candidate, authority_verifier)
    payload = _payload(candidate, canonical, temporal_authority, creative_authority)
    manifest_sha = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return CreativeReleaseManifest(
        candidate_id=candidate.candidate_id,
        media_sha256=candidate.media_sha256,
        temporal_evidence_hash=candidate.temporal.evidence_hash,
        temporal_provider=candidate.temporal.provider,
        temporal_provider_run_id=temporal_authority.claim.provider_run_id,
        temporal_provider_attestation_id=temporal_authority.claim.provider_attestation_id,
        temporal_full_video_scope=True,
        temporal_authority_verifier_id=temporal_authority.verifier_id,
        temporal_authority_receipt_sha256=temporal_authority.receipt_sha256,
        creative_evidence_hash=candidate.creative.content_hash(),
        creative_provider=candidate.creative.provider,
        creative_provider_run_id=creative_authority.claim.provider_run_id,
        creative_provider_attestation_id=creative_authority.claim.provider_attestation_id,
        creative_full_video_scope=True,
        creative_authority_verifier_id=creative_authority.verifier_id,
        creative_authority_receipt_sha256=creative_authority.receipt_sha256,
        temporal_score=round(candidate.temporal.score, 6),
        creative_mean_score=round(candidate.mean_score, 6),
        ranked_candidate_ids=canonical.ranked_candidate_ids,
        manifest_sha256=manifest_sha,
    )
