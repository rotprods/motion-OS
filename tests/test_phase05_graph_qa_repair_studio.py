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
        try:
            inspect_project(g,render_manifest=bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f'malformed render manifest should be rejected: {bad!r}')
