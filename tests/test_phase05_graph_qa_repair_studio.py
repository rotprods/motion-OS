import pytest

from src.graph.editing_graph import TypedEditingGraph
from src.graph.model import Edge
from src.qa.graph_critic import inspect_graph_contract, attach_findings
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
        actual_mutates={
            e.target for e in g.edges
            if e.source==candidate.candidate_id and e.kind=='MUTATES'
        }
        derived_defects={
            e.target for e in g.edges
            if e.source==candidate.candidate_id and e.kind=='DERIVED_FROM'
        }
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

    assert first
    assert second
    assert first.isdisjoint(second)
    assert all('qa:run-001' in node_id for node_id in first)
    assert all('qa:run-002' in node_id for node_id in second)
    assert all(g.node(node_id) is not None for node_id in first | second)


def test_reusing_same_qa_run_id_fails_closed_instead_of_folding_history():
    g=fixture_graph()
    findings=inspect_graph_contract(g)
    attach_findings(g,findings,run_id='qa:run-reused')

    with pytest.raises(ValueError,match='QA run identity collision'):
        attach_findings(g,findings,run_id='qa:run-reused')


def test_repair_candidate_projects_all_actual_mutation_targets():
    g=fixture_graph()
    findings=inspect_graph_contract(g)
    created=attach_findings(g,findings,run_id='qa:run-multi')
    defect_id=next(node_id for node_id in created if node_id.startswith('defect:'))
    candidate=RepairCandidateSpec(
        candidate_id='repair:multi-target',
        defect_id=defect_id,
        strategy='structural',
        mutations=(
            RepairMutation('hero','set','opacity',0.9,'repair subject integration'),
            RepairMutation('type','set','text_integrity','strict','repair typography integrity'),
            RepairMutation('type','set','layout_strategy','reflow','second mutation on same target'),
        ),
        affected_nodes=('hero','type'),
        regression_protected=('scene',),
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
        candidate_id='repair:missing-target',
        defect_id=defect_id,
        strategy='minimal',
        mutations=(RepairMutation('missing-node','set','x',1,'invalid target'),),
        affected_nodes=('missing-node',),
        regression_protected=(),
    )

    with pytest.raises(ValueError,match='repair mutation target missing'):
        attach_repair_candidates(g,[candidate])
    assert 'repair:missing-target' not in {n.id for n in g.nodes}


def test_studio_inspector_and_zero_context_recovery():
    g=fixture_graph()
    assignments=assign_renderers(g)
    rm=render_manifest(g,assignments,fps=30,width=1080,height=1920,duration_ms=1000)
    snapshot=inspect_project(g,render_manifest=rm)
    assert not snapshot['unresolved_layers']
    manifest=recovery_manifest(g,git_sha='a'*40,asset_manifest_hash='b'*64,render_manifest=rm,qa_summary={'decision':'PASS'},artifact_refs=['drive:file:1'])
    assert manifest['recovery_ready'] is True
    assert manifest['manifest_hash']==recovery_manifest(g,git_sha='a'*40,asset_manifest_hash='b'*64,render_manifest=rm,qa_summary={'decision':'PASS'},artifact_refs=['drive:file:1'])['manifest_hash']
