from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from src.qa.creative_tournament import CreativeCandidate, TournamentResult


class ReleaseManifestError(ValueError):
    pass


@dataclass(frozen=True)
class CreativeReleaseManifest:
    candidate_id: str
    media_sha256: str
    temporal_evidence_hash: str
    temporal_score: float
    creative_mean_score: float
    ranked_candidate_ids: tuple[str, ...]
    manifest_sha256: str


def _payload(candidate: CreativeCandidate, result: TournamentResult) -> dict:
    return {
        "candidate_id": candidate.candidate_id,
        "media_sha256": candidate.media_sha256,
        "temporal_evidence_hash": candidate.temporal.evidence_hash,
        "temporal_score": round(float(candidate.temporal.score), 6),
        "creative_mean_score": round(float(candidate.mean_score), 6),
        "ranked_candidate_ids": list(result.ranked_candidate_ids),
    }


def build_release_manifest(result: TournamentResult, candidates: Iterable[CreativeCandidate]) -> CreativeReleaseManifest:
    items = tuple(candidates)
    if result.release_candidate_id is None:
        raise ReleaseManifestError("tournament has no release-eligible candidate")
    if not items:
        raise ReleaseManifestError("candidate set is empty")
    ids = [candidate.candidate_id for candidate in items]
    if len(ids) != len(set(ids)):
        raise ReleaseManifestError("duplicate candidate identity")
    by_id = {candidate.candidate_id: candidate for candidate in items}
    if result.release_candidate_id not in by_id:
        raise ReleaseManifestError("release candidate missing from candidate set")
    if set(result.ranked_candidate_ids) != set(by_id):
        raise ReleaseManifestError("tournament ranking and candidate set disagree")
    candidate = by_id[result.release_candidate_id]
    if not candidate.release_ready:
        raise ReleaseManifestError("release candidate no longer satisfies release gates")
    payload = _payload(candidate, result)
    manifest_sha = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return CreativeReleaseManifest(
        candidate_id=candidate.candidate_id,
        media_sha256=candidate.media_sha256,
        temporal_evidence_hash=candidate.temporal.evidence_hash,
        temporal_score=round(float(candidate.temporal.score), 6),
        creative_mean_score=round(float(candidate.mean_score), 6),
        ranked_candidate_ids=result.ranked_candidate_ids,
        manifest_sha256=manifest_sha,
    )
