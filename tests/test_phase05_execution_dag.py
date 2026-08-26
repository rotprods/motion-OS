from src.graph.editing_graph import TypedEditingGraph
from src.graph.impact import descendant_invalidation, assert_invalidated, assert_preserved
from src.graph.model import Edge
from src.graph.scheduler import build_execution_plan, scheduler_from_plan


def build_pipeline_graph():
    g = TypedEditingGraph('pipeline_g', 'project_01')
    for node_id, kind in [
        ('source', 'Asset'),
        ('style', 'StyleSignature'),
        ('type', 'TypographyRole'),
        ('layer', 'Layer'),
        ('composition', 'Composition'),
        ('renderer', 'Renderer'),
    ]:
        g.add_node(g.typed_node(node_id, kind, provenance_refs=['fixture']))

    # style depends on source evidence
    g.add_edge(Edge('style', 'source', 'DERIVED_FROM', {'id': 'e_style_source'}))
    # layer depends on style and typography
    g.add_edge(Edge('layer', 'style', 'CONSTRAINED_BY', {'id': 'e_layer_style'}))
    g.add_edge(Edge('layer', 'type', 'USES', {'id': 'e_layer_type'}))
    # composition is compiled from layer; renderer is backend dependency
    g.add_edge(Edge('layer', 'composition', 'COMPILES_TO', {'id': 'e_compile'}))
    g.add_edge(Edge('composition', 'renderer', 'RENDERED_BY', {'id': 'e_render'}))
    return g


def test_typography_mutation_does_not_invalidate_source_or_style_extraction():
    g = build_pipeline_graph()
    impact = descendant_invalidation(g, ['type'])
    assert_invalidated(impact, 'type', 'layer', 'composition')
    assert_preserved(impact, 'source', 'style')


def test_source_mutation_invalidates_downstream_style_layer_and_composition():
    g = build_pipeline_graph()
    impact = descendant_invalidation(g, ['source'])
    assert_invalidated(impact, 'source', 'style', 'layer', 'composition')
    assert_preserved(impact, 'type', 'renderer')


def test_renderer_change_invalidates_composition_but_not_semantic_or_asset_evidence():
    g = build_pipeline_graph()
    impact = descendant_invalidation(g, ['renderer'])
    assert_invalidated(impact, 'renderer', 'composition')
    assert_preserved(impact, 'source', 'style', 'type')


def test_execution_plan_respects_requires_dependency_and_is_deterministic():
    g = TypedEditingGraph('exec_g', 'project_01')
    for node_id, kind in [('extract', 'Skill'), ('normalize', 'Skill'), ('compile', 'Skill')]:
        g.add_node(g.typed_node(node_id, kind, authority='measured'))
    # source node depends on target node for REQUIRES/DEPENDS_ON semantics.
    g.add_edge(Edge('normalize', 'extract', 'REQUIRES', {'id': 'd1'}))
    g.add_edge(Edge('compile', 'normalize', 'DEPENDS_ON', {'id': 'd2'}))

    plan_a = build_execution_plan(g, executable_kinds={'Skill'}, runtime_inputs={'runtime': 'ci'})
    plan_b = build_execution_plan(g, executable_kinds={'Skill'}, runtime_inputs={'runtime': 'ci'})
    assert plan_a.node_order() == ('extract', 'normalize', 'compile')
    assert plan_a == plan_b
    assert len({step.cache_key for step in plan_a.steps}) == 3

    scheduler = scheduler_from_plan(plan_a)
    assert [job.id for job in scheduler.ready()] == ['extract']
    scheduler.mark('extract', 'DONE')
    assert [job.id for job in scheduler.ready()] == ['normalize']


def test_cache_key_changes_when_runtime_input_changes():
    g = TypedEditingGraph('exec_g2', 'project_01')
    g.add_node(g.typed_node('render', 'Skill', data={'renderer': 'remotion'}))
    a = build_execution_plan(g, executable_kinds={'Skill'}, runtime_inputs={'renderer_version': '1'})
    b = build_execution_plan(g, executable_kinds={'Skill'}, runtime_inputs={'renderer_version': '2'})
    assert a.steps[0].cache_key != b.steps[0].cache_key
