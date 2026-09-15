import pytest

from src.graph.editing_graph import TypedEditingGraph
from src.graph.model import Edge
from src.qa.graph_critic import GraphQAFinding, inspect_graph_contract, attach_findings
from src.qa.graph_repair import (
    RepairCandidateSpec,
    RepairMutation,
    attach_repair_candidates,
    choose_candidate,
    plan_repair_candidates,
    tournament_hash,
)
from src.renderers.multirender import assign_renderers, render_manifest
from src.studio.inspector import inspect_project, recovery_manifest


def fixture_graph():
    g=TypedEditingGraph('g:test','p:test')
    g.add_node(g.typed_node('project','Project',data={'duration_ms':1000},authority='authoritative',provenance_refs=['brief']))
    g.add_node(g.typed_node('beat','NarrativeBeat',data={'start_ms':0,'end_ms':1000},provenance_refs=['brief']))
    g.add_node(g.typed_node('scene','Scene',data={'start_ms':0,'end_ms':1000},provenance_refs=['beat']))
    g.add_node(g.typed_node('hero','Layer',data={'layer_class':'SUBJECT','z':3,'attention_role':'primary','renderer_support':['remotion']},provenance_refs=['scene']))
    g.add_node(g.typed_node('type','Layer',data={'layer_class':'TYPOGRAPHY','z':6,'attention_role':'secondary','renderer_support':['hyperframes','remotion'],'text_integrity':'weak'},provenance_refs=['scene']))
    g.add_edge(Edge('beat','scene','MATERIALIZES_AS',{'id':'e_beat_scene'}))
    g.add_edge(Edge('scene','hero','CONTAINS',{'id':'e_scene_hero'}))
    g.add_edge(Edge('scene','type','CONTAINS',{'id':'e_scene_type'}))
    return g


def test_graph_critic_attaches_defect_and_repair_tournament():
    g=fixture_graph()
    findings=inspect_graph_contract(g)
    assert any(f.code=='TEXT_INTEGRITY_WEAK' for f in findings)
    created=attach_findings(g,findings,run_id='qa:run-a')
    defects=[nid for nid in created if nid.startswith('defect:')]
    assert defects
    candidates=plan_repair_candidates(g,defects[0])
    assert {c.strategy for c in candidates}=={'minimal','structural','renderer_swap'}
    assert tournament_hash(candidates)==tournament_hash(candidates)
    attach_repair_candidates(g,candidates)

    for candidate in candidates:
        mutation_targets={m.target_node_id for m in candidate.mutations}
        actual_mutates={e.target for e in g.edges if e.source==candidate.candidate_id and e.kind=='MUTATES'}
        derived_defects={e.target for e in g.edges if e.source==candidate.candidate_id and e.kind=='DERIVED_FROM'}
        assert actual_mutates==mutation_targets
        assert candidate.defect_id not in actual_mutates
        assert derived_defects=={candidate.defect_id}

    scores={c.candidate_id:(0.95 if c.strategy=='structural' else 0.8) for c in candidates}
    regress={c.candidate_id:True for c in candidates}
    decision=choose_candidate(candidates,scores,regression_pass=regress)
    assert decision['decision']=='PROMOTE'
    assert ':2' in decision['winner']


def test_qa_history_ids_are_run_scoped_and_preserve_both_executions():
    g=fixture_graph()
    findings=inspect_graph_contract(g)
    first=set(attach_findings(g,findings,run_id='qa:run-001'))
    second=set(attach_findings(g,findings,run_id='qa:run-002'))
    assert first and second and first.isdisjoint(second)
    assert all('qa:run-001' in node_id for node_id in first)
    assert all('qa:run-002' in node_id for node_id in second)
    assert all(g.node(node_id) is not None for node_id in first | second)


def test_reusing_same_qa_run_id_fails_closed_instead_of_folding_history():
    g=fixture_graph()
    findings=inspect_graph_contract(g)
    attach_findings(g,findings,run_id='qa:run-reused')
    with pytest.raises(ValueError,match='QA run identity collision'):
        attach_findings(g,findings,run_id='qa:run-reused')


def test_qa_run_id_cannot_alias_non_run_node_and_does_not_mutate_graph():
    g=fixture_graph()
    before_nodes=[n.id for n in g.nodes]
    before_edges=[(e.source,e.target,e.kind) for e in g.edges]
    findings=inspect_graph_contract(g)
    with pytest.raises(ValueError,match='collides with non-Run'):
        attach_findings(g,findings,run_id='scene')
    assert [n.id for n in g.nodes]==before_nodes
    assert [(e.source,e.target,e.kind) for e in g.edges]==before_edges


def test_qa_preflights_all_generated_ids_before_any_write():
    g=fixture_graph()
    findings=inspect_graph_contract(g)
    if len(findings) < 2:
        findings=list(findings)+[GraphQAFinding('SECOND','P1','scene','second synthetic finding')]
    run_id='qa:run-atomic'
    colliding_id=f"qa:{run_id}:002:{findings[1].code.lower()}"
    g.add_node(g.typed_node(colliding_id,'QAResult',data={'preexisting':True},authority='authoritative',provenance_refs=['fixture']))
    before_nodes={n.id for n in g.nodes}
    before_edges={(e.source,e.target,e.kind) for e in g.edges}
    with pytest.raises(ValueError,match='QA run identity collision'):
        attach_findings(g,findings,run_id=run_id)
    assert {n.id for n in g.nodes}==before_nodes
    assert {(e.source,e.target,e.kind) for e in g.edges}==before_edges
    assert run_id not in before_nodes


def test_qa_missing_finding_target_fails_before_run_node_write():
    g=fixture_graph()
    findings=[GraphQAFinding('MISSING','P1','missing-node','bad target')]
    with pytest.raises(ValueError,match='QA finding target missing'):
        attach_findings(g,findings,run_id='qa:run-missing-target')
    assert 'qa:run-missing-target' not in {n.id for n in g.nodes}


def test_repair_candidate_projects_all_actual_mutation_targets():
    g=fixture_graph()
    findings=inspect_graph_contract(g)
    created=attach_findings(g,findings,run_id='qa:run-multi')
    defect_id=next(node_id for node_id in created if node_id.startswith('defect:'))
    candidate=RepairCandidateSpec(
        candidate_id='repair:multi-target', defect_id=defect_id, strategy='structural',
        mutations=(
            RepairMutation('hero','set','opacity',0.9,'repair subject integration'),
            RepairMutation('type','set','text_integrity','strict','repair typography integrity'),
            RepairMutation('type','set','layout_strategy','reflow','second mutation on same target'),
        ),
        affected_nodes=('hero','type'), regression_protected=('scene',),
    )
    attach_repair_candidates(g,[candidate])
    mutates=[e.target for e in g.edges if e.source==candidate.candidate_id and e.kind=='MUTATES']
    assert mutates==['hero','type']


def test_repair_candidate_with_missing_mutation_target_fails_before_write():
    g=fixture_graph()
    findings=inspect_graph_contract(g)
    created=attach_findings(g,findings,run_id='qa:run-missing')
    defect_id=next(node_id for node_id in created if node_id.startswith('defect:'))
    candidate=RepairCandidateSpec(
        candidate_id='repair:missing-target', defect_id=defect_id, strategy='minimal',
        mutations=(RepairMutation('missing-node','set','x',1,'invalid target'),),
        affected_nodes=('missing-node',), regression_protected=(),
    )
    with pytest.raises(ValueError,match='repair mutation target missing'):
        attach_repair_candidates(g,[candidate])
    assert 'repair:missing-target' not in {n.id for n in g.nodes}


def _valid_recovery_inputs(g):
    assignments=assign_renderers(g)
    rm=render_manifest(g,assignments,fps=30,width=1080,height=1920,duration_ms=1000)
    return {
        'git_sha':'a'*40,
        'asset_manifest_hash':'b'*64,
        'render_manifest':rm,
        'qa_summary':{'decision':'PASS'},
        'artifact_refs':['drive:file:1'],
    }


def test_studio_inspector_and_zero_context_recovery():
    g=fixture_graph()
    inputs=_valid_recovery_inputs(g)
    snapshot=inspect_project(g,render_manifest=inputs['render_manifest'])
    assert snapshot['render_manifest_present'] is True
    assert not snapshot['unresolved_layers']
    manifest=recovery_manifest(g,**inputs)
    assert manifest['recovery_ready'] is True
    assert all(manifest['zero_context_requirements'].values())
    assert manifest['manifest_hash']==recovery_manifest(g,**inputs)['manifest_hash']


def test_missing_render_manifest_cannot_claim_recovery_ready():
    g=fixture_graph()
    inputs=_valid_recovery_inputs(g)
    inputs['render_manifest']=None
    snapshot=inspect_project(g,render_manifest=None)
    assert snapshot['render_manifest_present'] is False
    assert snapshot['unresolved_layers']==['hero','type']
    manifest=recovery_manifest(g,**inputs)
    assert manifest['recovery_ready'] is False
    assert manifest['zero_context_requirements']['render_manifest_present'] is False
    assert manifest['zero_context_requirements']['no_unresolved_layers'] is False


def test_explicit_empty_assignments_and_missing_manifest_are_both_fail_closed():
    g=fixture_graph()
    inputs=_valid_recovery_inputs(g)
    inputs['render_manifest']={'assignments':[],'manifest_hash':'c'*64}
    manifest=recovery_manifest(g,**inputs)
    assert manifest['recovery_ready'] is False
    assert manifest['zero_context_requirements']['render_manifest_present'] is True
    assert manifest['zero_context_requirements']['no_unresolved_layers'] is False


def test_recovery_ready_requires_assets_render_evidence_qa_and_artifacts():
    g=fixture_graph()
    baseline=_valid_recovery_inputs(g)
    cases=[
        ('git_sha','not-a-sha','git_sha_valid'),
        ('asset_manifest_hash',None,'asset_manifest_hash_valid'),
        ('render_manifest',{'assignments':[{'node_id':'hero'},{'node_id':'type'}]},'render_manifest_hash_valid'),
        ('qa_summary',{},'qa_summary_present'),
        ('artifact_refs',[],'artifact_refs_present'),
    ]
    for field,value,requirement in cases:
        inputs=dict(baseline)
        inputs[field]=value
        manifest=recovery_manifest(g,**inputs)
        assert manifest['recovery_ready'] is False
        assert manifest['zero_context_requirements'][requirement] is False


def test_malformed_render_assignments_are_rejected_not_treated_as_complete():
    g=fixture_graph()
    for bad in (
        {},
        {'assignments':'hero','manifest_hash':'c'*64},
        {'assignments':[{}],'manifest_hash':'c'*64},
        {'assignments':[{'node_id':'hero'},{'node_id':'hero'}],'manifest_hash':'c'*64},
    ):
        with pytest.raises(ValueError):
            inspect_project(g,render_manifest=bad)
