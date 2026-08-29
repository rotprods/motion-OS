#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = (
    "architecture/v2/EXECUTIVE_V2.md",
    "architecture/v2/GAP_RISK_MATRIX.md",
    "architecture/v2/DECISION_LEDGER.md",
    "architecture/v2/LEXICON.md",
    "architecture/v2/IMPLEMENTATION_PROGRAM.md",
    "architecture/v2/CHECKPOINTS.md",
    "architecture/v2/ASSURANCE_MODEL.md",
    "architecture/v2/system_graph.mmd",
    "architecture/v2/hypergraph.snapshot.json",
    "state/v2/project-state.json",
    "state/v2/tasks.json",
    "state/v2/checkpoint.json",
)

ALLOWED_AUTHORITY = {
    "PROPOSED_V2_CANDIDATE",
    "SESSION_EVIDENCE",
    "BRANCH_ONLY",
    "NOT_PROMOTED",
    "NONE",
}


def _load_json(rel: str, root: Path = ROOT) -> dict[str, Any]:
    path = root / rel
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {rel}: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{rel} must contain a JSON object")
    return value


def _assert_unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        duplicates = sorted({v for v in values if values.count(v) > 1})
        raise ValueError(f"duplicate {label}: {duplicates}")


def validate_hypergraph(root: Path = ROOT) -> None:
    graph = _load_json("architecture/v2/hypergraph.snapshot.json", root)
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    hyperedges = graph.get("hyperedges")
    if not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(hyperedges, list):
        raise ValueError("hypergraph nodes/edges/hyperedges must be arrays")

    node_ids: list[str] = []
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"].strip():
            raise ValueError("every hypergraph node requires a non-empty string id")
        node_ids.append(node["id"])
    _assert_unique(node_ids, "node ids")
    node_set = set(node_ids)

    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("edge must be an object")
        source = edge.get("from")
        target = edge.get("to")
        if source not in node_set or target not in node_set:
            raise ValueError(f"dangling edge: {source!r} -> {target!r}")
        if not isinstance(edge.get("type"), str) or not edge["type"].strip():
            raise ValueError("edge type must be non-empty")

    hyper_ids: list[str] = []
    for hyperedge in hyperedges:
        if not isinstance(hyperedge, dict):
            raise ValueError("hyperedge must be an object")
        hid = hyperedge.get("id")
        if not isinstance(hid, str) or not hid.strip():
            raise ValueError("hyperedge id must be non-empty")
        hyper_ids.append(hid)
        members = hyperedge.get("members", [])
        if not isinstance(members, list) or not members:
            raise ValueError(f"hyperedge {hid} requires members")
        missing = [member for member in members if member not in node_set]
        if missing:
            raise ValueError(f"hyperedge {hid} references missing nodes: {missing}")
        outcome = hyperedge.get("outcome")
        if outcome is not None and outcome not in node_set:
            raise ValueError(f"hyperedge {hid} outcome references missing node: {outcome}")
    _assert_unique(hyper_ids, "hyperedge ids")


def validate_tasks(root: Path = ROOT) -> None:
    payload = _load_json("state/v2/tasks.json", root)
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks.json requires a non-empty tasks array")
    task_ids: list[str] = []
    graph: dict[str, tuple[str, ...]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("task must be an object")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task id must be non-empty")
        task_ids.append(task_id)
        deps = task.get("depends_on", [])
        if not isinstance(deps, list) or not all(isinstance(dep, str) for dep in deps):
            raise ValueError(f"task {task_id} has invalid depends_on")
        if task_id in deps:
            raise ValueError(f"task {task_id} depends on itself")
        graph[task_id] = tuple(deps)
        if not task.get("dod") or not task.get("evidence"):
            raise ValueError(f"task {task_id} requires dod and evidence")
    _assert_unique(task_ids, "task ids")
    ids = set(task_ids)
    for task_id, deps in graph.items():
        missing = [dep for dep in deps if dep not in ids]
        if missing:
            raise ValueError(f"task {task_id} has missing dependencies: {missing}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            raise ValueError(f"task dependency cycle includes {task_id}")
        visiting.add(task_id)
        for dep in graph[task_id]:
            visit(dep)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in task_ids:
        visit(task_id)


def validate_checkpoint(root: Path = ROOT) -> None:
    payload = _load_json("state/v2/checkpoint.json", root)
    states = payload.get("checkpoint_states")
    if not isinstance(states, dict):
        raise ValueError("checkpoint_states must be an object")
    expected = {f"CP{i}" for i in range(15)}
    if set(states) != expected:
        raise ValueError(f"checkpoint set mismatch: expected {sorted(expected)}, got {sorted(states)}")
    next_target = payload.get("next_checkpoint_target")
    if next_target not in expected:
        raise ValueError("next_checkpoint_target must reference a known checkpoint")
    for checkpoint_id, checkpoint in states.items():
        if not isinstance(checkpoint, dict) or not checkpoint.get("name") or not checkpoint.get("state"):
            raise ValueError(f"checkpoint {checkpoint_id} requires name and state")
        authority = checkpoint.get("authority")
        if authority not in ALLOWED_AUTHORITY:
            raise ValueError(f"checkpoint {checkpoint_id} has unknown authority {authority!r}")


def validate_package(root: Path = ROOT) -> dict[str, Any]:
    missing = [rel for rel in REQUIRED_DOCS if not (root / rel).is_file()]
    if missing:
        raise ValueError(f"missing V2 package files: {missing}")
    validate_hypergraph(root)
    validate_tasks(root)
    validate_checkpoint(root)
    project_state = _load_json("state/v2/project-state.json", root)
    if project_state.get("authority") != "PROPOSED_V2_CANDIDATE":
        raise ValueError("V2 project-state must not self-promote before migration")
    if project_state.get("release_state") != "BLOCKED":
        raise ValueError("V2 project-state must remain BLOCKED while production checkpoints are incomplete")
    return {
        "schema": "motion-os.v2-package-validation/v1",
        "status": "PASS",
        "source_main_sha": project_state.get("source_main_sha"),
        "documents": list(REQUIRED_DOCS),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the MOTION.OS V2 architecture package")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = validate_package(args.root.resolve())
    except ValueError as exc:
        print(json.dumps({"schema": "motion-os.v2-package-validation/v1", "status": "FAIL", "reason": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
