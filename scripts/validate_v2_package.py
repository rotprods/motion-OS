#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_v2_hypergraph import validate as validate_hypergraph

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "architecture/v2/README.md",
    "architecture/v2/EXECUTIVE_V2.md",
    "architecture/v2/ARCHITECTURE_DELTA.md",
    "architecture/v2/DECISION_LEDGER.md",
    "architecture/v2/LEXICON.md",
    "architecture/v2/CHECKPOINTS.md",
    "architecture/v2/DEFINITION_OF_DONE.md",
    "architecture/v2/GRAPH_PROJECTIONS.md",
    "architecture/v2/MIGRATION_PLAN.md",
    "architecture/v2/ASSURANCE_RECOVERY_SECURITY.md",
    "plans/v2/GAP_RISK_MATRIX.md",
    "plans/v2/IMPLEMENTATION_PROGRAM.md",
    "plans/v2/NEXT_ITERATION_METAPROMPT.md",
    "graph/v2/motion_os_v2_hypergraph.json",
    "state/v2/v2_state.json",
    "state/v2/task_dag.json",
]


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED:
        if not (root / rel).is_file():
            errors.append(f"package:missing:{rel}")

    if errors:
        return errors

    errors.extend(validate_hypergraph(root / "schemas/v2_hypergraph.schema.json", root / "graph/v2/motion_os_v2_hypergraph.json"))

    state = _load(root / "state/v2/v2_state.json")
    dag = _load(root / "state/v2/task_dag.json")
    source = state.get("source", {}).get("main_sha")
    if source != dag.get("source_revision"):
        errors.append("package:source_revision_mismatch")
    if not state.get("promotion", {}).get("blocked"):
        errors.append("authority:v2_state_must_remain_blocked_before_cp14")

    tasks = dag.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("dag:tasks_missing")
        return errors
    ids = [t.get("id") for t in tasks if isinstance(t, dict)]
    if len(ids) != len(tasks) or len(ids) != len(set(ids)):
        errors.append("dag:duplicate_or_invalid_ids")
        return errors
    known = set(ids)
    graph: dict[str, list[str]] = {}
    for task in tasks:
        tid = task["id"]
        deps = task.get("depends_on", [])
        if not isinstance(deps, list) or any(dep not in known for dep in deps):
            errors.append(f"dag:{tid}:missing_dependency")
        if tid in deps:
            errors.append(f"dag:{tid}:self_dependency")
        for field in ("objective", "owner", "tests", "evidence", "dod"):
            if not task.get(field):
                errors.append(f"dag:{tid}:missing_{field}")
        graph[tid] = deps

    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(tid: str) -> None:
        if tid in visited:
            return
        if tid in visiting:
            errors.append(f"dag:cycle:{tid}")
            return
        visiting.add(tid)
        for dep in graph.get(tid, []):
            visit(dep)
        visiting.remove(tid)
        visited.add(tid)
    for tid in ids:
        visit(tid)

    return errors


if __name__ == "__main__":
    found = validate()
    if found:
        print("\n".join(found))
        raise SystemExit(1)
    print("MOTION.OS V2 package valid")
