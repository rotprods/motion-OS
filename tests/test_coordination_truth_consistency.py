import pytest

from src.coordination.truth_consistency import (
    TruthClaim,
    compile_truth_consistency,
    require_truth_consistency,
)


def test_live_github_overrides_stale_current_lifecycle_claims():
    report = compile_truth_consistency(
        live_github={"main:sha": "abc1234", "pr:44": "MERGED"},
        claims=[
            TruthClaim("ACTIVE_AGENTS.yaml", "pr:44", "FINAL_QUALIFICATION"),
            TruthClaim("project_state.json", "main:sha", "old0000"),
        ],
    )
    assert not report.ok
    assert report.stale_surfaces == ("ACTIVE_AGENTS.yaml", "project_state.json")
    assert {c.key for c in report.conflicts} == {"main:sha", "pr:44"}


def test_historical_claims_are_preserved_without_becoming_current_conflicts():
    report = compile_truth_consistency(
        live_github={"pr:44": "MERGED"},
        claims=[TruthClaim("historical_event", "pr:44", "OPEN_DRAFT", current=False)],
    )
    assert report.ok
    assert report.conflicts == ()


def test_scalar_types_are_normalized_without_string_coercion_bugs():
    report = compile_truth_consistency(
        live_github={"ci:green": True, "pr:count": 2},
        claims=[
            TruthClaim("machine-view", "ci:green", True),
            TruthClaim("machine-view", "pr:count", 2),
        ],
    )
    assert report.ok


def test_ambiguous_truth_value_and_current_marker_fail_closed():
    with pytest.raises(ValueError, match="scalar"):
        compile_truth_consistency(live_github={"pr:44": {"state": "MERGED"}}, claims=[])
    with pytest.raises(ValueError, match="current must be boolean"):
        TruthClaim("surface", "pr:44", "MERGED", current="false")  # type: ignore[arg-type]


def test_unknown_live_authority_domain_fails_closed():
    with pytest.raises(ValueError, match="unsupported live truth key"):
        compile_truth_consistency(
            live_github={"authority:write": "GRANTED"},
            claims=[],
        )


def test_require_truth_consistency_blocks_irreversible_action_preflight():
    with pytest.raises(RuntimeError, match="canonical truth conflict"):
        require_truth_consistency(
            live_github={"pr:53": "OPEN_DRAFT"},
            claims=[TruthClaim("bootstrap", "pr:53", "MERGED")],
        )
