from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping


class TaskState(str, Enum):
    PLANNED = "PLANNED"
    READY = "READY"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class PlanningTask:
    task_id: str
    phase_id: str
    state: TaskState
    depends_on: tuple[str, ...] = ()
    owner_workstream: str | None = None
    checkpoint_id: str | None = None

    def __post_init__(self) -> None:
        if not self.task_id.startswith("motion://task/"):
            raise ValueError("task_id must be canonical")
        if not self.phase_id.startswith("motion://phase/"):
            raise ValueError("phase_id must be canonical")
        if self.task_id in self.depends_on:
            raise ValueError("task cannot depend on itself")


class PlanningGraph:
    """Deterministic DAG for North-Star → phase → task execution readiness."""

    def __init__(self, tasks: Iterable[PlanningTask]) -> None:
        ordered = tuple(sorted(tasks, key=lambda item: item.task_id))
        self._tasks = {task.task_id: task for task in ordered}
        if len(self._tasks) != len(ordered):
            raise ValueError("duplicate task_id")
        for task in ordered:
            missing = sorted(dep for dep in task.depends_on if dep not in self._tasks)
            if missing:
                raise ValueError(f"task {task.task_id} has missing dependencies: {missing}")
        cycle = self.detect_cycle()
        if cycle:
            raise ValueError(f"planning graph contains cycle: {' -> '.join(cycle)}")

    @classmethod
    def from_mappings(cls, rows: Iterable[Mapping[str, object]]) -> "PlanningGraph":
        tasks = []
        for row in rows:
            tasks.append(PlanningTask(
                task_id=str(row["task_id"]),
                phase_id=str(row["phase_id"]),
                state=TaskState(str(row.get("state", "PLANNED"))),
                depends_on=tuple(sorted(str(x) for x in row.get("depends_on", ()) or ())),
                owner_workstream=str(row["owner_workstream"]) if row.get("owner_workstream") else None,
                checkpoint_id=str(row["checkpoint_id"]) if row.get("checkpoint_id") else None,
            ))
        return cls(tasks)

    def detect_cycle(self) -> tuple[str, ...]:
        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []

        def visit(task_id: str) -> tuple[str, ...] | None:
            if task_id in visiting:
                start = stack.index(task_id)
                return tuple(stack[start:] + [task_id])
            if task_id in visited:
                return None
            visiting.add(task_id)
            stack.append(task_id)
            for dep in self._tasks[task_id].depends_on:
                cycle = visit(dep)
                if cycle:
                    return cycle
            stack.pop()
            visiting.remove(task_id)
            visited.add(task_id)
            return None

        for task_id in sorted(self._tasks):
            cycle = visit(task_id)
            if cycle:
                return cycle
        return ()

    def ready_tasks(self) -> tuple[PlanningTask, ...]:
        ready: list[PlanningTask] = []
        for task in self._tasks.values():
            if task.state not in {TaskState.PLANNED, TaskState.READY}:
                continue
            if all(self._tasks[dep].state in {TaskState.DONE, TaskState.SUPERSEDED} for dep in task.depends_on):
                ready.append(task)
        return tuple(sorted(ready, key=lambda item: item.task_id))

    def blockers_for(self, task_id: str) -> tuple[PlanningTask, ...]:
        task = self._tasks[task_id]
        blockers = [
            self._tasks[dep]
            for dep in task.depends_on
            if self._tasks[dep].state not in {TaskState.DONE, TaskState.SUPERSEDED}
        ]
        return tuple(sorted(blockers, key=lambda item: item.task_id))

    def downstream_impact(self, task_id: str) -> tuple[PlanningTask, ...]:
        impacted: set[str] = set()
        frontier = [task_id]
        while frontier:
            current = frontier.pop()
            for candidate in self._tasks.values():
                if current in candidate.depends_on and candidate.task_id not in impacted:
                    impacted.add(candidate.task_id)
                    frontier.append(candidate.task_id)
        return tuple(self._tasks[item] for item in sorted(impacted))

    def phase_progress(self, phase_id: str) -> tuple[int, int]:
        phase = [task for task in self._tasks.values() if task.phase_id == phase_id]
        done = sum(task.state in {TaskState.DONE, TaskState.SUPERSEDED} for task in phase)
        return done, len(phase)
