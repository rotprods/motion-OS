import pytest

from src.graph.editing_graph import TypedEditingGraph
from src.graph.model import Edge
from src.qa.graph_critic import inspect_graph_contract, attach_findings
from src.qa.graph_repair import plan_repair_candidates, attach_repair_candidates, choose_candidate, tournament_hash
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
    created=attach_findings(g,findings)
    defects=[nid for nid in created if nid.startswith('defect:')]
    assert defects
    candidates=plan_repair_candidates(g,defects[0])
    assert {c.strategy for c in candidates}=={'minimal','structural','renderer_swap'}
    assert tournament_hash(candidates)==tournament_hash(candidates)
    attach_repair_candidates(g,candidates)
    scores={c.candidate_id:(0.95 if c.strategy=='structural' else 0.8) for c in candidates}
    regress={c.candidate_id:True for c in candidates}
    decision=choose_candidate(candidates,scores,regression_pass=regress)
    assert decision['decision']=='PROMOTE'
    assert ':2' in decision['winner']


def test_qa_history_ids_are_scoped_by_run_and_preserve_multiple_passes():
    g=fixture_graph()
    findings=inspect_graph_contract(g)

    first=attach_findings(g,findings,run_id='qa:run:001')
    second=attach_findings(g,findings,run_id='qa:run:002')

    assert set(first).isdisjoint(second)
    assert all(':qa:run:001:' in node_id for node_id in first)
    assert all(':qa:run:002:' in node_id for node_id in second)
    assert len(g.query_nodes(kind='Run')) == 2
    assert len(g.query_nodes(kind='QAResult')) == len(findings) * 2
    assert len(g.query_nodes(kind='Defect')) == len(findings) * 2
    assert g.validate_typed()['ok'] is True


def test_same_qa_run_replay_fails_closed_before_partial_history_mutation():
    g=fixture_graph()
    findings=inspect_graph_contract(g)
    attach_findings(g,findings,run_id='qa:run:stable')
    before_nodes=len(g.nodes)
    before_edges=len(g.edges)

    with pytest.raises(ValueError,match='qa run history already exists or collides'):
        attach_findings(g,findings,run_id='qa:run:stable')

    assert len(g.nodes) == before_nodes
    assert len(g.edges) == before_edges


def test_qa_run_id_cannot_alias_non_run_graph_node():
    g=fixture_graph()
    with pytest.raises(ValueError,match='collides with non-Run node'):
        attach_findings(g,inspect_graph_contract(g),run_id='scene')


def test_studio_inspector_and_zero_context_recovery():
    g=fixture_graph()
    assignments=assign_renderers(g)
    rm=render_manifest(g,assignments,fps=30,width=1080,height=1920,duration_ms=1000)
    snapshot=inspect_project(g,render_manifest=rm)
    assert not snapshot['unresolved_layers']
    manifest=recovery_manifest(g,git_sha='a'*40,asset_manifest_hash='b'*64,render_manifest=rm,qa_summary={'decision':'PASS'},artifact_refs=['drive:file:1'])
    assert manifest['recovery_ready'] is True
    assert manifest['manifest_hash']==recovery_manifest(g,git_sha='a'*40,asset_manifest_hash='b'*64,render_manifest=rm,qa_summary={'decision':'PASS'},artifact_refs=['drive:file:1'])['manifest_hash']
