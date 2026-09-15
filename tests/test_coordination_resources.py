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


def test_semantic_coordination_namespaces_are_first_class_resources():
    assert canonicalize_resource("architecture:event-fabric").uri == "architecture:event-fabric"
    assert canonicalize_resource("adr:008").uri == "adr:008"
    assert canonicalize_resource("root-cause:qa-history-collision").uri == "root-cause:qa-history-collision"
    assert canonicalize_resource("authority:release").uri == "authority:release"


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


def test_semantic_namespace_collision_is_detectable_without_path_overlap():
    assert resource_overlap(
        canonicalize_resource("adr:008"),
        canonicalize_resource("adr:008"),
    )
    assert resource_overlap(
        canonicalize_resource("root-cause:qa-history-collision"),
        canonicalize_resource("root-cause:qa-history-collision"),
    )


def test_requested_scope_detects_active_tree_collision():
    conflicts = conflicts_with_any(
        ["file:src/content/content_factory.py", "contract:studio-entry"],
        ["tree:src/content/**", "contract:avatar-handoff"],
    )
    assert conflicts == (("file:src/content/content_factory.py", "tree:src/content"),)


def test_requested_scope_detects_semantic_collision_with_disjoint_files():
    conflicts = conflicts_with_any(
        ["file:architecture/ADR_009.md", "root-cause:qa-history-collision"],
        ["file:src/qa/graph_critic.py", "root-cause:qa-history-collision"],
    )
    assert conflicts == (("root-cause:qa-history-collision", "root-cause:qa-history-collision"),)


def test_collision_pairs_exposes_self_overlapping_declared_scopes():
    pairs = collision_pairs([
        "tree:src/content/**",
        "file:src/content/content_factory.py",
        "file:runtime/remotion/index.ts",
    ])
    assert pairs == (("file:src/content/content_factory.py", "tree:src/content"),)
