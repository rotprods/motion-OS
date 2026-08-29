import hashlib

import pytest

from src.benchmarks.authority import (
    BenchmarkBriefEvidence,
    BenchmarkEvidenceError,
    BenchmarkLedger,
    BriefStatus,
    LegacyBenchmarkClaim,
)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def passed(brief_id: str, style: str, *, score: float = 9.2, evidence_id: str | None = None) -> BenchmarkBriefEvidence:
    return BenchmarkBriefEvidence(
        evidence_id=evidence_id or f"ev-{brief_id}",
        brief_id=brief_id,
        style_family=style,
        brief_sha256=sha(f"brief:{brief_id}"),
        artifact_sha256=sha(f"artifact:{brief_id}"),
        test_run_id=f"run-{brief_id}",
        status=BriefStatus.PASS,
        quality_score=score,
        assertions=("artifact_bound", "creative_gate_passed"),
    )


def test_legacy_25x5_aggregate_grants_no_authority():
    claim = LegacyBenchmarkClaim(brief_count=25, style_count=5)
    assert claim.authority_effect == "NONE"
    assert claim.mapped_to_brief_ids is False


def test_legacy_claim_cannot_self_promote():
    with pytest.raises(BenchmarkEvidenceError):
        LegacyBenchmarkClaim(brief_count=25, style_count=5, mapped_to_brief_ids=True, authority_effect="VERIFIED")


def test_pass_requires_artifact_score_and_assertions():
    with pytest.raises(BenchmarkEvidenceError, match="artifact"):
        BenchmarkBriefEvidence("e", "b", "s", sha("b"), None, "run", BriefStatus.PASS, 9.5, (), ("ok",))
    with pytest.raises(BenchmarkEvidenceError, match="quality"):
        BenchmarkBriefEvidence("e", "b", "s", sha("b"), sha("a"), "run", BriefStatus.PASS, None, (), ("ok",))
    with pytest.raises(BenchmarkEvidenceError, match="assertions"):
        BenchmarkBriefEvidence("e", "b", "s", sha("b"), sha("a"), "run", BriefStatus.PASS, 9.5)


def test_string_status_cannot_bypass_pass_requirements():
    with pytest.raises(BenchmarkEvidenceError, match="BriefStatus"):
        BenchmarkBriefEvidence("e", "b", "s", sha("b"), None, "run", "PASS")  # type: ignore[arg-type]


def test_assertions_and_findings_must_be_tuples_not_truthy_strings():
    with pytest.raises(BenchmarkEvidenceError, match="assertions"):
        BenchmarkBriefEvidence("e", "b", "s", sha("b"), sha("a"), "run", BriefStatus.PASS, 9.5, (), "looks-good")  # type: ignore[arg-type]
    with pytest.raises(BenchmarkEvidenceError, match="findings"):
        BenchmarkBriefEvidence("e2", "b2", "s", sha("b2"), None, "run2", BriefStatus.FAIL, findings="failed")  # type: ignore[arg-type]


def test_failure_requires_findings():
    with pytest.raises(BenchmarkEvidenceError, match="findings"):
        BenchmarkBriefEvidence("e", "b", "s", sha("b"), None, "run", BriefStatus.FAIL)


def test_conflicting_evidence_id_reuse_fails_closed():
    ledger = BenchmarkLedger()
    ledger.append(passed("b1", "style-a", evidence_id="same"))
    with pytest.raises(BenchmarkEvidenceError, match="conflicting"):
        ledger.append(passed("b2", "style-b", evidence_id="same"))


def test_identical_evidence_replay_is_idempotent():
    ledger = BenchmarkLedger()
    item = passed("b1", "style-a")
    ledger.append(item)
    ledger.append(item)
    assert ledger.metrics().passed_briefs == 1


def test_25_balanced_passes_across_five_styles_can_be_authoritative():
    ledger = BenchmarkLedger()
    styles = [f"style-{i}" for i in range(5)]
    for i in range(25):
        ledger.append(passed(f"b{i:02d}", styles[i % 5]))
    metrics = ledger.metrics()
    assert metrics.passed_briefs == 25
    assert metrics.apsr == 1.0
    assert metrics.gsr == 1.0
    assert metrics.mean_quality == pytest.approx(9.2)
    assert metrics.minimum_quality == pytest.approx(9.2)
    assert all(count == 5 for _, count in metrics.style_pass_counts)
    assert metrics.authoritative is True
    assert metrics.blockers == ()


def test_25_passes_in_one_style_fails_generalization():
    ledger = BenchmarkLedger()
    for i in range(25):
        ledger.append(passed(f"b{i:02d}", "one-style"))
    metrics = ledger.metrics()
    assert metrics.apsr == 1.0
    assert metrics.gsr == 0.0
    assert metrics.authoritative is False
    assert any(item.startswith("style_families:") for item in metrics.blockers)
    assert any(item.startswith("style_balance:") for item in metrics.blockers)


def test_five_styles_with_unbalanced_distribution_fails_gsr():
    ledger = BenchmarkLedger()
    styles = ["a"] * 21 + ["b", "c", "d", "e"]
    for i, style in enumerate(styles):
        ledger.append(passed(f"b{i:02d}", style))
    metrics = ledger.metrics()
    assert metrics.apsr == 1.0
    assert metrics.gsr == pytest.approx(0.2)
    assert metrics.authoritative is False
    assert "style_balance:1/5@5" in metrics.blockers


def test_single_low_quality_pass_cannot_hide_behind_high_mean():
    ledger = BenchmarkLedger()
    for i in range(25):
        score = 8.8 if i == 0 else 9.8
        ledger.append(passed(f"b{i:02d}", f"style-{i % 5}", score=score))
    metrics = ledger.metrics()
    assert metrics.mean_quality > 9.0
    assert metrics.minimum_quality == 8.8
    assert metrics.authoritative is False
    assert any(item.startswith("minimum_quality:") for item in metrics.blockers)


def test_high_pass_count_with_low_quality_is_not_authoritative():
    ledger = BenchmarkLedger()
    for i in range(25):
        ledger.append(passed(f"b{i:02d}", f"style-{i % 5}", score=8.99))
    metrics = ledger.metrics()
    assert metrics.authoritative is False
    assert any(item.startswith("mean_quality:") for item in metrics.blockers)


def test_failed_or_blocked_brief_prevents_authority():
    ledger = BenchmarkLedger()
    for i in range(24):
        ledger.append(passed(f"b{i:02d}", f"style-{i % 5}"))
    ledger.append(BenchmarkBriefEvidence("ev-f", "bf", "style-4", sha("bf"), None, "run-f", BriefStatus.FAIL, findings=("render_failed",)))
    metrics = ledger.metrics()
    assert metrics.authoritative is False
    assert metrics.failed_briefs == 1


def test_two_distinct_revisions_for_same_brief_are_ambiguous_without_supersession():
    ledger = BenchmarkLedger()
    ledger.append(passed("b1", "style-a", evidence_id="rev1"))
    ledger.append(BenchmarkBriefEvidence("rev2", "b1", "style-a", sha("brief:b1:changed"), sha("artifact:b1:changed"), "run2", BriefStatus.PASS, 9.5, assertions=("artifact_bound",)))
    metrics = ledger.metrics(required_briefs=1, required_styles=1)
    assert metrics.authoritative is False
    assert metrics.passed_briefs == 0
    assert "ambiguous_brief_revisions:b1" in metrics.blockers


def test_metrics_hash_is_deterministic_independent_of_append_order():
    a, b = BenchmarkLedger(), BenchmarkLedger()
    items = [passed("b1", "s1"), passed("b2", "s2")]
    for item in items:
        a.append(item)
    for item in reversed(items):
        b.append(item)
    assert a.metrics().evidence_hash == b.metrics().evidence_hash


def test_nonfinite_quality_fails_closed():
    for value in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(BenchmarkEvidenceError):
            passed("b1", "s", score=value)
