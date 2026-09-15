import hashlib
import math

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


def evidence(*, attested=True, run_id="run-1", provider="vision-provider", media_text="video"):
    frame_count = 90
    indices = uniform_sample_indices(frame_count, target_samples=8)
    return build_temporal_evidence(
        media_sha256=digest(media_text),
        frame_count=frame_count,
        fps=30,
        frame_hashes=hashes(indices),
        provider=provider,
        provider_run_id=run_id,
        provider_attested_full_video=attested,
        target_samples=8,
    )


def authoritative_payload(ev, **overrides):
    payload = {
        "provider": ev.provider,
        "provider_run_id": ev.provider_run_id,
        "media_sha256": ev.media_sha256,
        "full_video_scope": True,
        "provider_attestation_id": "attestation-1",
        "authoritative": True,
        "score": 9.3,
        "dimensions": {},
        "defects": [],
        "recommendation": "RELEASE",
    }
    payload.update(overrides)
    return payload


def test_uniform_sampling_binds_boundaries_and_is_deterministic():
    a = uniform_sample_indices(90, target_samples=8)
    b = uniform_sample_indices(90, target_samples=8)
    assert a == b
    assert a[0] == 0 and a[-1] == 89 and len(a) == 8


def test_short_video_samples_every_frame():
    assert uniform_sample_indices(4, target_samples=8) == (0, 1, 2, 3)


def test_missing_required_frame_hash_fails_closed():
    indices = uniform_sample_indices(90, target_samples=8)
    with pytest.raises(TemporalEvidenceError, match="missing required"):
        build_temporal_evidence(
            media_sha256=digest("video"),
            frame_count=90,
            fps=30,
            frame_hashes=hashes(indices[:-1]),
            target_samples=8,
        )


def test_duration_disagreement_fails_closed():
    with pytest.raises(TemporalEvidenceError, match="duration"):
        FullVideoEvidence(
            media_sha256=digest("video"),
            frame_count=90,
            fps=30,
            duration_ms=5000,
            samples=(
                TemporalSample(0, 0, digest("0")),
                TemporalSample(89, 2967, digest("89")),
            ),
        )


def test_sample_timestamp_must_match_decoded_frame_clock():
    with pytest.raises(TemporalEvidenceError, match="decoded frame clock"):
        FullVideoEvidence(
            media_sha256=digest("video"),
            frame_count=3,
            fps=30,
            duration_ms=100,
            samples=(
                TemporalSample(0, 0, digest("0")),
                TemporalSample(2, 99, digest("2")),
            ),
        )


def test_local_attestation_boolean_is_never_external_provider_authority():
    ev = evidence(attested=True)
    assert ev.provider_attested_full_video is True
    assert ev.authoritative_provider_evidence is False

    legacy_self_attested_payload = {
        "provider": ev.provider,
        "provider_run_id": ev.provider_run_id,
        "authoritative": True,
        "score": 9.8,
        "dimensions": {},
        "defects": [],
        "recommendation": "RELEASE",
    }
    with pytest.raises(TemporalEvidenceError, match="missing required fields"):
        critique_from_provider_payload(ev, legacy_self_attested_payload)


def test_valid_external_attestation_can_be_authoritative_even_when_local_boolean_is_false():
    ev = evidence(attested=False)
    critique = critique_from_provider_payload(ev, authoritative_payload(ev))
    assert critique.authoritative is True
    assert critique.provider_attestation_id == "attestation-1"
    assert critique.full_video_scope is True
    assert release_eligible(critique) is True


def test_missing_prepared_provider_run_id_cannot_be_authoritative():
    ev = evidence(run_id=None)
    payload = authoritative_payload(ev)
    payload["provider_run_id"] = "external-run"
    with pytest.raises(TemporalEvidenceError, match="locally prepared provider"):
        critique_from_provider_payload(ev, payload)


def test_provider_identity_mismatch_fails_closed_for_bound_evidence():
    ev = evidence(provider="provider-a")
    with pytest.raises(TemporalEvidenceError, match="provider identity"):
        critique_from_provider_payload(
            ev,
            authoritative_payload(ev, provider="provider-b"),
        )


def test_provider_run_id_mismatch_fails_closed():
    ev = evidence(run_id="run-authoritative")
    with pytest.raises(TemporalEvidenceError, match="provider_run_id"):
        critique_from_provider_payload(
            ev,
            authoritative_payload(ev, provider_run_id="other-run"),
        )


def test_provider_run_id_missing_fails_closed_for_authority():
    ev = evidence()
    payload = authoritative_payload(ev)
    payload.pop("provider_run_id")
    with pytest.raises(TemporalEvidenceError, match="missing required fields"):
        critique_from_provider_payload(ev, payload)


def test_media_sha_missing_fails_closed_for_authority():
    ev = evidence()
    payload = authoritative_payload(ev)
    payload.pop("media_sha256")
    with pytest.raises(TemporalEvidenceError, match="media_sha256"):
        critique_from_provider_payload(ev, payload)


def test_wrong_media_sha_fails_closed():
    ev = evidence()
    with pytest.raises(TemporalEvidenceError, match="media_sha256 does not match"):
        critique_from_provider_payload(
            ev,
            authoritative_payload(ev, media_sha256=digest("different-video")),
        )


def test_full_video_scope_must_be_literal_true_for_authority():
    ev = evidence()
    with pytest.raises(TemporalEvidenceError, match="full_video_scope"):
        critique_from_provider_payload(
            ev,
            authoritative_payload(ev, full_video_scope=False),
        )


def test_provider_attestation_identity_required_for_authority():
    ev = evidence()
    payload = authoritative_payload(ev)
    payload.pop("provider_attestation_id")
    with pytest.raises(TemporalEvidenceError, match="provider_attestation_id"):
        critique_from_provider_payload(ev, payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authoritative", "true"),
        ("full_video_scope", "true"),
        ("authoritative", 1),
        ("full_video_scope", 1),
    ],
)
def test_truthy_or_numeric_boolean_spoofs_are_rejected(field, value):
    ev = evidence()
    payload = authoritative_payload(ev)
    payload[field] = value
    with pytest.raises(TemporalEvidenceError, match="literal boolean"):
        critique_from_provider_payload(ev, payload)


@pytest.mark.parametrize("value", [True, False, "9.5", None])
def test_score_rejects_bool_and_coercible_non_numeric_scalars(value):
    ev = evidence()
    payload = authoritative_payload(ev, score=value)
    with pytest.raises(TemporalEvidenceError, match="numeric scalar"):
        critique_from_provider_payload(ev, payload)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_score_fails_closed(value):
    ev = evidence()
    with pytest.raises(TemporalEvidenceError, match="finite"):
        critique_from_provider_payload(ev, authoritative_payload(ev, score=value))


def test_non_finite_dimension_fails_closed():
    ev = evidence()
    with pytest.raises(TemporalEvidenceError, match="finite"):
        critique_from_provider_payload(
            ev,
            authoritative_payload(ev, dimensions={"temporal_coherence": math.inf}),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provider", "p" * 129),
        ("provider_run_id", "r" * 257),
        ("provider_attestation_id", "a" * 257),
    ],
)
def test_authority_identity_fields_are_bounded(field, value):
    ev = evidence()
    with pytest.raises(TemporalEvidenceError, match="maximum length"):
        critique_from_provider_payload(ev, authoritative_payload(ev, **{field: value}))


def test_same_run_cross_media_replay_is_rejected():
    source = evidence(run_id="shared-run", media_text="candidate-a")
    target = evidence(run_id="shared-run", media_text="candidate-b")
    replayed_payload = authoritative_payload(source)
    with pytest.raises(TemporalEvidenceError, match="media_sha256 does not match"):
        critique_from_provider_payload(target, replayed_payload)


def test_payload_replay_on_different_candidate_is_rejected_even_with_same_provider_and_run():
    original = evidence(provider="provider-a", run_id="run-42", media_text="candidate-original")
    other = evidence(provider="provider-a", run_id="run-42", media_text="candidate-other")
    payload = authoritative_payload(original, provider_attestation_id="provider-event-777")
    with pytest.raises(TemporalEvidenceError, match="media_sha256 does not match"):
        critique_from_provider_payload(other, payload)


def test_p1_defect_forces_release_block_even_with_high_score():
    ev = evidence()
    sample = ev.samples[2]
    critique = critique_from_provider_payload(
        ev,
        authoritative_payload(
            ev,
            score=9.7,
            dimensions={"motion_choreography": 9.7},
            defects=[
                {
                    "code": "TEMPORAL_POP",
                    "severity": "P1",
                    "start_ms": max(0, sample.timestamp_ms - 20),
                    "end_ms": sample.timestamp_ms + 20,
                    "evidence_frame_indices": [sample.frame_index],
                    "description": "abrupt visual discontinuity",
                }
            ],
        ),
    )
    assert critique.authoritative is True
    assert critique.recommendation == "BLOCK"
    assert release_eligible(critique) is False


def test_defect_cannot_reference_unbound_frame():
    ev = evidence()
    unsampled = next(
        index
        for index in range(ev.frame_count)
        if index not in {s.frame_index for s in ev.samples}
    )
    with pytest.raises(TemporalEvidenceError, match="outside bound evidence"):
        critique_from_provider_payload(
            ev,
            authoritative_payload(
                ev,
                score=8.0,
                defects=[
                    {
                        "code": "GHOST",
                        "severity": "P2",
                        "start_ms": 100,
                        "end_ms": 200,
                        "evidence_frame_indices": [unsampled],
                    }
                ],
                recommendation="ITERATE",
            ),
        )


def test_defect_evidence_frame_must_fall_inside_its_interval():
    ev = evidence()
    sample = ev.samples[-2]
    assert sample.timestamp_ms > 100
    with pytest.raises(TemporalEvidenceError, match="outside defect interval"):
        critique_from_provider_payload(
            ev,
            authoritative_payload(
                ev,
                score=8.0,
                defects=[
                    {
                        "code": "MISBOUND",
                        "severity": "P2",
                        "start_ms": 0,
                        "end_ms": 100,
                        "evidence_frame_indices": [sample.frame_index],
                    }
                ],
                recommendation="ITERATE",
            ),
        )


def test_defect_integer_fields_reject_boolean_and_string_coercion():
    ev = evidence()
    sample = ev.samples[1]
    for bad_value in (True, "0"):
        payload = authoritative_payload(
            ev,
            recommendation="ITERATE",
            defects=[
                {
                    "code": "BAD_SCALAR",
                    "severity": "P2",
                    "start_ms": bad_value,
                    "end_ms": sample.timestamp_ms + 10,
                    "evidence_frame_indices": [sample.frame_index],
                }
            ],
        )
        with pytest.raises(TemporalEvidenceError, match="integer"):
            critique_from_provider_payload(ev, payload)


def test_evidence_hash_changes_when_sample_evidence_changes():
    ev1 = evidence()
    indices = uniform_sample_indices(90, target_samples=8)
    changed = hashes(indices)
    changed[indices[3]] = digest("mutated-frame")
    ev2 = build_temporal_evidence(
        media_sha256=digest("video"),
        frame_count=90,
        fps=30,
        frame_hashes=changed,
        provider="vision-provider",
        provider_run_id="run-1",
        provider_attested_full_video=True,
        target_samples=8,
    )
    assert ev1.content_hash() != ev2.content_hash()


def test_authoritative_clean_high_score_can_release():
    ev = evidence()
    critique = critique_from_provider_payload(
        ev,
        authoritative_payload(
            ev,
            score=9.3,
            dimensions={
                "temporal_coherence": 9.4,
                "motion_choreography": 9.2,
            },
        ),
    )
    assert critique.authoritative is True
    assert critique.provider_run_id == ev.provider_run_id
    assert critique.media_sha256 == ev.media_sha256
    assert critique.provider_attestation_id == "attestation-1"
    assert critique.full_video_scope is True
    assert critique.evidence_hash == ev.content_hash()
    assert release_eligible(critique) is True


def test_explicit_non_authoritative_payload_cannot_release():
    ev = evidence()
    payload = authoritative_payload(ev, authoritative=False)
    critique = critique_from_provider_payload(ev, payload)
    assert critique.authoritative is False
    assert critique.recommendation == "BLOCK"
    assert release_eligible(critique) is False


def test_score_outside_range_fails_closed():
    ev = evidence(attested=False)
    with pytest.raises(TemporalEvidenceError, match="scores"):
        critique_from_provider_payload(
            ev,
            {
                "provider": ev.provider,
                "provider_run_id": ev.provider_run_id,
                "authoritative": False,
                "score": 10.1,
            },
        )
