from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from src.graph.model import Edge
from src.skills.registry import CapabilityInventory, SkillRegistry


@dataclass(frozen=True)
class SkillInvocation:
    invocation_id: str
    skill_id: str
    depends_on: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)
    min_authority: str | None = None


@dataclass(frozen=True)
class SkillExecutionRecord:
    invocation_id: str
    requested_skill_id: str
    selected_skill_id: str | None
    fallback_chain: tuple[str, ...]
    status: str
    reason: str
    dependency_ids: tuple[str, ...]
    result_summary: Any = None


@dataclass(frozen=True)
class SkillExecutionTrace:
    run_id: str
    records: tuple[SkillExecutionRecord, ...]

    @property
    def ok(self) -> bool:
        return bool(self.records) and all(record.status == 'DONE' for record in self.records)


class SkillExecutionError(RuntimeError):
    """Strict-mode executor failure that preserves a persistable execution trace."""

    def __init__(self, reason: str, trace: SkillExecutionTrace):
        super().__init__(reason)
        self.trace = trace


class SkillRuntime:
    def __init__(self, registry: SkillRegistry, inventory: CapabilityInventory):
        self.registry = registry
        self.inventory = inventory
        self.executors: dict[str, Callable[[dict[str, Any], dict[str, Any]], Any]] = {}

    def register_executor(self, skill_id: str, executor: Callable[[dict[str, Any], dict[str, Any]], Any]) -> None:
        self.registry.get(skill_id)
        self.executors[skill_id] = executor

    @staticmethod
    def _topological_order(invocations: tuple[SkillInvocation, ...]) -> tuple[SkillInvocation, ...]:
        by_id = {item.invocation_id: item for item in invocations}
        if len(by_id) != len(invocations):
            raise ValueError('duplicate invocation_id')
        for item in invocations:
            missing = set(item.depends_on) - set(by_id)
            if missing:
                raise ValueError(f'{item.invocation_id} depends on missing invocations: {sorted(missing)}')
        indegree = {item.invocation_id: len(item.depends_on) for item in invocations}
        reverse = {item.invocation_id: set() for item in invocations}
        for item in invocations:
            for dependency in item.depends_on:
                reverse[dependency].add(item.invocation_id)
        ready = sorted(invocation_id for invocation_id, degree in indegree.items() if degree == 0)
        ordered = []
        while ready:
            invocation_id = ready.pop(0)
            ordered.append(by_id[invocation_id])
            for dependent in sorted(reverse[invocation_id]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)
                    ready.sort()
        if len(ordered) != len(invocations):
            cyclic = sorted(invocation_id for invocation_id, degree in indegree.items() if degree > 0)
            raise ValueError(f'skill dependency cycle: {cyclic}')
        return tuple(ordered)

    def run(
        self,
        invocations: tuple[SkillInvocation, ...],
        *,
        run_id: str,
        initial_context: dict[str, Any] | None = None,
        strict: bool = True,
    ) -> tuple[SkillExecutionTrace, dict[str, Any]]:
        order = self._topological_order(invocations)
        context: dict[str, Any] = dict(initial_context or {})
        context.setdefault('outputs', {})
        records: list[SkillExecutionRecord] = []
        status_by_invocation: dict[str, str] = {}

        for invocation in order:
            dependency_failures = [dep for dep in invocation.depends_on if status_by_invocation.get(dep) != 'DONE']
            if dependency_failures:
                record = SkillExecutionRecord(
                    invocation_id=invocation.invocation_id,
                    requested_skill_id=invocation.skill_id,
                    selected_skill_id=None,
                    fallback_chain=(),
                    status='BLOCKED',
                    reason=f'dependency_failed:{dependency_failures}',
                    dependency_ids=invocation.depends_on,
                )
                records.append(record)
                status_by_invocation[invocation.invocation_id] = 'BLOCKED'
                if strict:
                    raise RuntimeError(record.reason)
                continue

            resolution = self.registry.resolve(
                invocation.skill_id,
                self.inventory,
                min_authority=invocation.min_authority,
            )
            if not resolution.ready:
                record = SkillExecutionRecord(
                    invocation_id=invocation.invocation_id,
                    requested_skill_id=invocation.skill_id,
                    selected_skill_id=None,
                    fallback_chain=resolution.fallback_chain,
                    status='BLOCKED',
                    reason=resolution.reason,
                    dependency_ids=invocation.depends_on,
                    result_summary={
                        'missing_capabilities': resolution.missing_capabilities,
                        'missing_tools': resolution.missing_tools,
                        'missing_providers': resolution.missing_providers,
                    },
                )
                records.append(record)
                status_by_invocation[invocation.invocation_id] = 'BLOCKED'
                if strict:
                    raise RuntimeError(f'skill unavailable: {record}')
                continue

            selected_id = resolution.selected_skill_id
            executor = self.executors.get(selected_id)
            if executor is None:
                record = SkillExecutionRecord(
                    invocation_id=invocation.invocation_id,
                    requested_skill_id=invocation.skill_id,
                    selected_skill_id=selected_id,
                    fallback_chain=resolution.fallback_chain,
                    status='BLOCKED',
                    reason=f'executor_missing:{selected_id}',
                    dependency_ids=invocation.depends_on,
                )
                records.append(record)
                status_by_invocation[invocation.invocation_id] = 'BLOCKED'
                if strict:
                    raise RuntimeError(record.reason)
                continue

            local_context = {
                **context,
                'invocation_id': invocation.invocation_id,
                'requested_skill_id': invocation.skill_id,
                'selected_skill_id': selected_id,
                'dependencies': {dep: context['outputs'].get(dep) for dep in invocation.depends_on},
            }
            try:
                result = executor(dict(invocation.payload), local_context)
            except Exception as exc:
                error_type = type(exc).__name__
                reason = f'executor_failed:{selected_id}:{error_type}'
                record = SkillExecutionRecord(
                    invocation_id=invocation.invocation_id,
                    requested_skill_id=invocation.skill_id,
                    selected_skill_id=selected_id,
                    fallback_chain=resolution.fallback_chain,
                    status='FAILED',
                    reason=reason,
                    dependency_ids=invocation.depends_on,
                    result_summary={'error_type': error_type},
                )
                records.append(record)
                status_by_invocation[invocation.invocation_id] = 'FAILED'
                if strict:
                    trace = SkillExecutionTrace(run_id=run_id, records=tuple(records))
                    raise SkillExecutionError(reason, trace) from exc
                continue

            context['outputs'][invocation.invocation_id] = result
            record = SkillExecutionRecord(
                invocation_id=invocation.invocation_id,
                requested_skill_id=invocation.skill_id,
                selected_skill_id=selected_id,
                fallback_chain=resolution.fallback_chain,
                status='DONE',
                reason=resolution.reason,
                dependency_ids=invocation.depends_on,
                result_summary=result,
            )
            records.append(record)
            status_by_invocation[invocation.invocation_id] = 'DONE'

        return SkillExecutionTrace(run_id=run_id, records=tuple(records)), context


def record_execution_trace(graph, trace: SkillExecutionTrace) -> None:
    """Attach runtime evidence to L3 without changing L1/L2 creative intent."""
    run_node_id = f'run:{trace.run_id}'
    existing_ids = {node.id for node in graph.nodes}
    if run_node_id not in existing_ids:
        if trace.ok:
            run_status = 'DONE'
        elif any(record.status == 'FAILED' for record in trace.records):
            run_status = 'FAILED'
        else:
            run_status = 'PARTIAL'
        graph.add_node(graph.typed_node(run_node_id, 'Run', data={'run_id': trace.run_id, 'status': run_status}, authority='measured', provenance_refs=['skill_runtime']))
        existing_ids.add(run_node_id)

    for index, record in enumerate(trace.records):
        skill_name = record.selected_skill_id or record.requested_skill_id
        skill_node_id = f'skill:{skill_name}'
        if skill_node_id not in existing_ids:
            graph.add_node(graph.typed_node(skill_node_id, 'Skill', data={'skill_id': skill_name}, authority='authoritative', provenance_refs=['skill_registry']))
            existing_ids.add(skill_node_id)
        tool_call_id = f'toolcall:{trace.run_id}:{record.invocation_id}'
        if tool_call_id not in existing_ids:
            graph.add_node(graph.typed_node(tool_call_id, 'ToolCall', data={
                'invocation_id': record.invocation_id,
                'requested_skill_id': record.requested_skill_id,
                'selected_skill_id': record.selected_skill_id,
                'fallback_chain': list(record.fallback_chain),
                'status': record.status,
                'reason': record.reason,
            }, authority='measured', provenance_refs=[run_node_id]))
            existing_ids.add(tool_call_id)
        graph.add_edge(Edge(run_node_id, skill_node_id, 'REQUIRES_SKILL', {'id': f'e_{trace.run_id}_{index}_skill'}))
        graph.add_edge(Edge(tool_call_id, run_node_id, 'PRODUCED_BY', {'id': f'e_{trace.run_id}_{index}_run'}))
        graph.add_edge(Edge(tool_call_id, skill_node_id, 'REQUIRES_SKILL', {'id': f'e_{trace.run_id}_{index}_call_skill'}))
