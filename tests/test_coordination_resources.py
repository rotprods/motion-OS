import pytest

from src.coordination.resources import (
    InvalidResourceURI,
    canonicalize_resource,
    collision_pairs,
    conflicts_with_any,
    resource_overlap,
)


def test_paths_are_canonicalized_before_locking():
    assert canonicalize_resource("file:/src/content/../content/factory.py").uri == "file:src/content/factory.py"
    assert canonicalize_resource("tree:src/content/**").uri == "tree:src/content"
    assert canonicalize_resource(r"file:src\content\factory.py").uri == "file:src/content/factory.py"


def test_path_escape_and_unknown_kind_fail_closed():
    with pytest.raises(InvalidResourceURI):
        canonicalize_resource("file:../../secret")
    with pytest.raises(InvalidResourceURI):
        canonicalize_resource("magic:all")


def test_tree_file_and_nested_tree_overlap():
    tree = canonicalize_resource("tree:src/content/**")
    file = canonicalize_resource("file:src/content/factory.py")
    nested = canonicalize_resource("tree:src/content/providers/**")
    other = canonicalize_resource("file:runtime/remotion/index.ts")
    assert resource_overlap(tree, file)
    assert resource_overlap(tree, nested)
    assert not resource_overlap(tree, other)


def test_semantic_contracts_only_overlap_on_exact_canonical_identity():
    assert resource_overlap(
        canonicalize_resource("contract:avatar-handoff"),
        canonicalize_resource("contract:avatar-handoff"),
    )
    assert not resource_overlap(
        canonicalize_resource("contract:avatar-handoff"),
        canonicalize_resource("contract:studio-entry"),
    )


def test_requested_scope_detects_active_tree_collision():
    conflicts = conflicts_with_any(
        ["file:src/content/content_factory.py", "contract:studio-entry"],
        ["tree:src/content/**", "contract:avatar-handoff"],
    )
    assert conflicts == (("file:src/content/content_factory.py", "tree:src/content"),)


def test_collision_pairs_exposes_self_overlapping_declared_scopes():
    pairs = collision_pairs([
        "tree:src/content/**",
        "file:src/content/content_factory.py",
        "file:runtime/remotion/index.ts",
    ])
    assert pairs == (("file:src/content/content_factory.py", "tree:src/content"),)
