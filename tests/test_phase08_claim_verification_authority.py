import pytest

from src.content.source_security import normalize_claim, source_pack


def test_normalization_never_fabricates_verification_timestamp():
    for strength in ("DIRECT", "HIGH_CONFIDENCE", "TIME_SENSITIVE"):
        claim = normalize_claim(
            proposition="La cifra publicada es 42.",
            source_ref="https://example.com/source",
            evidence_strength=strength,
        )
        assert claim.verified_at is None
        assert claim.verification_evidence == ()
        assert claim.verification_state == "UNVERIFIED"
        assert claim.to_dict()["verification_state"] == "UNVERIFIED"


def test_verified_claim_requires_timestamp_and_evidence_as_one_attestation():
    with pytest.raises(ValueError, match="verified_at requires verification_evidence"):
        normalize_claim(
            proposition="Dato",
            source_ref="https://example.com",
            evidence_strength="DIRECT",
            verified_at="2026-08-28T12:00:00+00:00",
        )
    with pytest.raises(ValueError, match="verification_evidence requires verified_at"):
        normalize_claim(
            proposition="Dato",
            source_ref="https://example.com",
            evidence_strength="DIRECT",
            verification_evidence=("artifact:sha256:abc",),
        )


def test_verified_claim_exposes_evidence_bound_state():
    claim = normalize_claim(
        proposition="Dato verificado",
        source_ref="https://example.com",
        evidence_strength="DIRECT",
        verified_at="2026-08-28T12:00:00+00:00",
        verification_evidence=("source-snapshot:sha256:abc123", "review:run-7"),
    )
    assert claim.verification_state == "VERIFIED"
    payload = claim.to_dict()
    assert payload["verified_at"] == "2026-08-28T12:00:00+00:00"
    assert payload["verification_evidence"] == ("source-snapshot:sha256:abc123", "review:run-7")
    assert payload["verification_state"] == "VERIFIED"


def test_verification_timestamp_must_be_parseable_and_timezone_aware():
    for bad in ("now", "2026-08-28T12:00:00"):
        with pytest.raises(ValueError, match="verified_at"):
            normalize_claim(
                proposition="Dato",
                source_ref="https://example.com",
                evidence_strength="DIRECT",
                verified_at=bad,
                verification_evidence=("evidence:1",),
            )


def test_blank_verification_evidence_fails_closed():
    with pytest.raises(ValueError, match="non-empty"):
        normalize_claim(
            proposition="Dato",
            source_ref="https://example.com",
            evidence_strength="DIRECT",
            verified_at="2026-08-28T12:00:00Z",
            verification_evidence=("",),
        )


def test_claim_identity_does_not_depend_on_authority_promotion():
    base = normalize_claim(
        proposition="Mismo claim",
        source_ref="https://example.com/source",
        evidence_strength="DIRECT",
    )
    verified = normalize_claim(
        proposition="Mismo claim",
        source_ref="https://example.com/source",
        evidence_strength="DIRECT",
        verified_at="2026-08-28T12:00:00Z",
        verification_evidence=("snapshot:sha256:abc",),
    )
    assert base.claim_id == verified.claim_id
    assert base.verification_state == "UNVERIFIED"
    assert verified.verification_state == "VERIFIED"


def test_source_pack_preserves_explicit_unverified_state():
    claim = normalize_claim(
        proposition="Dato",
        source_ref="https://example.com/source",
        evidence_strength="HIGH_CONFIDENCE",
    )
    pack = source_pack("contenido", "https://example.com/source", claims=(claim,))
    assert pack["claims"][0]["verification_state"] == "UNVERIFIED"
    assert pack["claims"][0]["verified_at"] is None
