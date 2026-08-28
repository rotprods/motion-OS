import hashlib

import pytest

from src.qa.creative_tournament import CreativeCandidate, CreativeReview, REQUIRED_DIMENSIONS, TournamentResult, run_tournament
from src.qa.release_manifest import ReleaseManifestError, build_release_manifest
from src.qa.temporal_multimodal import build_temporal_evidence, critique_from_provider_payload, uniform_sample_indices


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def candidate(candidate_id: str, *, creative_score=9.3, temporal_score=9.4, authoritative=True, creative_run=None):
    media_sha = digest(candidate_id)
    indices = uniform_sample_indices(90, target_samples=8)
    evidence = build_temporal_evidence(
        media_sha256=media_sha,
        frame_count=90,
        fps=30,
        frame_hashes={i: digest(f"{candidate_id}:frame:{i}") for i in indices},
        provider="vision-provider",
        provider_run_id=f"run:{candidate_id}" if authoritative else None,
        provider_attested_full_video=authoritative,
        target_samples=8,
    )
    critique = critique_from_provider_payload(evidence, {
        "provider": "vision-provider",
        "authoritative": authoritative,
        "score": temporal_score,
        "dimensions": {"temporal_coherence": temporal_score},
        "defects": [],
        "recommendation": "RELEASE",
    })
    creative = CreativeReview(
        media_sha256=media_sha,
        provider="creative-vision-provider",
        provider_run_id=creative_run or f"creative:{candidate_id}",
        dimensions={key: creative_score for key in REQUIRED_DIMENSIONS},
        provider_attested_media_review=True,
    )
    return CreativeCandidate(candidate_id, media_sha, critique, creative)


def test_release_manifest_binds_both_temporal_and_creative_evidence():
    a = candidate("a")
    b = candidate("b", creative_score=9.1)
    result = run_tournament([b, a])
    manifest = build_release_manifest(result, [a, b])
    winner = a if manifest.candidate_id == "a" else b
    assert manifest.media_sha256 == winner.media_sha256
    assert manifest.temporal_evidence_hash == winner.temporal.evidence_hash
    assert manifest.creative_evidence_hash == winner.creative.content_hash()
    assert len(manifest.manifest_sha256) == 64


def test_manifest_is_deterministic_when_candidate_input_order_changes():
    a = candidate("a")
    b = candidate("b", creative_score=9.1)
    result = run_tournament([a, b])
    assert build_release_manifest(result, [a, b]) == build_release_manifest(result, [b, a])


def test_no_release_candidate_fails_closed():
    blocked = candidate("blocked", creative_score=8.0)
    with pytest.raises(ReleaseManifestError, match="no release-eligible"):
        build_release_manifest(run_tournament([blocked]), [blocked])


def test_duplicate_candidate_identity_fails_closed():
    a = candidate("a")
    with pytest.raises(ReleaseManifestError, match="duplicate candidate identity"):
        build_release_manifest(run_tournament([a]), [a, a])


def test_candidate_set_substitution_fails_closed():
    a, b = candidate("a"), candidate("b")
    with pytest.raises(ReleaseManifestError, match="deterministic recomputation"):
        build_release_manifest(run_tournament([a]), [b])


def test_candidate_set_extension_fails_closed():
    a, b, c = candidate("a", creative_score=9.6), candidate("b", creative_score=9.1), candidate("c", creative_score=9.0)
    with pytest.raises(ReleaseManifestError, match="deterministic recomputation"):
        build_release_manifest(run_tournament([a, b]), [a, b, c])


def test_tampered_release_candidate_fails_closed():
    a, b = candidate("a", creative_score=9.6), candidate("b", creative_score=9.1)
    canonical = run_tournament([a, b])
    tampered = TournamentResult(canonical.winner_id, canonical.ranked_candidate_ids, "b", canonical.blocked_candidate_ids, canonical.reasons)
    with pytest.raises(ReleaseManifestError, match="deterministic recomputation"):
        build_release_manifest(tampered, [a, b])


def test_tampered_ranking_fails_closed():
    a, b = candidate("a", creative_score=9.6), candidate("b", creative_score=9.1)
    canonical = run_tournament([a, b])
    tampered = TournamentResult(canonical.winner_id, tuple(reversed(canonical.ranked_candidate_ids)), canonical.release_candidate_id, canonical.blocked_candidate_ids, canonical.reasons)
    with pytest.raises(ReleaseManifestError, match="deterministic recomputation"):
        build_release_manifest(tampered, [a, b])


def test_manifest_hash_changes_when_temporal_evidence_changes():
    a1 = candidate("a")
    m1 = build_release_manifest(run_tournament([a1]), [a1])
    media_sha = digest("a")
    indices = uniform_sample_indices(90, target_samples=8)
    evidence2 = build_temporal_evidence(
        media_sha256=media_sha, frame_count=90, fps=30,
        frame_hashes={i: digest(f"changed:a:frame:{i}") for i in indices},
        provider="vision-provider", provider_run_id="run:a:2", provider_attested_full_video=True, target_samples=8,
    )
    critique2 = critique_from_provider_payload(evidence2, {
        "provider": "vision-provider", "authoritative": True, "score": 9.4,
        "dimensions": {"temporal_coherence": 9.4}, "defects": [], "recommendation": "RELEASE",
    })
    a2 = CreativeCandidate("a", media_sha, critique2, a1.creative)
    m2 = build_release_manifest(run_tournament([a2]), [a2])
    assert m1.temporal_evidence_hash != m2.temporal_evidence_hash
    assert m1.manifest_sha256 != m2.manifest_sha256


def test_manifest_hash_changes_when_creative_evidence_run_changes():
    a1 = candidate("a", creative_run="creative:a:1")
    a2 = candidate("a", creative_run="creative:a:2")
    m1 = build_release_manifest(run_tournament([a1]), [a1])
    m2 = build_release_manifest(run_tournament([a2]), [a2])
    assert m1.creative_evidence_hash != m2.creative_evidence_hash
    assert m1.manifest_sha256 != m2.manifest_sha256
