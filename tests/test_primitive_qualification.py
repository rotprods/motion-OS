import hashlib

import pytest

from src.primitives.registry import build_registry
from src.qa.primitive_qualification import (
    LegacyAggregateClaim,
    PrimitiveEvidence,
    PrimitiveQualificationError,
    PrimitiveQualificationLedger,
    build_fixture_matrix,
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def physical(primitive_id: str, renderer: str, *, evidence_id=None, passed=True, frames=90, fps=30.0):
    return PrimitiveEvidence(
        evidence_id=evidence_id or f"ev:{primitive_id}:{renderer}",
        primitive_id=primitive_id,
        renderer=renderer,
        fixture_id=f"primitive:{primitive_id}:renderer:{renderer}:v1",
        test_run_id=f"run:{primitive_id}:{renderer}",
        evidence_kind="PHYSICAL_RENDER",
        passed=passed,
        fixture_sha256=digest(f"fixture:{primitive_id}:{renderer}"),
        artifact_sha256=digest(f"artifact:{primitive_id}:{renderer}"),
        frame_count=frames,
        fps=fps,
        visual_duration_ms=round(frames / fps * 1000),
        assertions=("frame_count_matches", "visual_output_verified") if passed else ("visual_failure_detected",),
    )


def contract(primitive_id: str, renderer: str):
    return PrimitiveEvidence(
        evidence_id=f"contract:{primitive_id}:{renderer}",
        primitive_id=primitive_id,
        renderer=renderer,
        fixture_id=f"primitive:{primitive_id}:renderer:{renderer}:v1",
        test_run_id=f"contract-run:{primitive_id}:{renderer}",
        evidence_kind="CONTRACT",
        passed=True,
        fixture_sha256=digest(f"fixture:{primitive_id}:{renderer}"),
        assertions=("schema_valid",),
    )


def test_live_registry_has_exactly_45_unique_semantic_primitives():
    registry = build_registry()
    assert len(registry) == 45
    assert len({p.id for p in registry}) == 45
    assert all(p.semantic_intents and p.channels and p.qa for p in registry)


def test_fixture_matrix_covers_every_declared_primitive_renderer_pair_once():
    registry = build_registry()
    matrix = build_fixture_matrix(registry)
    expected = {(p.id, renderer) for p in registry for renderer in p.renderer_support}
    observed = {(case.primitive_id, case.renderer) for case in matrix}
    assert observed == expected
    assert len(matrix) == len(expected) == 135
    assert [case.fixture_id for case in matrix] == [
        f"primitive:{case.primitive_id}:renderer:{case.renderer}:v1" for case in matrix
    ]


def test_legacy_15_30_aggregate_cannot_promote_any_primitive_without_id_bound_evidence():
    ledger = PrimitiveQualificationLedger()
    report = ledger.report(LegacyAggregateClaim("CP25", 45, 15, 30))
    assert report["registered_primitives"] == 45
    assert report["empirical_authority"] == 0
    assert report["primitive_counts"]["UNQUALIFIED"] == 45
    assert report["renderer_cases"]["unqualified"] == 135
    assert report["legacy_aggregate"]["verified_count"] == 15
    assert report["legacy_aggregate"]["mapped_to_primitive_ids"] is False
    assert report["legacy_aggregate"]["authority_effect"] == "NONE"


def test_single_physical_renderer_does_not_overpromote_primitive_across_other_renderers():
    ledger = PrimitiveQualificationLedger(evidence=[physical("macro_push", "remotion")])
    assert ledger.renderer_state("macro_push", "remotion") == "PHYSICALLY_VERIFIED"
    assert ledger.renderer_state("macro_push", "hyperframes") == "UNQUALIFIED"
    assert ledger.primitive_state("macro_push") == "CONTRACT_VERIFIED"


def test_primitive_is_physical_only_when_all_declared_renderers_have_physical_evidence():
    primitive = next(p for p in build_registry() if p.id == "macro_push")
    ledger = PrimitiveQualificationLedger(
        evidence=[physical(primitive.id, renderer) for renderer in primitive.renderer_support]
    )
    assert ledger.primitive_state("macro_push") == "PHYSICALLY_VERIFIED"
    assert ledger.report()["empirical_authority"] == 1


def test_contract_evidence_never_counts_as_physical_authority():
    ledger = PrimitiveQualificationLedger(evidence=[contract("macro_push", "remotion")])
    assert ledger.renderer_state("macro_push", "remotion") == "CONTRACT_VERIFIED"
    assert ledger.primitive_state("macro_push") == "CONTRACT_VERIFIED"
    assert ledger.report()["empirical_authority"] == 0


def test_failed_physical_fixture_quarantines_that_renderer_and_primitive():
    ledger = PrimitiveQualificationLedger(evidence=[physical("macro_push", "remotion", passed=False)])
    assert ledger.renderer_state("macro_push", "remotion") == "QUARANTINED"
    assert ledger.primitive_state("macro_push") == "QUARANTINED"


def test_unknown_primitive_fails_closed():
    with pytest.raises(PrimitiveQualificationError, match="unknown primitive_id"):
        PrimitiveQualificationLedger(evidence=[physical("invented_primitive", "remotion")])


def test_undeclared_renderer_fails_closed():
    with pytest.raises(PrimitiveQualificationError, match="not declared"):
        PrimitiveQualificationLedger(evidence=[physical("macro_push", "unknown_renderer")])


def test_noncanonical_fixture_id_fails_closed():
    item = physical("macro_push", "remotion")
    item = PrimitiveEvidence(
        evidence_id=item.evidence_id,
        primitive_id=item.primitive_id,
        renderer=item.renderer,
        fixture_id="ad-hoc-fixture",
        test_run_id=item.test_run_id,
        evidence_kind=item.evidence_kind,
        passed=item.passed,
        fixture_sha256=item.fixture_sha256,
        artifact_sha256=item.artifact_sha256,
        frame_count=item.frame_count,
        fps=item.fps,
        visual_duration_ms=item.visual_duration_ms,
        assertions=item.assertions,
    )
    with pytest.raises(PrimitiveQualificationError, match="canonical"):
        PrimitiveQualificationLedger(evidence=[item])


def test_physical_evidence_requires_artifact_hash_and_visual_time_authority():
    with pytest.raises(PrimitiveQualificationError, match="artifact_sha256"):
        PrimitiveEvidence(
            evidence_id="x", primitive_id="macro_push", renderer="remotion",
            fixture_id="primitive:macro_push:renderer:remotion:v1", test_run_id="run",
            evidence_kind="PHYSICAL_RENDER", passed=True, fixture_sha256=digest("fixture"),
            frame_count=90, fps=30, visual_duration_ms=3000, assertions=("ok",),
        )
    with pytest.raises(PrimitiveQualificationError, match="visual duration"):
        PrimitiveEvidence(
            evidence_id="x", primitive_id="macro_push", renderer="remotion",
            fixture_id="primitive:macro_push:renderer:remotion:v1", test_run_id="run",
            evidence_kind="PHYSICAL_RENDER", passed=True, fixture_sha256=digest("fixture"),
            artifact_sha256=digest("artifact"), frame_count=90, fps=30, visual_duration_ms=5000,
            assertions=("ok",),
        )


def test_pass_without_explicit_assertions_fails_closed():
    with pytest.raises(PrimitiveQualificationError, match="assertions"):
        PrimitiveEvidence(
            evidence_id="x", primitive_id="macro_push", renderer="remotion",
            fixture_id="primitive:macro_push:renderer:remotion:v1", test_run_id="run",
            evidence_kind="CONTRACT", passed=True, fixture_sha256=digest("fixture"), assertions=(),
        )


def test_identical_evidence_replay_is_idempotent_but_conflicting_reuse_fails_closed():
    item = physical("macro_push", "remotion", evidence_id="same")
    ledger = PrimitiveQualificationLedger(evidence=[item, item])
    assert len(ledger.evidence) == 1
    conflict = physical("macro_push", "remotion", evidence_id="same", passed=False)
    with pytest.raises(PrimitiveQualificationError, match="conflicting payload"):
        ledger.add(conflict)


def test_legacy_aggregate_must_match_live_registry_count():
    ledger = PrimitiveQualificationLedger()
    with pytest.raises(PrimitiveQualificationError, match="live registry"):
        ledger.report(LegacyAggregateClaim("CP25", 44, 15, 29))
