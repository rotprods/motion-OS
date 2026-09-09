from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

import scripts.release_candidate_rehearsal as rehearsal


REPO = "rotprods/motion-OS"
CANDIDATE = "a" * 40
MAIN = "d4e628a1aef0cd382c3c2f1ea327a8ff70c41bd9"
ROOT = Path(__file__).resolve().parents[1]


def _main(sha: str = MAIN, *, protected: bool = False) -> dict:
    return {"name": "main", "commit": {"sha": sha}, "protected": protected}


def _barrier(state: str = "open") -> dict:
    return {"number": 48, "state": state}


def _assess(*, protected: bool = False, barrier: str = "open", expected: str = MAIN) -> dict:
    return rehearsal.assess_rehearsal(
        repository=REPO,
        candidate_sha=CANDIDATE,
        expected_main_sha=expected,
        main_before=_main(protected=protected),
        main_after=_main(protected=protected),
        barrier_before=_barrier(barrier),
        barrier_after=_barrier(barrier),
    )


def test_live_current_state_is_blocked_by_both_external_preconditions():
    result = _assess()
    rehearsal.verify_attestation(result)
    assert result["status"] == "BLOCKED_EXTERNAL"
    assert result["blockers"] == ["issue_48_open", "main_native_protection_absent"]
    assert result["promotion_authorized"] is False
    assert result["release_authorized"] is False
    assert result["project_done"] is False


def test_closed_barrier_without_native_protection_remains_blocked():
    result = _assess(barrier="closed")
    assert result["status"] == "BLOCKED_EXTERNAL"
    assert result["blockers"] == ["main_native_protection_absent"]


def test_protected_main_with_open_barrier_remains_blocked():
    result = _assess(protected=True)
    assert result["status"] == "BLOCKED_EXTERNAL"
    assert result["blockers"] == ["issue_48_open"]


def test_all_external_preconditions_can_be_observed_without_granting_authority():
    result = _assess(protected=True, barrier="closed")
    rehearsal.verify_attestation(result)
    assert result["status"] == "PRECONDITIONS_SATISFIED"
    assert result["blockers"] == []
    assert result["promotion_authorized"] is False
    assert result["release_authorized"] is False
    assert result["project_done"] is False


def test_main_drift_during_check_invalidates_rehearsal():
    result = rehearsal.assess_rehearsal(
        repository=REPO,
        candidate_sha=CANDIDATE,
        expected_main_sha=MAIN,
        main_before=_main(),
        main_after=_main("b" * 40),
        barrier_before=_barrier(),
        barrier_after=_barrier(),
    )
    assert result["status"] == "STALE_LIVE_AUTHORITY"
    assert result["blockers"] == ["live_authority_drifted_during_check"]


def test_protection_drift_during_check_invalidates_rehearsal():
    result = rehearsal.assess_rehearsal(
        repository=REPO,
        candidate_sha=CANDIDATE,
        expected_main_sha=MAIN,
        main_before=_main(protected=False),
        main_after=_main(protected=True),
        barrier_before=_barrier(),
        barrier_after=_barrier(),
    )
    assert result["status"] == "STALE_LIVE_AUTHORITY"


def test_barrier_drift_during_check_invalidates_rehearsal():
    result = rehearsal.assess_rehearsal(
        repository=REPO,
        candidate_sha=CANDIDATE,
        expected_main_sha=MAIN,
        main_before=_main(),
        main_after=_main(),
        barrier_before=_barrier("open"),
        barrier_after=_barrier("closed"),
    )
    assert result["status"] == "STALE_LIVE_AUTHORITY"


def test_expected_main_binding_goes_stale_when_main_changes_before_check():
    result = rehearsal.assess_rehearsal(
        repository=REPO,
        candidate_sha=CANDIDATE,
        expected_main_sha="c" * 40,
        main_before=_main(),
        main_after=_main(),
        barrier_before=_barrier(),
        barrier_after=_barrier(),
    )
    assert result["status"] == "STALE_EXPECTED_MAIN"
    assert result["blockers"] == ["expected_main_sha_mismatch"]


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "main", "commit": {"sha": MAIN}, "protected": "false"},
        {"name": "other", "commit": {"sha": MAIN}, "protected": False},
        {"name": "main", "commit": {}, "protected": False},
    ],
)
def test_malformed_main_payload_fails_closed(payload: dict):
    with pytest.raises(ValueError, match="invalid_main_response|invalid_commit_sha"):
        rehearsal.assess_rehearsal(
            repository=REPO,
            candidate_sha=CANDIDATE,
            expected_main_sha=MAIN,
            main_before=payload,
            main_after=payload,
            barrier_before=_barrier(),
            barrier_after=_barrier(),
        )


def test_malformed_barrier_payload_fails_closed():
    with pytest.raises(ValueError, match="invalid_barrier_response"):
        rehearsal.assess_rehearsal(
            repository=REPO,
            candidate_sha=CANDIDATE,
            expected_main_sha=MAIN,
            main_before=_main(),
            main_after=_main(),
            barrier_before={"number": 49, "state": "closed"},
            barrier_after={"number": 49, "state": "closed"},
        )


def test_attestation_tamper_is_rejected():
    result = _assess()
    result["observed_main_sha"] = "b" * 40
    with pytest.raises(ValueError, match="attestation_hash_mismatch"):
        rehearsal.verify_attestation(result)


def test_rehashed_self_promotion_attempt_is_still_rejected():
    result = _assess(protected=True, barrier="closed")
    mutated = deepcopy(result)
    mutated["promotion_authorized"] = True
    mutated.pop("attestation_hash")
    mutated["attestation_hash"] = rehearsal._canonical_hash(mutated)
    with pytest.raises(ValueError, match="rehearsal_cannot_authorize_release"):
        rehearsal.verify_attestation(mutated)


def test_rehearsal_cli_bootstraps_from_clean_checkout_without_site_packages():
    completed = subprocess.run(
        [sys.executable, "-S", "scripts/release_candidate_rehearsal.py", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--expected-main-sha" in completed.stdout
    assert "--expect-status" in completed.stdout


def test_ci_expected_blocked_mode_returns_success_only_for_exact_blocked_state(monkeypatch, tmp_path: Path):
    responses = iter([_main(), _barrier(), _main(), _barrier()])
    monkeypatch.setattr(rehearsal, "_github_json", lambda **kwargs: next(responses))
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.setenv("GITHUB_SHA", CANDIDATE)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    out = tmp_path / "rehearsal.json"

    code = rehearsal.main([
        "--expected-main-sha", MAIN,
        "--expect-status", "BLOCKED_EXTERNAL",
        "--json-out", str(out),
    ])

    assert code == 0
    persisted = json.loads(out.read_text(encoding="utf-8"))
    rehearsal.verify_attestation(persisted)
    assert persisted["status"] == "BLOCKED_EXTERNAL"


def test_normal_cli_mode_refuses_zero_exit_for_blocked_candidate(monkeypatch, tmp_path: Path):
    responses = iter([_main(), _barrier(), _main(), _barrier()])
    monkeypatch.setattr(rehearsal, "_github_json", lambda **kwargs: next(responses))
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.setenv("GITHUB_SHA", CANDIDATE)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    code = rehearsal.main([
        "--expected-main-sha", MAIN,
        "--json-out", str(tmp_path / "rehearsal.json"),
    ])
    assert code == 2
