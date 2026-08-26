from src.graph.model import MotionGraph, Node, Edge
from src.compilers.remotion_graph import compile_editing_graph_to_remotion, emit_remotion_project_files, build_ssr_render_contract
from src.compilers.hyperframes import compile_editing_graph_to_hyperframes, emit_hyperframes_project, build_hyperframes_render_contract
from src.compilers.lottie import compile_vector_subgraph_to_lottie, validate_lottie_subset
from src.renderers.multirender import assign_renderers, render_manifest
from src.renderers.assembly import RenderArtifact, build_composite_plan


def fixture_graph():
    nodes=[
        Node('scene_01','Scene',{'data':{'start_ms':0,'end_ms':1000}}),
        Node('env','Layer',{'data':{'layer_class':'ENVIRONMENT','z':0,'renderer_support':['remotion','hyperframes']}}),
        Node('hero','Layer',{'data':{'layer_class':'SUBJECT','z':3,'attention_role':'primary','renderer_support':['remotion']}}),
        Node('type','Layer',{'data':{'layer_class':'TYPOGRAPHY','z':6,'renderer_support':['hyperframes','remotion']}}),
        Node('camera','CameraRig',{'data':{'motion':'static','no_shake':True}}),
        Node('cue','AudioCue',{'data':{'at_ms':0,'event':'impact'}}),
    ]
    edges=[
        Edge('scene_01','env','CONTAINS'), Edge('scene_01','hero','CONTAINS'), Edge('scene_01','type','CONTAINS'),
        Edge('scene_01','camera','CONTAINS'), Edge('scene_01','cue','SYNC_WITH'),
    ]
    return MotionGraph(nodes,edges)


def test_remotion_graph_compiler_is_deterministic_and_emits_project():
    graph=fixture_graph()
    spec=compile_editing_graph_to_remotion(graph,fps=30,width=1080,height=1920)
    assert spec.duration_in_frames==30
    assert len(spec.scenes)==1
    assert [l['id'] for l in spec.scenes[0]['layers']]==['env','hero','type']
    assert spec.content_hash()==compile_editing_graph_to_remotion(graph,fps=30,width=1080,height=1920).content_hash()
    files=emit_remotion_project_files(spec)
    assert {'motion-spec.json','Root.tsx','MotionOSComposition.tsx'} <= set(files)
    contract=build_ssr_render_contract(spec)
    assert contract['pipeline']==['bundle','selectComposition','renderMedia']
    assert contract['authority']=='compiler_ready'


def test_hyperframes_graph_compiler_and_project_contract():
    spec=compile_editing_graph_to_hyperframes(fixture_graph(),fps=30)
    assert spec.duration_ms==1000
    files=emit_hyperframes_project(spec)
    assert {'index.html','motion.js','motion-spec.json'} <= set(files)
    assert 'gsap.timeline' in files['motion.js']
    contract=build_hyperframes_render_contract(spec)
    assert contract['deterministic_timeline'] is True
    assert contract['authority']=='compiler_ready'


def test_lottie_supported_subset_rejects_unknown_features():
    doc=compile_vector_subgraph_to_lottie([{'id':'ring','type':'shape','features':['transform','fill','trim_path']}],out_frame=30)
    assert validate_lottie_subset(doc).supported
    broken=dict(doc)
    broken['layers']=[{'type':'shape','features':['unsupported_magic']}]
    result=validate_lottie_subset(broken)
    assert not result.supported
    assert 'feature:unsupported_magic' in result.unsupported


def test_multi_renderer_assignments_and_composite_plan():
    graph=fixture_graph()
    assignments=assign_renderers(graph)
    by_id={a.node_id:a.renderer for a in assignments}
    assert by_id['hero']=='remotion'
    assert by_id['type']=='hyperframes'
    manifest=render_manifest(graph,assignments,fps=30,width=1080,height=1920,duration_ms=1000)
    assert manifest['manifest_hash']==render_manifest(graph,assignments,fps=30,width=1080,height=1920,duration_ms=1000)['manifest_hash']
    artifacts=[RenderArtifact('base','remotion','base.mov',0,1000,1080,1920,30,False,('graph:1',))]
    plan=build_composite_plan(artifacts,width=1080,height=1920,fps=30,duration_ms=1000)
    assert plan['temporal_policy']=='exact_global_clock'
    assert plan['provenance_required'] is True
