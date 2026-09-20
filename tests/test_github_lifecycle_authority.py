import pytest

from src.coordination.github_lifecycle import (
    GitHubLifecycleSnapshot,
    PRLifecycle,
    PullRequestSnapshot,
)


def _raw(**overrides):
    value = {
        "number": 44,
        "head": "feat/test",
        "head_sha": "1" * 40,
        "base": "main",
        "state": "open",
        "draft": False,
        "merged": False,
        "merged_at": None,
    }
    value.update(overrides)
    return value


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("draft", "false"),
        ("draft", 0),
        ("merged", "false"),
        ("merged", 0),
    ],
)
def test_github_lifecycle_rejects_truthy_or_coercible_boolean_spoofs(field, value):
    with pytest.raises(ValueError, match="literal boolean"):
        PullRequestSnapshot.from_github(_raw(**{field: value}))


def test_github_lifecycle_rejects_unknown_state_and_noncanonical_sha():
    with pytest.raises(ValueError, match="state must be open or closed"):
        PullRequestSnapshot.from_github(_raw(state="mystery"))
    with pytest.raises(ValueError, match="40-character lowercase Git SHA"):
        PullRequestSnapshot.from_github(_raw(head_sha="not-a-sha"))


def test_direct_lifecycle_snapshot_cannot_forge_revision_hash():
    pr = PullRequestSnapshot.from_github(_raw())
    with pytest.raises(ValueError, match="revision_hash does not match"):
        GitHubLifecycleSnapshot(
            repository="rotprods/motion-OS",
            main_sha="a" * 40,
            prs=(pr,),
            revision_hash="0" * 64,
        )


def test_built_lifecycle_snapshot_is_self_verifying_and_sorted():
    snapshot = GitHubLifecycleSnapshot.build(
        repository="rotprods/motion-OS",
        main_sha="a" * 40,
        prs=[
            _raw(number=45, head="feat/b", head_sha="2" * 40),
            _raw(number=44, head="feat/a", head_sha="1" * 40, draft=True),
        ],
    )
    assert snapshot.verify_hash() is True
    assert [item.number for item in snapshot.prs] == [44, 45]
    assert snapshot.prs[0].state == PRLifecycle.OPEN_DRAFT
    assert snapshot.prs[1].state == PRLifecycle.OPEN


def test_merged_at_must_be_null_or_nonempty_text():
    with pytest.raises(ValueError, match="merged_at"):
        PullRequestSnapshot.from_github(_raw(merged_at=False))
