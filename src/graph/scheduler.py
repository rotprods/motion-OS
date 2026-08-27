from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json


@dataclass
class Job:
    id: str
    kind: str
    status: str
    priority: int
    deps: list[str]
    payload: dict


class GraphScheduler:
    def __init__(self):
        self.jobs = {}

    def add(self, j):
        if j.id in self.jobs:
            raise ValueError(f'Duplicate job {j.id}')
        self.jobs[j.id] = j

    def ready(self):
        done = {i for i, j in self.jobs.items() if j.status == 'DONE'}
        return sorted(
            [j for j in self.jobs.values() if j.status == 'PENDING' and set(j.deps) <= done],
            key=lambda j: (-j.priority, j.id),
        )

    def mark(self, i, status):
        self.jobs[i].status = status

    def to_dict(self):
        return {'jobs': [asdict(j) for j in self.jobs.values()]}


EXECUTION_DEPENDENCY_RELATIONS = frozenset({'REQUIRES', 'DEPENDS_ON'})


@dataclass(frozen=True)
class ExecutionStep:
    node_id: str
    kind: str
    deps: tuple[str, ...]
    cache_key: str


@dataclass(frozen=True)
class ExecutionPlan:
    graph_hash: str
    steps: tuple[ExecutionStep, ...]

    def node_order(self) -> tuple[str, ...]:
        return tuple(step.node_id for step in self.steps)


def _stable_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str)


def stable_cache_key(node, *, upstream_keys: list[str], runtime_inputs: dict | None = None) -> str:
    payload = {
        'node_id': node.id,
        'kind': node.kind,
        'attrs': node.attrs,
        'upstream_keys': sorted(upstream_keys),
        'runtime_inputs': runtime_inputs or {},
    }
    return sha256(_stable_json(payload).encode('utf-8')).hexdigest()


def _project_scheduler_dependencies(
    node_id: str,
    *,
    deps: dict[str, set[str]],
    executable_ids: set[str],
    memo: dict[str, frozenset[str]],
) -> frozenset[str]:
    """Project full graph dependencies onto executable scheduler jobs.

    Non-executable nodes still participate in graph ordering and cache keys, but
    they never become scheduler jobs. A direct dependency on such a node must
    therefore resolve to its nearest executable prerequisites (if any), rather
    than leaving an impossible dependency on a job that cannot reach DONE.
    """
    if node_id in memo:
        return memo[node_id]

    projected: set[str] = set()
    for requirement in deps[node_id]:
        if requirement in executable_ids:
            projected.add(requirement)
        else:
            projected.update(
                _project_scheduler_dependencies(
                    requirement,
                    deps=deps,
                    executable_ids=executable_ids,
                    memo=memo,
                )
            )
    result = frozenset(projected)
    memo[node_id] = result
    return result


def build_execution_plan(
    graph,
    *,
    executable_kinds: set[str] | None = None,
    dependency_relations=EXECUTION_DEPENDENCY_RELATIONS,
    runtime_inputs: dict | None = None,
) -> ExecutionPlan:
    """Build a deterministic execution plan from graph dependencies.

    Dependency semantics:
    - `A REQUIRES B`: A depends on B, therefore B executes before A.
    - `A DEPENDS_ON B`: A depends on B, therefore B executes before A.

    Other editing/semantic relations do not automatically become execution
    dependencies; they are handled by impact/invalidation and compiler logic.

    When `executable_kinds` filters the graph, non-executable dependency nodes
    remain part of ordering/cache state but are projected out of scheduler deps.
    Any executable prerequisites behind them are preserved transitively.
    """
    allowed = set(dependency_relations)
    ids = {node.id for node in graph.nodes}
    deps: dict[str, set[str]] = {node_id: set() for node_id in ids}
    for edge in graph.edges:
        if edge.kind not in allowed:
            continue
        if edge.source not in ids or edge.target not in ids:
            raise ValueError(f'Execution dependency references missing node: {edge.source}->{edge.target}')
        deps[edge.source].add(edge.target)

    indegree = {node_id: len(values) for node_id, values in deps.items()}
    reverse: dict[str, set[str]] = {node_id: set() for node_id in ids}
    for node_id, requirements in deps.items():
        for requirement in requirements:
            reverse[requirement].add(node_id)

    ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    ordered: list[str] = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(node_id)
        for dependent in sorted(reverse[node_id]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort()
    if len(ordered) != len(ids):
        cyclic = sorted(node_id for node_id, degree in indegree.items() if degree > 0)
        raise ValueError(f'Execution dependency cycle detected: {cyclic}')

    executable_ids = {
        node_id
        for node_id in ordered
        if executable_kinds is None or graph.node(node_id).kind in executable_kinds
    }
    scheduler_dep_memo: dict[str, frozenset[str]] = {}

    cache_by_node: dict[str, str] = {}
    steps: list[ExecutionStep] = []
    for node_id in ordered:
        node = graph.node(node_id)
        upstream = [cache_by_node[d] for d in sorted(deps[node_id])]
        key = stable_cache_key(node, upstream_keys=upstream, runtime_inputs=runtime_inputs)
        cache_by_node[node_id] = key
        if node_id in executable_ids:
            scheduler_deps = _project_scheduler_dependencies(
                node_id,
                deps=deps,
                executable_ids=executable_ids,
                memo=scheduler_dep_memo,
            )
            steps.append(
                ExecutionStep(
                    node_id=node_id,
                    kind=node.kind,
                    deps=tuple(sorted(scheduler_deps)),
                    cache_key=key,
                )
            )

    graph_hash_source = getattr(graph, 'content_hash', None)
    graph_hash = graph_hash_source() if callable(graph_hash_source) else sha256(
        _stable_json({'nodes': sorted(ids), 'edges': sorted((e.source, e.kind, e.target) for e in graph.edges)}).encode('utf-8')
    ).hexdigest()
    return ExecutionPlan(graph_hash=graph_hash, steps=tuple(steps))


def scheduler_from_plan(plan: ExecutionPlan, *, priority_by_kind: dict[str, int] | None = None) -> GraphScheduler:
    priorities = priority_by_kind or {}
    scheduler = GraphScheduler()
    planned_ids = {step.node_id for step in plan.steps}
    for step in plan.steps:
        unknown_deps = set(step.deps) - planned_ids
        if unknown_deps:
            raise ValueError(f'Execution plan contains unschedulable dependencies for {step.node_id}: {sorted(unknown_deps)}')
        scheduler.add(
            Job(
                id=step.node_id,
                kind=step.kind,
                status='PENDING',
                priority=int(priorities.get(step.kind, 0)),
                deps=list(step.deps),
                payload={'cache_key': step.cache_key, 'graph_hash': plan.graph_hash},
            )
        )
    return scheduler
