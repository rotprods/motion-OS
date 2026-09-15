import hashlib

import pytest

from src.qa.creative_tournament import (
    CreativeCandidate,
    REQUIRED_DIMENSIONS,
    TournamentResult,
    creative_review_from_provider_payload,
    run_tournament,
)
from src.qa.release_manifest import ReleaseManifestError, build_release_manifest
from src.qa.temporal_multimodal import (
    build_temporal_evidence,
    critique_from_provider_payload,
    uniform_sample_indices,
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def candidate(
    candidate_id: str,
    *,
    creative_score=9.3,
    temporal_score=9.4,
    authoritative=True,
    creative_run=None,
):
    media_sha = digest(candidate_id)
    indices = uniform_sample_indices(90, target_samples=8)
    temporal_run = f"run:{candidate_id}" if authoritative else None
    evidence = build_temporal_evidence(
        media_sha256=media_sha,
        frame_count=90,
        fps=30,
        frame_hashes={i: digest(f"{candidate_id}:frame:{i}") for i in indices},
        provider="vision-provider",
        provider_run_id=temporal_run,
        provider_attested_full_video=authoritative,
        target_samples=8,
    )
    temporal_payload = {
        "provider": "vision-provider",
        "authoritative": authoritative,
        "score": temporal_score,
        "dimensions": {"temporal_coherence": temporal_score},
        "defects": [],
        "recommendation": "RELEASE",
    }
    if authoritative:
        temporal_payload.update(
            {
                "provider_run_id": temporal_run,
                "media_sha256": media_sha,
                "full_video_scope": True,
                "provider_attestation_id": f"temporal-attestation:{candidate_id}",
            }
        )
    critique = critique_from_provider_payload(evidence, temporal_payload)

    creative_run_id = creative_run or f"creative:{candidate_id}"
    creative_payload = {
        "provider": "creative-vision-provider",
        "provider_run_id": creative_run_id,
        "media_sha256": media_sha,
        "full_video_scope": True,
        "provider_attestation_id": f"creative-attestation:{candidate_id}:{creative_run_id}",
        "authoritative": True,
        "dimensions": {key: creative_score for key in REQUIRED_DIMENSIONS},
    }
    creative = creative_review_from_provider_payload(
        expected_media_sha256=media_sha,
        expected_provider="creative-vision-provider",
        expected_provider_run_id=creative_run_id,
        payload=creative_payload,
    )
    return CreativeCandidate(candidate_id, media_sha, critique, creative)


def test_release_manifest_binds_temporal_and_creative_attestation_authority():
    a = candidate("a")
    b = candidate("b", creative_score=9.1)
    result = run_tournament([b, a])
    manifest = build_release_manifest(result, [a, b])
    winner = a if manifest.candidate_id == "a" else b
    assert manifest.media_sha256 == winner.media_sha256
    assert manifest.temporal_evidence_hash == winner.temporal.evidence_hash
    assert manifest.temporal_provider == winner.temporal.provider
    assert manifest.temporal_provider_run_id == winner.temporal.provider_run_id
    assert manifest.temporal_provider_attestation_id == winner.temporal.provider_attestation_id
    assert manifest.temporal_full_video_scope is True
    assert manifest.creative_evidence_hash == winner.creative.content_hash()
    assert manifest.creative_provider == winner.creative.provider
    assert manifest.creative_provider_run_id == winner.creative.provider_run_id
    assert manifest.creative_provider_attestation_id == winner.creative.provider_attestation_id
    assert manifest.creative_full_video_scope is True
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
    a = candidate("a", creative_score=9.6)
    b = candidate("b", creative_score=9.1)
    c = candidate("c", creative_score=9.0)
    with pytest.raises(ReleaseManifestError, match="deterministic recomputation"):
        build_release_manifest(run_tournament([a, b]), [a, b, c])


def test_tampered_release_candidate_fails_closed():
    a = candidate("a", creative_score=9.6)
    b = candidate("b", creative_score=9.1)
    canonical = run_tournament([a, b])
    tampered = TournamentResult(
        canonical.winner_id,
        canonical.ranked_candidate_ids,
        "b",
        canonical.blocked_candidate_ids,
        canonical.reasons,
    )
    with pytest.raises(ReleaseManifestError, match="deterministic recomputation"):
        build_release_manifest(tampered, [a, b])


def test_tampered_ranking_fails_closed():
    a = candidate("a", creative_score=9.6)
    b = candidate("b", creative_score=9.1)
    canonical = run_tournament([a, b])
    tampered = TournamentResult(
        canonical.winner_id,
        tuple(reversed(canonical.ranked_candidate_ids)),
        canonical.release_candidate_id,
        canonical.blocked_candidate_ids,
        canonical.reasons,
    )
    with pytest.raises(ReleaseManifestError, match="deterministic recomputation"):
        build_release_manifest(tampered, [a, b])


def test_manifest_hash_changes_when_temporal_evidence_or_run_changes():
    a1 = candidate("a")
    m1 = build_release_manifest(run_tournament([a1]), [a1])
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
    critique2 = critique_from_provider_payload(
        evidence2,
        {
            "provider": "vision-provider",
            "provider_run_id": "run:a:2",
            "media_sha256": media_sha,
            "full_video_scope": True,
            "provider_attestation_id": "temporal-attestation:a:2",
            "authoritative": True,
            "score": 9.4,
            "dimensions": {"temporal_coherence": 9.4},
            "defects": [],
            "recommendation": "RELEASE",
        },
    )
    a2 = CreativeCandidate("a", media_sha, critique2, a1.creative)
    m2 = build_release_manifest(run_tournament([a2]), [a2])
    assert m1.temporal_evidence_hash != m2.temporal_evidence_hash
    assert m1.temporal_provider_run_id != m2.temporal_provider_run_id
    assert m1.temporal_provider_attestation_id != m2.temporal_provider_attestation_id
    assert m1.manifest_sha256 != m2.manifest_sha256


def test_manifest_hash_changes_when_creative_evidence_run_changes():
    a1 = candidate("a", creative_run="creative:a:1")
    a2 = candidate("a", creative_run="creative:a:2")
    m1 = build_release_manifest(run_tournament([a1]), [a1])
    m2 = build_release_manifest(run_tournament([a2]), [a2])
    assert m1.creative_evidence_hash != m2.creative_evidence_hash
    assert m1.creative_provider_run_id != m2.creative_provider_run_id
    assert m1.creative_provider_attestation_id != m2.creative_provider_attestation_id
    assert m1.manifest_sha256 != m2.manifest_sha256
