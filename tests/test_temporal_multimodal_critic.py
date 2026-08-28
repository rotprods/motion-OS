import hashlib

import pytest

from src.qa.temporal_multimodal import (
    FullVideoEvidence,
    TemporalEvidenceError,
    TemporalSample,
    build_temporal_evidence,
    critique_from_provider_payload,
    release_eligible,
    uniform_sample_indices,
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def hashes(indices):
    return {index: digest(f"frame-{index}") for index in indices}


def evidence(*, attested=True, run_id="run-1", provider="vision-provider"):
    frame_count = 90
    indices = uniform_sample_indices(frame_count, target_samples=8)
    return build_temporal_evidence(
        media_sha256=digest("video"),
        frame_count=frame_count,
        fps=30,
        frame_hashes=hashes(indices),
        provider=provider,
        provider_run_id=run_id,
        provider_attested_full_video=attested,
        target_samples=8,
    )


def test_uniform_sampling_binds_boundaries_and_is_deterministic():
    a = uniform_sample_indices(90, target_samples=8)
    b = uniform_sample_indices(90, target_samples=8)
    assert a == b
    assert a[0] == 0
    assert a[-1] == 89
    assert len(a) == 8


def test_short_video_samples_every_frame():
    assert uniform_sample_indices(4, target_samples=8) == (0, 1, 2, 3)


def test_missing_required_frame_hash_fails_closed():
    indices = uniform_sample_indices(90, target_samples=8)
    with pytest.raises(TemporalEvidenceError, match="missing required"):
        build_temporal_evidence(
            media_sha256=digest("video"), frame_count=90, fps=30,
            frame_hashes=hashes(indices[:-1]), target_samples=8,
        )


def test_duration_disagreement_fails_closed():
    with pytest.raises(TemporalEvidenceError, match="duration"):
        FullVideoEvidence(
            media_sha256=digest("video"), frame_count=90, fps=30, duration_ms=5000,
            samples=(TemporalSample(0, 0, digest("0")), TemporalSample(89, 2967, digest("89"))),
        )


def test_unattested_provider_cannot_become_authoritative_or_release():
    ev = evidence(attested=False)
    critique = critique_from_provider_payload(ev, {
        "provider": "vision-provider", "authoritative": True, "score": 9.8,
        "dimensions": {"temporal_coherence": 9.8}, "defects": [], "recommendation": "RELEASE",
    })
    assert critique.authoritative is False
    assert critique.recommendation == "BLOCK"
    assert release_eligible(critique) is False


def test_missing_provider_run_id_cannot_be_authoritative():
    ev = evidence(run_id=None)
    critique = critique_from_provider_payload(ev, {
        "provider": "vision-provider", "authoritative": True, "score": 9.8,
        "defects": [], "recommendation": "RELEASE",
    })
    assert critique.authoritative is False
    assert release_eligible(critique) is False


def test_provider_identity_mismatch_cannot_be_authoritative():
    ev = evidence(provider="provider-a")
    critique = critique_from_provider_payload(ev, {
        "provider": "provider-b", "authoritative": True, "score": 9.8,
        "defects": [], "recommendation": "RELEASE",
    })
    assert critique.authoritative is False
    assert release_eligible(critique) is False


def test_p1_defect_forces_release_block_even_with_high_score():
    ev = evidence()
    frame = ev.samples[2].frame_index
    critique = critique_from_provider_payload(ev, {
        "provider": ev.provider, "authoritative": True, "score": 9.7,
        "dimensions": {"motion_choreography": 9.7},
        "defects": [{
            "code": "TEMPORAL_POP", "severity": "P1", "start_ms": 500, "end_ms": 700,
            "evidence_frame_indices": [frame], "description": "abrupt visual discontinuity",
        }],
        "recommendation": "RELEASE",
    })
    assert critique.authoritative is True
    assert critique.recommendation == "BLOCK"
    assert release_eligible(critique) is False


def test_defect_cannot_reference_unbound_frame():
    ev = evidence()
    unsampled = next(index for index in range(ev.frame_count) if index not in {s.frame_index for s in ev.samples})
    with pytest.raises(TemporalEvidenceError, match="outside bound evidence"):
        critique_from_provider_payload(ev, {
            "provider": ev.provider, "authoritative": True, "score": 8.0,
            "defects": [{
                "code": "GHOST", "severity": "P2", "start_ms": 100, "end_ms": 200,
                "evidence_frame_indices": [unsampled],
            }],
        })


def test_evidence_hash_changes_when_sample_evidence_changes():
    ev1 = evidence()
    indices = uniform_sample_indices(90, target_samples=8)
    changed = hashes(indices)
    changed[indices[3]] = digest("mutated-frame")
    ev2 = build_temporal_evidence(
        media_sha256=digest("video"), frame_count=90, fps=30, frame_hashes=changed,
        provider="vision-provider", provider_run_id="run-1", provider_attested_full_video=True,
        target_samples=8,
    )
    assert ev1.content_hash() != ev2.content_hash()


def test_authoritative_clean_high_score_can_release():
    ev = evidence()
    critique = critique_from_provider_payload(ev, {
        "provider": ev.provider, "authoritative": True, "score": 9.3,
        "dimensions": {"temporal_coherence": 9.4, "motion_choreography": 9.2},
        "defects": [], "recommendation": "RELEASE",
    })
    assert critique.authoritative is True
    assert critique.evidence_hash == ev.content_hash()
    assert release_eligible(critique) is True


def test_score_outside_range_fails_closed():
    ev = evidence()
    with pytest.raises(TemporalEvidenceError, match="scores"):
        critique_from_provider_payload(ev, {"provider": ev.provider, "score": 10.1})
