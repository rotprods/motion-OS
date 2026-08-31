from pathlib import Path

import pytest

from scripts.main_lineage_sentinel import _safe_output_path, assess_lineage


SHA = "a" * 40


def _pr(**overrides):
    base = {
        "number": 42,
        "merged_at": "2026-08-30T12:00:00Z",
        "merge_commit_sha": SHA,
        "base": {"ref": "main"},
    }
    base.update(overrides)
    return base


def test_exact_merged_pr_lineage_passes():
    verdict = assess_lineage(repository="rotprods/motion-OS", commit_sha=SHA, target_branch="main", pulls=[_pr()])
    assert verdict.ok is True
    assert verdict.authority == "VERIFIED"
    assert verdict.matched_pr_numbers == (42,)


def test_direct_write_or_untraceable_commit_is_blocked():
    verdict = assess_lineage(repository="rotprods/motion-OS", commit_sha=SHA, target_branch="main", pulls=[])
    assert verdict.ok is False
    assert verdict.state == "DIRECT_WRITE_OR_UNTRACEABLE"
    assert verdict.authority == "BLOCKED"


def test_open_or_unmerged_pr_does_not_authorize_commit():
    verdict = assess_lineage(
        repository="rotprods/motion-OS",
        commit_sha=SHA,
        target_branch="main",
        pulls=[_pr(merged_at=None)],
    )
    assert verdict.ok is False


def test_wrong_target_branch_does_not_authorize_commit():
    verdict = assess_lineage(
        repository="rotprods/motion-OS",
        commit_sha=SHA,
        target_branch="main",
        pulls=[_pr(base={"ref": "release"})],
    )
    assert verdict.ok is False


def test_associated_pr_with_different_merge_sha_does_not_authorize_direct_push():
    verdict = assess_lineage(
        repository="rotprods/motion-OS",
        commit_sha=SHA,
        target_branch="main",
        pulls=[_pr(merge_commit_sha="b" * 40)],
    )
    assert verdict.ok is False


def test_multiple_matching_prs_are_sorted_and_deterministic():
    pulls = [_pr(number=9), _pr(number=2)]
    verdict = assess_lineage(repository="rotprods/motion-OS", commit_sha=SHA, target_branch="main", pulls=pulls)
    assert verdict.matched_pr_numbers == (2, 9)


@pytest.mark.parametrize(
    "repository,sha,branch,pulls",
    [
        ("../evil/repo", SHA, "main", []),
        ("rotprods/motion-OS", "not-a-sha", "main", []),
        ("rotprods/motion-OS", SHA, "main\nspoof", []),
        ("rotprods/motion-OS", SHA, "main", {}),
        ("rotprods/motion-OS", SHA, "main", ["not-an-object"]),
        ("rotprods/motion-OS", SHA, "main", [{"number": True, "merged_at": None, "merge_commit_sha": None, "base": {"ref": "main"}}]),
        ("rotprods/motion-OS", SHA, "main", [{"number": 1, "merged_at": 123, "merge_commit_sha": None, "base": {"ref": "main"}}]),
        ("rotprods/motion-OS", SHA, "main", [{"number": 1, "merged_at": None, "merge_commit_sha": None, "base": {}}]),
    ],
)
def test_malformed_untrusted_github_data_fails_closed(repository, sha, branch, pulls):
    with pytest.raises(ValueError):
        assess_lineage(repository=repository, commit_sha=sha, target_branch=branch, pulls=pulls)


def test_response_size_is_bounded():
    with pytest.raises(ValueError, match="safety bound"):
        assess_lineage(repository="rotprods/motion-OS", commit_sha=SHA, target_branch="main", pulls=[_pr(number=i + 1) for i in range(101)])


def test_json_evidence_path_must_stay_inside_working_tree(tmp_path: Path):
    safe = _safe_output_path(".artifacts/main-lineage.json", root=tmp_path)
    assert safe == (tmp_path / ".artifacts/main-lineage.json").resolve()

    with pytest.raises(ValueError, match="working tree"):
        _safe_output_path("../escape.json", root=tmp_path)
    with pytest.raises(ValueError, match="working tree"):
        _safe_output_path(str((tmp_path.parent / "escape.json").resolve()), root=tmp_path)
