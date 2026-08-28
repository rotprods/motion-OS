from scripts.change_impact import classify


def test_regular_readme_change_does_not_trigger_expensive_gates():
    result = classify(["README.md"])
    assert result == {"analysis": False, "remotion": False, "security": False, "full": False}


def test_analysis_change_routes_to_analysis_only():
    result = classify(["src/extraction/pipeline.py"])
    assert result["analysis"] is True
    assert result["remotion"] is False
    assert result["full"] is False


def test_remotion_change_routes_to_remotion():
    result = classify(["runtime/remotion/src/Root.tsx"])
    assert result["remotion"] is True
    assert result["analysis"] is False


def test_dependency_change_routes_to_security_and_analysis_when_pyproject():
    result = classify(["pyproject.toml"])
    assert result["security"] is True
    assert result["analysis"] is True


def test_ci_policy_change_forces_every_gate():
    result = classify([".github/workflows/merge-gate.yml"])
    assert result == {"analysis": True, "remotion": True, "security": True, "full": True}


def test_canonical_truth_changes_force_every_gate():
    for path in [
        "STATE.md",
        "TASKS.md",
        "HANDOFF.md",
        "state/project_state.json",
        "state/checkpoints.json",
        "coordination/ACTIVE_AGENTS.yaml",
        "src/qa/alignment.py",
        "config/alignment_weights.json",
    ]:
        result = classify([path])
        assert all(result.values()), (path, result)


def test_force_full_for_merge_group_forces_every_gate():
    result = classify(["README.md"], force_full=True)
    assert all(result.values())
