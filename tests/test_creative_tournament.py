import hashlib
import math

import pytest

from src.qa.creative_tournament import (
    CreativeCandidate,
    CreativeReview,
    CreativeTournamentError,
    REQUIRED_DIMENSIONS,
    creative_review_from_provider_payload,
    run_tournament,
)
from src.qa.temporal_multimodal import (
    build_temporal_evidence,
    critique_from_provider_payload,
    uniform_sample_indices,
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def dims(score: float = 9.2):
    return {key: score for key in REQUIRED_DIMENSIONS}


def temporal(*, authoritative=True, score=9.3, recommendation="RELEASE", media_sha=None):
    media_sha = media_sha or digest("video")
    indices = uniform_sample_indices(90, target_samples=8)
    run_id = "run-1" if authoritative else None
    evidence = build_temporal_evidence(
        media_sha256=media_sha,
        frame_count=90,
        fps=30,
        frame_hashes={i: digest(f"{media_sha}:frame-{i}") for i in indices},
        provider="vision-provider",
        provider_run_id=run_id,
        provider_attested_full_video=authoritative,
        target_samples=8,
    )
    payload = {
        "provider": "vision-provider",
        "authoritative": authoritative,
        "score": score,
        "dimensions": {"temporal_coherence": score},
        "defects": [],
        "recommendation": recommendation,
    }
    if run_id is not None:
        payload["provider_run_id"] = run_id
    if authoritative:
        payload.update(
            {
                "media_sha256": media_sha,
                "full_video_scope": True,
                "provider_attestation_id": "temporal-attestation-1",
            }
        )
    return critique_from_provider_payload(evidence, payload)


def creative_payload(media_sha: str, *, score=9.2, authoritative=True, **overrides):
    payload = {
        "provider": "creative-vision-provider",
        "provider_run_id": "creative-run-1",
        "media_sha256": media_sha,
        "full_video_scope": True,
        "provider_attestation_id": "creative-attestation-1",
        "authoritative": authoritative,
        "dimensions": dims(score),
    }
    payload.update(overrides)
    return payload


def creative(media_sha: str, *, score=9.2, authoritative=True):
    if authoritative:
        return creative_review_from_provider_payload(
            expected_media_sha256=media_sha,
            expected_provider="creative-vision-provider",
            expected_provider_run_id="creative-run-1",
            payload=creative_payload(media_sha, score=score),
        )
    return CreativeReview(
        media_sha256=media_sha,
        provider="fixture",
        provider_run_id=None,
        dimensions=dims(score),
        provider_attested_media_review=False,
    )


def candidate(candidate_id: str, *, creative_score=9.2, temporal_auth=True, creative_auth=True):
    media_sha = digest(candidate_id)
    return CreativeCandidate(
        candidate_id=candidate_id,
        media_sha256=media_sha,
        temporal=temporal(authoritative=temporal_auth, media_sha=media_sha),
        creative=creative(media_sha, score=creative_score, authoritative=creative_auth),
    )


def test_release_ready_candidate_wins_over_higher_non_authoritative_temporal_score():
    good = candidate("good", creative_score=9.2, temporal_auth=True)
    fake = candidate("fake", creative_score=9.9, temporal_auth=False)
    result = run_tournament([fake, good])
    assert result.winner_id == "good"
    assert result.release_candidate_id == "good"
    assert "NON_AUTHORITATIVE_TEMPORAL_CRITIC" in result.reasons["fake"]


def test_non_authoritative_creative_review_cannot_release():
    item = candidate("unbound", creative_auth=False)
    result = run_tournament([item])
    assert result.release_candidate_id is None
    assert "NON_AUTHORITATIVE_CREATIVE_REVIEW" in result.reasons["unbound"]


def test_local_creative_attestation_boolean_alone_never_creates_authority():
    review = CreativeReview(
        media_sha256=digest("local-bool-spoof"),
        provider="creative-vision-provider",
        provider_run_id="creative-run-1",
        dimensions=dims(9.9),
        provider_attested_media_review=True,
    )
    assert review.provider_attested_media_review is True
    assert review.authoritative_evidence is False


def test_valid_creative_provider_payload_binds_exact_candidate():
    media_sha = digest("bound-candidate")
    review = creative_review_from_provider_payload(
        expected_media_sha256=media_sha,
        expected_provider="creative-vision-provider",
        expected_provider_run_id="creative-run-1",
        payload=creative_payload(media_sha),
    )
    assert review.authoritative_evidence is True
    assert review.provider_attestation_id == "creative-attestation-1"
    assert review.full_video_scope is True
    assert review.media_sha256 == media_sha


def test_creative_provider_payload_wrong_media_sha_fails_closed():
    expected = digest("candidate-a")
    with pytest.raises(CreativeTournamentError, match="media_sha256 does not match"):
        creative_review_from_provider_payload(
            expected_media_sha256=expected,
            expected_provider="creative-vision-provider",
            expected_provider_run_id="creative-run-1",
            payload=creative_payload(digest("candidate-b")),
        )


def test_creative_provider_payload_wrong_provider_fails_closed():
    media_sha = digest("candidate")
    with pytest.raises(CreativeTournamentError, match="provider identity"):
        creative_review_from_provider_payload(
            expected_media_sha256=media_sha,
            expected_provider="creative-vision-provider",
            expected_provider_run_id="creative-run-1",
            payload=creative_payload(media_sha, provider="other-provider"),
        )


def test_creative_provider_payload_wrong_run_id_fails_closed():
    media_sha = digest("candidate")
    with pytest.raises(CreativeTournamentError, match="provider_run_id"):
        creative_review_from_provider_payload(
            expected_media_sha256=media_sha,
            expected_provider="creative-vision-provider",
            expected_provider_run_id="creative-run-1",
            payload=creative_payload(media_sha, provider_run_id="other-run"),
        )


def test_creative_provider_payload_missing_attestation_id_fails_closed():
    media_sha = digest("candidate")
    payload = creative_payload(media_sha)
    payload.pop("provider_attestation_id")
    with pytest.raises(CreativeTournamentError, match="provider_attestation_id"):
        creative_review_from_provider_payload(
            expected_media_sha256=media_sha,
            expected_provider="creative-vision-provider",
            expected_provider_run_id="creative-run-1",
            payload=payload,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authoritative", "true"),
        ("full_video_scope", "true"),
        ("authoritative", 1),
        ("full_video_scope", 1),
    ],
)
def test_creative_truthy_boolean_spoofs_are_rejected(field, value):
    media_sha = digest("candidate")
    payload = creative_payload(media_sha, **{field: value})
    with pytest.raises(CreativeTournamentError, match="literal boolean"):
        creative_review_from_provider_payload(
            expected_media_sha256=media_sha,
            expected_provider="creative-vision-provider",
            expected_provider_run_id="creative-run-1",
            payload=payload,
        )


@pytest.mark.parametrize("value", [True, "9.2", math.nan, math.inf])
def test_creative_dimension_scalars_fail_closed(value):
    media_sha = digest("candidate")
    scores = dims(9.2)
    scores["composition"] = value
    payload = creative_payload(media_sha, dimensions=scores)
    expected = "finite" if isinstance(value, float) and not math.isfinite(value) else "numeric scalar"
    with pytest.raises(CreativeTournamentError, match=expected):
        creative_review_from_provider_payload(
            expected_media_sha256=media_sha,
            expected_provider="creative-vision-provider",
            expected_provider_run_id="creative-run-1",
            payload=payload,
        )


def test_creative_same_run_cross_media_replay_is_rejected():
    original_sha = digest("candidate-original")
    other_sha = digest("candidate-other")
    replay = creative_payload(original_sha)
    with pytest.raises(CreativeTournamentError, match="media_sha256 does not match"):
        creative_review_from_provider_payload(
            expected_media_sha256=other_sha,
            expected_provider="creative-vision-provider",
            expected_provider_run_id="creative-run-1",
            payload=replay,
        )


def test_mean_above_nine_still_fails_when_hard_dimension_is_below_threshold():
    media_sha = digest("weak-type")
    scores = dims(9.5)
    scores["typography"] = 8.9
    review = creative_review_from_provider_payload(
        expected_media_sha256=media_sha,
        expected_provider="creative-vision-provider",
        expected_provider_run_id="creative-run-1",
        payload=creative_payload(media_sha, dimensions=scores),
    )
    item = CreativeCandidate("weak-type", media_sha, temporal(media_sha=media_sha), review)
    assert item.mean_score > 9.0
    assert item.release_ready is False
    assert "CREATIVE_THRESHOLD_FAILURE" in run_tournament([item]).reasons[item.candidate_id]


def test_creative_mean_below_nine_blocks_release():
    item = candidate("below-nine", creative_score=8.99)
    result = run_tournament([item])
    assert result.release_candidate_id is None
    assert "CREATIVE_MEAN_BELOW_9" in result.reasons[item.candidate_id]


def test_duplicate_candidate_ids_fail_closed():
    with pytest.raises(CreativeTournamentError, match="unique"):
        run_tournament([candidate("same"), candidate("same")])


def test_empty_tournament_fails_closed():
    with pytest.raises(CreativeTournamentError, match="at least one"):
        run_tournament([])


def test_missing_dimension_fails_closed():
    scores = dims()
    scores.pop("typography")
    with pytest.raises(CreativeTournamentError, match="missing creative dimensions"):
        CreativeReview(digest("bad"), "provider", "run", scores, True)


def test_unknown_dimension_fails_closed():
    scores = dims()
    scores["invented"] = 9.9
    with pytest.raises(CreativeTournamentError, match="unknown creative dimensions"):
        CreativeReview(digest("bad"), "provider", "run", scores, True)


def test_out_of_range_dimension_fails_closed():
    scores = dims()
    scores["composition"] = 10.1
    with pytest.raises(CreativeTournamentError, match=r"\[0, 10\]"):
        CreativeReview(digest("bad"), "provider", "run", scores, True)


def test_ranking_is_deterministic_for_same_inputs():
    items = [candidate("c"), candidate("a"), candidate("b")]
    first = run_tournament(items)
    second = run_tournament(reversed(items))
    assert first.ranked_candidate_ids == second.ranked_candidate_ids
    assert first.release_candidate_id == second.release_candidate_id


def test_temporal_iterate_blocks_release_even_with_good_creative_scores():
    media_sha = digest("temporal-iterate")
    item = CreativeCandidate(
        "temporal-iterate",
        media_sha,
        temporal(recommendation="ITERATE", media_sha=media_sha),
        creative(media_sha, score=9.5),
    )
    result = run_tournament([item])
    assert result.release_candidate_id is None
    assert "TEMPORAL_RELEASE_GATE_FAILED" in result.reasons[item.candidate_id]


def test_temporal_critique_from_other_media_is_rejected():
    media_sha = digest("candidate-b")
    with pytest.raises(CreativeTournamentError, match="must match temporal critique"):
        CreativeCandidate(
            "candidate-b",
            media_sha,
            temporal(media_sha=digest("candidate-a")),
            creative(media_sha),
        )


def test_creative_review_from_other_media_is_rejected():
    media_sha = digest("candidate-b")
    with pytest.raises(CreativeTournamentError, match="must match creative review"):
        CreativeCandidate(
            "candidate-b",
            media_sha,
            temporal(media_sha=media_sha),
            creative(digest("candidate-a")),
        )


def test_creative_review_hash_changes_with_scores_or_provider_run():
    media_sha = digest("x")
    a = creative(media_sha, score=9.2)
    b = creative_review_from_provider_payload(
        expected_media_sha256=media_sha,
        expected_provider="creative-vision-provider",
        expected_provider_run_id="creative-run-2",
        payload=creative_payload(media_sha, provider_run_id="creative-run-2"),
    )
    c = creative(media_sha, score=9.3)
    assert a.content_hash() != b.content_hash()
    assert a.content_hash() != c.content_hash()
