from src.graph.model import MotionGraph,Node
from src.graph.runtime_mutation import materialize_defects_and_patches,link_iterations
from src.qa.semantic_contract import release_gate,SEMANTIC_DIMENSIONS
from src.renderers.router import choose_renderer,RendererCapability
def test_graph_native_defects_and_patches():
 g=MotionGraph();g.add_node(Node('r','Renderer',{}));materialize_defects_and_patches(g,1,[{'severity':'P2','code':'X'}],[{'priority':3,'action':'fix'}]);assert len(g.query_nodes(kind='Defect'))==1;assert len(g.query_nodes(kind='Patch'))==1;link_iterations(g,1,2);assert g.node('I002').kind=='Iteration'
def test_release_requires_semantic_qa():assert release_gate([],[],None)['reason']=='SEMANTIC_VISION_QA_REQUIRED'
def test_semantic_accept():
 report={'scores':{k:9.2 for k in SEMANTIC_DIMENSIONS},'defects':[]};assert release_gate([],[],report)['status']=='ACCEPT'
def test_renderer_router_fallback():
 caps=[RendererCapability('hyperframes',False,None,[],'x'),RendererCapability('remotion',False,None,[],'x'),RendererCapability('native_prototype',True,'ffmpeg',[])];assert choose_renderer({'heavy_svg':True},caps)['selected']=='native_prototype'
