import pytest

from scripts.release_authority_guard import assess_release_authority, validate_release_state


SHA = "a" * 40
OTHER = "b" * 40


def _state(**overrides):
    base = {"release_status": "RELEASED", "p0_blockers": []}
    base.update(overrides)
    return base


def _pull(**overrides):
    base = {
        "number": 55,
        "merged_at": "2026-08-30T12:00:00Z",
        "merge_commit_sha": SHA,
        "base": {"ref": "main"},
    }
    base.update(overrides)
    return base


def _assess(**overrides):
    args = dict(
        repository="rotprods/motion-OS",
        release_sha=SHA,
        live_main_sha=SHA,
        live_main_sha_after=SHA,
        project_state=_state(),
        associated_pulls=[_pull()],
    )
    args.update(overrides)
    return assess_release_authority(**args)


def test_release_requires_stable_current_main_and_exact_pr_lineage():
    verdict = _assess()
    assert verdict.ok is True
    assert verdict.authority == "VERIFIED"
    assert verdict.matched_pr_numbers == (55,)


def test_live_main_drift_during_check_blocks_release():
    verdict = _assess(live_main_sha_after=OTHER)
    assert verdict.ok is False
    assert verdict.state == "LIVE_MAIN_DRIFTED_DURING_CHECK"
    assert verdict.authority == "BLOCKED"


def test_old_tag_or_noncurrent_release_target_is_blocked_even_if_state_says_released():
    verdict = _assess(release_sha=OTHER)
    assert verdict.ok is False
    assert verdict.state == "RELEASE_TARGET_NOT_CURRENT_MAIN"


def test_direct_write_main_is_blocked_even_if_state_says_released():
    verdict = _assess(associated_pulls=[])
    assert verdict.ok is False
    assert verdict.state == "MAIN_LINEAGE_UNVERIFIED"


def test_open_or_wrong_sha_pr_does_not_authorize_release():
    for pull in [_pull(merged_at=None), _pull(merge_commit_sha=OTHER)]:
        assert _assess(associated_pulls=[pull]).ok is False


@pytest.mark.parametrize(
    "state",
    [
        None,
        [],
        {},
        {"release_status": True, "p0_blockers": []},
        {"release_status": "RELEASED", "p0_blockers": None},
        {"release_status": "RELEASED", "p0_blockers": ""},
        {"release_status": "RELEASED", "p0_blockers": [""]},
        {"release_status": "BLOCKED", "p0_blockers": []},
        {"release_status": "RELEASED", "p0_blockers": ["P0 remains"]},
    ],
)
def test_release_state_structure_and_authority_fail_closed(state):
    with pytest.raises(ValueError):
        validate_release_state(state)


def test_release_state_extra_fields_do_not_change_authority_contract():
    validate_release_state({"release_status": "RELEASED", "p0_blockers": [], "other": {"untrusted": True}})


def test_malformed_lineage_payload_still_fails_closed_via_shared_contract():
    with pytest.raises(ValueError):
        _assess(associated_pulls={"spoof": "not a list"})
