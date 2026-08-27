import pytest

from src.coordination.planning import PlanningGraph, PlanningTask, TaskState


def task(name, phase, state, deps=()):
    return PlanningTask(
        task_id=f"motion://task/{name}",
        phase_id=f"motion://phase/{phase}",
        state=state,
        depends_on=tuple(f"motion://task/{dep}" for dep in deps),
    )


def test_ready_tasks_require_dependencies_done_or_superseded():
    graph = PlanningGraph([
        task("p0", "07-p0", TaskState.DONE),
        task("p1", "07-p1", TaskState.PLANNED, ("p0",)),
        task("p2", "07-p2", TaskState.PLANNED, ("p1",)),
    ])
    assert [item.task_id for item in graph.ready_tasks()] == ["motion://task/p1"]
    assert [item.task_id for item in graph.blockers_for("motion://task/p2")] == ["motion://task/p1"]


def test_downstream_impact_is_transitive_and_deterministic():
    graph = PlanningGraph([
        task("a", "x", TaskState.DONE),
        task("b", "x", TaskState.PLANNED, ("a",)),
        task("c", "x", TaskState.PLANNED, ("b",)),
        task("d", "x", TaskState.PLANNED, ("a",)),
    ])
    assert [item.task_id for item in graph.downstream_impact("motion://task/a")] == [
        "motion://task/b", "motion://task/c", "motion://task/d"
    ]


def test_cycle_fails_closed():
    with pytest.raises(ValueError, match="contains cycle"):
        PlanningGraph([
            task("a", "x", TaskState.PLANNED, ("b",)),
            task("b", "x", TaskState.PLANNED, ("a",)),
        ])


def test_phase_progress_keeps_denominator_visible():
    graph = PlanningGraph([
        task("a", "p", TaskState.DONE),
        task("b", "p", TaskState.SUPERSEDED),
        task("c", "p", TaskState.ACTIVE),
    ])
    assert graph.phase_progress("motion://phase/p") == (2, 3)
