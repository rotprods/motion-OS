from src.coordination.conflicts import ConflictClass, classify_conflict


def test_tree_file_overlap_is_path_overlap():
    finding = classify_conflict(
        requested_scopes=["tree:src/content/**"],
        active_scopes=["file:src/content/foo.py"],
    )
    assert finding.classification == ConflictClass.PATH_OVERLAP
    assert not finding.blocked


def test_same_semantic_contract_is_blocking_overlap_even_with_different_files():
    finding = classify_conflict(
        requested_scopes=["contract:avatar-handoff", "file:src/a.py"],
        active_scopes=["contract:avatar-handoff", "file:src/b.py"],
    )
    assert finding.classification == ConflictClass.SEMANTIC_OVERLAP
    assert finding.blocked


def test_dependency_risk_detected_without_direct_overlap():
    finding = classify_conflict(
        requested_scopes=["contract:studio-entry"],
        active_scopes=["contract:avatar-handoff"],
        dependency_edges={"contract:studio-entry": ["contract:avatar-handoff"]},
    )
    assert finding.classification == ConflictClass.DEPENDENCY_RISK
    assert not finding.blocked


def test_authority_conflict_has_highest_precedence():
    finding = classify_conflict(
        requested_scopes=["file:src/a.py"],
        active_scopes=["file:src/b.py"],
        requested_authority=["capability:render-authority"],
        active_authority=["capability:render-authority"],
    )
    assert finding.classification == ConflictClass.AUTHORITY_CONFLICT
    assert finding.blocked


def test_no_overlap_is_none():
    finding = classify_conflict(
        requested_scopes=["file:src/a.py", "contract:a"],
        active_scopes=["file:src/b.py", "contract:b"],
    )
    assert finding.classification == ConflictClass.NONE
