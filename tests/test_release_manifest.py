import hashlib

import pytest

from src.qa.creative_tournament import CreativeCandidate, REQUIRED_DIMENSIONS, TournamentResult, run_tournament
from src.qa.release_manifest import ReleaseManifestError, build_release_manifest
from src.qa.temporal_multimodal import build_temporal_evidence, critique_from_provider_payload, uniform_sample_indices


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def candidate(candidate_id: str, *, creative_score=9.3, temporal_score=9.4, authoritative=True):
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
    return CreativeCandidate(
        candidate_id=candidate_id,
        media_sha256=media_sha,
        temporal=critique,
        dimensions={key: creative_score for key in REQUIRED_DIMENSIONS},
        evidence_bound=True,
    )


def test_release_manifest_binds_candidate_media_and_temporal_evidence():
    a = candidate("a")
    b = candidate("b", creative_score=9.1)
    result = run_tournament([b, a])
    manifest = build_release_manifest(result, [a, b])
    assert manifest.candidate_id == result.release_candidate_id
    winner = a if manifest.candidate_id == "a" else b
    assert manifest.media_sha256 == winner.media_sha256
    assert manifest.temporal_evidence_hash == winner.temporal.evidence_hash
    assert len(manifest.manifest_sha256) == 64


def test_manifest_is_deterministic_when_candidate_input_order_changes():
    a = candidate("a")
    b = candidate("b", creative_score=9.1)
    result = run_tournament([a, b])
    first = build_release_manifest(result, [a, b])
    second = build_release_manifest(result, [b, a])
    assert first == second


def test_no_release_candidate_fails_closed():
    blocked = candidate("blocked", creative_score=8.0)
    result = run_tournament([blocked])
    with pytest.raises(ReleaseManifestError, match="no release-eligible"):
        build_release_manifest(result, [blocked])


def test_duplicate_candidate_identity_fails_closed():
    a = candidate("a")
    result = run_tournament([a])
    with pytest.raises(ReleaseManifestError, match="duplicate candidate identity"):
        build_release_manifest(result, [a, a])


def test_candidate_set_substitution_fails_closed():
    a = candidate("a")
    b = candidate("b")
    result = run_tournament([a])
    with pytest.raises(ReleaseManifestError, match="deterministic recomputation"):
        build_release_manifest(result, [b])


def test_candidate_set_extension_fails_closed():
    a = candidate("a", creative_score=9.6)
    b = candidate("b", creative_score=9.1)
    c = candidate("c", creative_score=9.0)
    result = run_tournament([a, b])
    with pytest.raises(ReleaseManifestError, match="deterministic recomputation"):
        build_release_manifest(result, [a, b, c])


def test_tampered_release_candidate_fails_closed():
    a = candidate("a", creative_score=9.6)
    b = candidate("b", creative_score=9.1)
    canonical = run_tournament([a, b])
    tampered = TournamentResult(
        winner_id=canonical.winner_id,
        ranked_candidate_ids=canonical.ranked_candidate_ids,
        release_candidate_id="b" if canonical.release_candidate_id == "a" else "a",
        blocked_candidate_ids=canonical.blocked_candidate_ids,
        reasons=canonical.reasons,
    )
    with pytest.raises(ReleaseManifestError, match="deterministic recomputation"):
        build_release_manifest(tampered, [a, b])


def test_tampered_ranking_fails_closed():
    a = candidate("a", creative_score=9.6)
    b = candidate("b", creative_score=9.1)
    canonical = run_tournament([a, b])
    tampered = TournamentResult(
        winner_id=canonical.winner_id,
        ranked_candidate_ids=tuple(reversed(canonical.ranked_candidate_ids)),
        release_candidate_id=canonical.release_candidate_id,
        blocked_candidate_ids=canonical.blocked_candidate_ids,
        reasons=canonical.reasons,
    )
    with pytest.raises(ReleaseManifestError, match="deterministic recomputation"):
        build_release_manifest(tampered, [a, b])


def test_manifest_hash_changes_when_temporal_evidence_changes():
    a1 = candidate("a")
    result1 = run_tournament([a1])
    m1 = build_release_manifest(result1, [a1])

    media_sha = digest("a")
    indices = uniform_sample_indices(90, target_samples=8)
    evidence2 = build_temporal_evidence(
        media_sha256=media_sha,
        frame_count=90,
        fps=30,
        frame_hashes={i: digest(f"changed:a:frame:{i}") for i in indices},
        provider="vision-provider",
        provider_run_id="run:a:2",
        provider_attested_full_video=True,
        target_samples=8,
    )
    critique2 = critique_from_provider_payload(evidence2, {
        "provider": "vision-provider",
        "authoritative": True,
        "score": 9.4,
        "dimensions": {"temporal_coherence": 9.4},
        "defects": [],
        "recommendation": "RELEASE",
    })
    a2 = CreativeCandidate(
        candidate_id="a",
        media_sha256=media_sha,
        temporal=critique2,
        dimensions={key: 9.3 for key in REQUIRED_DIMENSIONS},
        evidence_bound=True,
    )
    result2 = run_tournament([a2])
    m2 = build_release_manifest(result2, [a2])
    assert m1.temporal_evidence_hash != m2.temporal_evidence_hash
    assert m1.manifest_sha256 != m2.manifest_sha256
