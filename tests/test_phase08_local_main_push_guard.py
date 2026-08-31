import pytest

from scripts.pre_push_ref_guard import _ZERO_SHA, blocked_main_updates, parse_push_updates


A = "a" * 40
B = "b" * 40


def _line(local_ref: str, local_sha: str, remote_ref: str, remote_sha: str) -> str:
    return f"{local_ref} {local_sha} {remote_ref} {remote_sha}\n"


def test_feature_branch_update_is_allowed():
    updates = parse_push_updates([_line("refs/heads/feat/x", A, "refs/heads/feat/x", B)])
    assert blocked_main_updates(updates) == ()


def test_symbolic_or_detached_local_source_does_not_change_destination_policy():
    head_source = parse_push_updates([_line("HEAD", A, "refs/heads/feat/x", B)])
    sha_source = parse_push_updates([_line(A, A, "refs/heads/feat/x", B)])
    assert blocked_main_updates(head_source) == ()
    assert blocked_main_updates(sha_source) == ()


def test_direct_main_update_is_blocked():
    updates = parse_push_updates([_line("refs/heads/main", A, "refs/heads/main", B)])
    assert len(blocked_main_updates(updates)) == 1


def test_any_local_source_targeting_remote_main_is_blocked():
    updates = parse_push_updates([_line("HEAD", A, "refs/heads/main", B)])
    assert len(blocked_main_updates(updates)) == 1


def test_create_remote_main_is_blocked():
    updates = parse_push_updates([_line("refs/heads/new", A, "refs/heads/main", _ZERO_SHA)])
    assert len(blocked_main_updates(updates)) == 1


def test_delete_main_is_blocked_but_delete_feature_is_allowed():
    main_delete = parse_push_updates([_line("(delete)", _ZERO_SHA, "refs/heads/main", B)])
    feature_delete = parse_push_updates([_line("(delete)", _ZERO_SHA, "refs/heads/feat/x", B)])
    assert len(blocked_main_updates(main_delete)) == 1
    assert blocked_main_updates(feature_delete) == ()


def test_multi_ref_push_blocks_if_any_destination_is_main():
    updates = parse_push_updates([
        _line("refs/heads/feat/x", A, "refs/heads/feat/x", B),
        _line("refs/heads/main", A, "refs/heads/main", B),
    ])
    assert [item.remote_ref for item in blocked_main_updates(updates)] == ["refs/heads/main"]


def test_delete_marker_and_zero_sha_must_match():
    with pytest.raises(ValueError, match="delete marker"):
        parse_push_updates([_line("(delete)", A, "refs/heads/feat/x", B)])
    with pytest.raises(ValueError, match="delete marker"):
        parse_push_updates([_line("refs/heads/feat/x", _ZERO_SHA, "refs/heads/feat/x", B)])


@pytest.mark.parametrize(
    "lines",
    [
        [],
        ["\n"],
        ["only three fields here\n"],
        [_line("refs/heads/x", "badsha", "refs/heads/x", B)],
        [_line("refs/heads/x", A, "main", B)],
        [_line("refs/heads/x\nspoof", A, "refs/heads/x", B)],
    ],
)
def test_malformed_pre_push_input_fails_closed(lines):
    with pytest.raises(ValueError):
        parse_push_updates(lines)


def test_update_count_is_bounded():
    with pytest.raises(ValueError, match="safety bound"):
        parse_push_updates([_line(f"refs/heads/x{i}", A, f"refs/heads/x{i}", B) for i in range(257)])
