import hashlib

import pytest

from src.qa.primitive_qualification import (
    LegacyAggregateClaim,
    PrimitiveEvidence,
    PrimitiveQualificationError,
    PrimitiveQualificationLedger,
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def physical(**overrides):
    payload = {
        "evidence_id": "physical:test:macro_push:remotion",
        "primitive_id": "macro_push",
        "renderer": "remotion",
        "fixture_id": "primitive:macro_push:renderer:remotion:v1",
        "test_run_id": "run-1",
        "evidence_kind": "PHYSICAL_RENDER",
        "passed": True,
        "fixture_sha256": digest("fixture"),
        "artifact_sha256": digest("artifact"),
        "frame_count": 90,
        "fps": 30.0,
        "visual_duration_ms": 3000,
        "assertions": ("artifact_decodes", "primitive_identity_verified"),
    }
    payload.update(overrides)
    return PrimitiveEvidence(**payload)


@pytest.mark.parametrize("spoof", ["false", "true", 1, 0, None])
def test_passed_authority_requires_literal_boolean(spoof):
    with pytest.raises(PrimitiveQualificationError, match="JSON boolean"):
        physical(passed=spoof)


@pytest.mark.parametrize(
    "field,spoof",
    [
        ("frame_count", True),
        ("fps", True),
        ("visual_duration_ms", True),
        ("fps", float("nan")),
        ("fps", float("inf")),
    ],
)
def test_physical_timing_type_confusion_and_nonfinite_values_fail_closed(field, spoof):
    with pytest.raises(PrimitiveQualificationError, match="physical timing evidence"):
        physical(**{field: spoof})


def test_uppercase_or_nonhex_digest_cannot_be_evidence_identity():
    with pytest.raises(PrimitiveQualificationError, match="lowercase hex"):
        physical(fixture_sha256="A" * 64)
    with pytest.raises(PrimitiveQualificationError, match="lowercase hex"):
        physical(artifact_sha256="z" * 64)


def test_assertion_container_must_be_nonempty_tuple_of_nonempty_strings():
    with pytest.raises(PrimitiveQualificationError, match="tuple"):
        physical(assertions="artifact_decodes")
    with pytest.raises(PrimitiveQualificationError, match="assertion"):
        physical(assertions=("artifact_decodes", ""))


def test_contract_evidence_cannot_smuggle_physical_authority_fields():
    with pytest.raises(PrimitiveQualificationError, match="cannot carry physical"):
        PrimitiveEvidence(
            evidence_id="contract:test",
            primitive_id="macro_push",
            renderer="remotion",
            fixture_id="primitive:macro_push:renderer:remotion:v1",
            test_run_id="run-1",
            evidence_kind="CONTRACT",
            passed=True,
            fixture_sha256=digest("fixture"),
            artifact_sha256=digest("artifact"),
            assertions=("schema_valid",),
        )


def test_validated_literal_physical_pass_still_promotes_only_one_renderer():
    item = physical()
    ledger = PrimitiveQualificationLedger(evidence=[item])
    assert ledger.renderer_state("macro_push", "remotion") == "PHYSICALLY_VERIFIED"
    assert ledger.primitive_state("macro_push") == "CONTRACT_VERIFIED"


def test_legacy_counts_reject_boolean_type_confusion():
    with pytest.raises(PrimitiveQualificationError, match="non-negative integer"):
        LegacyAggregateClaim("CP25", True, 1, 0)
