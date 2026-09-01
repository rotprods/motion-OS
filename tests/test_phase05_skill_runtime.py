import pytest

from src.graph.editing_graph import TypedEditingGraph
from src.skills.registry import CapabilityInventory, SkillRegistry, SkillSpec
from src.skills.runtime import SkillExecutionError, SkillInvocation, SkillRuntime, record_execution_trace


def build_registry():
    registry = SkillRegistry()
    registry.register(SkillSpec(
        skill_id='extract_video',
        version='1.0.0',
        requires=('ffmpeg',),
        tools=('ffmpeg',),
        authority='measured',
        deterministic=True,
        failure_modes=('ffmpeg_unavailable',),
        qa=('feature_pack_valid',),
    ))
    registry.register(SkillSpec(
        skill_id='reference_search_pinterest',
        version='1.0.0',
        providers=('pinterest',),
        authority='evidence_only',
        deterministic=False,
        failure_modes=('provider_unavailable',),
        fallbacks=('reference_search_local',),
        qa=('provenance_complete',),
    ))
    registry.register(SkillSpec(
        skill_id='reference_search_local',
        version='1.0.0',
        providers=('local',),
        authority='evidence_only',
        deterministic=True,
        failure_modes=(),
        qa=('provenance_complete',),
    ))
    registry.register(SkillSpec(
        skill_id='normalize_style',
        version='1.0.0',
        authority='inferred',
        deterministic=True,
        failure_modes=(),
        qa=('schema_valid',),
    ))
    return registry


def test_registry_uses_explicit_fallback_when_provider_is_missing():
    registry = build_registry()
    inventory = CapabilityInventory.from_iterables(providers=['local'])
    resolution = registry.resolve('reference_search_pinterest', inventory)
    assert resolution.ready is True
    assert resolution.selected_skill_id == 'reference_search_local'
    assert resolution.fallback_chain == ('reference_search_pinterest', 'reference_search_local')


def test_missing_capability_never_silently_passes():
    registry = build_registry()
    inventory = CapabilityInventory.from_iterables()
    resolution = registry.resolve('extract_video', inventory)
    assert resolution.ready is False
    assert resolution.selected_skill_id is None
    assert resolution.missing_capabilities == ('ffmpeg',)
    assert resolution.missing_tools == ('ffmpeg',)


def test_runtime_executes_dependencies_in_order_and_records_fallback():
    registry = build_registry()
    inventory = CapabilityInventory.from_iterables(providers=['local'])
    runtime = SkillRuntime(registry, inventory)
    runtime.register_executor('reference_search_local', lambda payload, ctx: {'refs': ['local_ref'], 'query': payload['query']})
    runtime.register_executor('normalize_style', lambda payload, ctx: {'style': 'editorial_minimal', 'refs': ctx['dependencies']['search']['refs']})

    trace, context = runtime.run((
        SkillInvocation('search', 'reference_search_pinterest', payload={'query': 'premium motion'}),
        SkillInvocation('normalize', 'normalize_style', depends_on=('search',)),
    ), run_id='run_demo')

    assert trace.ok is True
    assert [record.invocation_id for record in trace.records] == ['search', 'normalize']
    assert trace.records[0].selected_skill_id == 'reference_search_local'
    assert context['outputs']['normalize']['refs'] == ['local_ref']

    graph = TypedEditingGraph('runtime_graph', 'project_demo')
    record_execution_trace(graph, trace)
    assert len(graph.query_nodes(kind='Run')) == 1
    assert len(graph.query_nodes(kind='ToolCall')) == 2
    assert len(graph.query_nodes(kind='Skill')) == 2
    assert graph.validate_typed()['ok'] is True


def test_runtime_blocks_downstream_when_dependency_cannot_run_in_non_strict_mode():
    registry = build_registry()
    runtime = SkillRuntime(registry, CapabilityInventory.from_iterables())
    runtime.register_executor('normalize_style', lambda payload, ctx: {'style': 'should_not_run'})
    trace, _ = runtime.run((
        SkillInvocation('extract', 'extract_video'),
        SkillInvocation('normalize', 'normalize_style', depends_on=('extract',)),
    ), run_id='blocked_run', strict=False)
    assert [r.status for r in trace.records] == ['BLOCKED', 'BLOCKED']
    assert trace.ok is False


def test_executor_exception_becomes_failed_trace_and_blocks_downstream_non_strict():
    registry = build_registry()
    runtime = SkillRuntime(registry, CapabilityInventory.from_iterables())

    def explode(payload, ctx):
        raise ValueError('secret-bearing provider response must not enter durable trace')

    runtime.register_executor('normalize_style', explode)
    trace, context = runtime.run((
        SkillInvocation('first', 'normalize_style'),
        SkillInvocation('second', 'normalize_style', depends_on=('first',)),
    ), run_id='failure_non_strict', strict=False)

    assert [record.status for record in trace.records] == ['FAILED', 'BLOCKED']
    assert trace.records[0].reason == 'executor_failed:normalize_style:ValueError'
    assert trace.records[0].result_summary == {'error_type': 'ValueError'}
    assert 'secret-bearing' not in trace.records[0].reason
    assert 'first' not in context['outputs']
    assert trace.ok is False


def test_strict_executor_exception_carries_persistable_failed_trace_without_secret_message():
    registry = build_registry()
    runtime = SkillRuntime(registry, CapabilityInventory.from_iterables())

    def explode(payload, ctx):
        raise RuntimeError('provider-token=do-not-persist')

    runtime.register_executor('normalize_style', explode)

    with pytest.raises(SkillExecutionError) as exc_info:
        runtime.run((SkillInvocation('normalize', 'normalize_style'),), run_id='failure_strict')

    failure = exc_info.value
    assert str(failure) == 'executor_failed:normalize_style:RuntimeError'
    assert 'provider-token' not in str(failure)
    assert len(failure.trace.records) == 1
    assert failure.trace.records[0].status == 'FAILED'
    assert failure.trace.records[0].result_summary == {'error_type': 'RuntimeError'}

    graph = TypedEditingGraph('failed_runtime_graph', 'project_demo')
    record_execution_trace(graph, failure.trace)
    run_node = graph.query_nodes(kind='Run')[0]
    tool_call = graph.query_nodes(kind='ToolCall')[0]
    assert run_node.attrs['data']['status'] == 'FAILED'
    assert tool_call.attrs['data']['status'] == 'FAILED'
    assert 'provider-token' not in tool_call.attrs['data']['reason']
    assert graph.validate_typed()['ok'] is True
