import hashlib

import pytest

from src.qa.creative_tournament import CreativeCandidate, CreativeReview, CreativeTournamentError, REQUIRED_DIMENSIONS, run_tournament
from src.qa.temporal_multimodal import build_temporal_evidence, critique_from_provider_payload, uniform_sample_indices


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
    return critique_from_provider_payload(evidence, {
        "provider": "vision-provider",
        "provider_run_id": run_id,
        "authoritative": authoritative,
        "score": score,
        "dimensions": {"temporal_coherence": score},
        "defects": [],
        "recommendation": recommendation,
    })


def creative(media_sha: str, *, score=9.2, authoritative=True):
    return CreativeReview(
        media_sha256=media_sha,
        provider="creative-vision-provider" if authoritative else "fixture",
        provider_run_id="creative-run-1" if authoritative else None,
        dimensions=dims(score),
        provider_attested_media_review=authoritative,
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


def test_mean_above_nine_still_fails_when_hard_dimension_is_below_threshold():
    media_sha = digest("weak-type")
    scores = dims(9.5)
    scores["typography"] = 8.9
    review = CreativeReview(media_sha, "creative-vision-provider", "run", scores, True)
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
    scores = dims(); scores.pop("typography")
    with pytest.raises(CreativeTournamentError, match="missing creative dimensions"):
        CreativeReview(digest("bad"), "provider", "run", scores, True)


def test_unknown_dimension_fails_closed():
    scores = dims(); scores["invented"] = 9.9
    with pytest.raises(CreativeTournamentError, match="unknown creative dimensions"):
        CreativeReview(digest("bad"), "provider", "run", scores, True)


def test_out_of_range_dimension_fails_closed():
    scores = dims(); scores["composition"] = 10.1
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
        "temporal-iterate", media_sha, temporal(recommendation="ITERATE", media_sha=media_sha), creative(media_sha, score=9.5)
    )
    result = run_tournament([item])
    assert result.release_candidate_id is None
    assert "TEMPORAL_RELEASE_GATE_FAILED" in result.reasons[item.candidate_id]


def test_temporal_critique_from_other_media_is_rejected():
    media_sha = digest("candidate-b")
    with pytest.raises(CreativeTournamentError, match="must match temporal critique"):
        CreativeCandidate("candidate-b", media_sha, temporal(media_sha=digest("candidate-a")), creative(media_sha))


def test_creative_review_from_other_media_is_rejected():
    media_sha = digest("candidate-b")
    with pytest.raises(CreativeTournamentError, match="must match creative review"):
        CreativeCandidate("candidate-b", media_sha, temporal(media_sha=media_sha), creative(digest("candidate-a")))


def test_creative_review_hash_changes_with_scores_or_provider_run():
    media_sha = digest("x")
    a = creative(media_sha, score=9.2)
    b = CreativeReview(media_sha, "creative-vision-provider", "creative-run-2", dims(9.2), True)
    c = creative(media_sha, score=9.3)
    assert a.content_hash() != b.content_hash()
    assert a.content_hash() != c.content_hash()
