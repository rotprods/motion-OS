import hashlib

import pytest

from src.qa.creative_tournament import CreativeCandidate, CreativeTournamentError, REQUIRED_DIMENSIONS, run_tournament
from src.qa.temporal_multimodal import build_temporal_evidence, critique_from_provider_payload, uniform_sample_indices


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def dims(score: float = 9.2):
    return {key: score for key in REQUIRED_DIMENSIONS}


def temporal(*, authoritative=True, score=9.3, recommendation="RELEASE", media_sha=None):
    media_sha = media_sha or digest("video")
    indices = uniform_sample_indices(90, target_samples=8)
    evidence = build_temporal_evidence(
        media_sha256=media_sha,
        frame_count=90,
        fps=30,
        frame_hashes={i: digest(f"{media_sha}:frame-{i}") for i in indices},
        provider="vision-provider",
        provider_run_id="run-1" if authoritative else None,
        provider_attested_full_video=authoritative,
        target_samples=8,
    )
    return critique_from_provider_payload(evidence, {
        "provider": "vision-provider",
        "authoritative": authoritative,
        "score": score,
        "dimensions": {"temporal_coherence": score},
        "defects": [],
        "recommendation": recommendation,
    })


def candidate(candidate_id: str, *, creative_score=9.2, temporal_auth=True, evidence_bound=True):
    media_sha = digest(candidate_id)
    return CreativeCandidate(
        candidate_id=candidate_id,
        media_sha256=media_sha,
        temporal=temporal(authoritative=temporal_auth, media_sha=media_sha),
        dimensions=dims(creative_score),
        evidence_bound=evidence_bound,
    )


def test_release_ready_candidate_wins_over_higher_non_authoritative_score():
    good = candidate("good", creative_score=9.2, temporal_auth=True)
    fake = candidate("fake", creative_score=9.9, temporal_auth=False)
    result = run_tournament([fake, good])
    assert result.winner_id == "good"
    assert result.release_candidate_id == "good"
    assert "fake" in result.blocked_candidate_ids
    assert "NON_AUTHORITATIVE_TEMPORAL_CRITIC" in result.reasons["fake"]


def test_unbound_creative_evidence_cannot_release():
    item = candidate("unbound", evidence_bound=False)
    result = run_tournament([item])
    assert result.release_candidate_id is None
    assert "UNBOUND_CREATIVE_EVIDENCE" in result.reasons["unbound"]


def test_mean_above_nine_still_fails_when_hard_dimension_is_below_threshold():
    scores = dims(9.5)
    scores["typography"] = 8.9
    media_sha = digest("weak-type")
    item = CreativeCandidate("weak-type", media_sha, temporal(media_sha=media_sha), scores, True)
    assert item.mean_score > 9.0
    assert item.release_ready is False
    result = run_tournament([item])
    assert "CREATIVE_THRESHOLD_FAILURE" in result.reasons[item.candidate_id]


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
    media_sha = digest("bad")
    with pytest.raises(CreativeTournamentError, match="missing creative dimensions"):
        CreativeCandidate("bad", media_sha, temporal(media_sha=media_sha), scores, True)


def test_out_of_range_dimension_fails_closed():
    scores = dims()
    scores["composition"] = 10.1
    media_sha = digest("bad")
    with pytest.raises(CreativeTournamentError, match="\[0, 10\]"):
        CreativeCandidate("bad", media_sha, temporal(media_sha=media_sha), scores, True)


def test_ranking_is_deterministic_for_same_inputs():
    items = [candidate("c"), candidate("a"), candidate("b")]
    first = run_tournament(items)
    second = run_tournament(reversed(items))
    assert first.ranked_candidate_ids == second.ranked_candidate_ids
    assert first.release_candidate_id == second.release_candidate_id


def test_temporal_iterate_blocks_release_even_with_good_creative_scores():
    media_sha = digest("temporal-iterate")
    item = CreativeCandidate(
        "temporal-iterate", media_sha, temporal(recommendation="ITERATE", media_sha=media_sha), dims(9.5), True
    )
    result = run_tournament([item])
    assert result.release_candidate_id is None
    assert "TEMPORAL_RELEASE_GATE_FAILED" in result.reasons[item.candidate_id]


def test_temporal_critique_from_other_media_is_rejected():
    with pytest.raises(CreativeTournamentError, match="must match temporal critique"):
        CreativeCandidate(
            "candidate-b",
            digest("candidate-b"),
            temporal(media_sha=digest("candidate-a")),
            dims(9.5),
            True,
        )
