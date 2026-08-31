from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from src.qa.creative_tournament import CreativeCandidate, TournamentResult, run_tournament


class ReleaseManifestError(ValueError):
    pass


@dataclass(frozen=True)
class CreativeReleaseManifest:
    candidate_id: str
    media_sha256: str
    temporal_evidence_hash: str
    temporal_provider: str
    temporal_provider_run_id: str
    creative_evidence_hash: str
    creative_provider: str
    creative_provider_run_id: str
    temporal_score: float
    creative_mean_score: float
    ranked_candidate_ids: tuple[str, ...]
    manifest_sha256: str


def _payload(candidate: CreativeCandidate, result: TournamentResult) -> dict:
    temporal_run_id = candidate.temporal.provider_run_id
    creative_run_id = candidate.creative.provider_run_id
    if not temporal_run_id:
        raise ReleaseManifestError("release candidate missing temporal provider run identity")
    if not creative_run_id:
        raise ReleaseManifestError("release candidate missing creative provider run identity")
    return {
        "candidate_id": candidate.candidate_id,
        "media_sha256": candidate.media_sha256,
        "temporal_evidence_hash": candidate.temporal.evidence_hash,
        "temporal_provider": candidate.temporal.provider,
        "temporal_provider_run_id": temporal_run_id,
        "creative_evidence_hash": candidate.creative.content_hash(),
        "creative_provider": candidate.creative.provider,
        "creative_provider_run_id": creative_run_id,
        "temporal_score": round(float(candidate.temporal.score), 6),
        "creative_mean_score": round(float(candidate.mean_score), 6),
        "ranked_candidate_ids": list(result.ranked_candidate_ids),
    }


def build_release_manifest(result: TournamentResult, candidates: Iterable[CreativeCandidate]) -> CreativeReleaseManifest:
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
    payload = _payload(candidate, canonical)
    manifest_sha = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return CreativeReleaseManifest(
        candidate_id=candidate.candidate_id,
        media_sha256=candidate.media_sha256,
        temporal_evidence_hash=candidate.temporal.evidence_hash,
        temporal_provider=candidate.temporal.provider,
        temporal_provider_run_id=str(candidate.temporal.provider_run_id),
        creative_evidence_hash=candidate.creative.content_hash(),
        creative_provider=candidate.creative.provider,
        creative_provider_run_id=str(candidate.creative.provider_run_id),
        temporal_score=round(float(candidate.temporal.score), 6),
        creative_mean_score=round(float(candidate.mean_score), 6),
        ranked_candidate_ids=canonical.ranked_candidate_ids,
        manifest_sha256=manifest_sha,
    )
