from src.graph.model import *
from src.graph.impact import affected_subgraph
from src.workflows.fitness import compare
from src.qa.release import release_gate
def test_impact():
 g=MotionGraph();[g.add_node(n) for n in [Node('b1','Beat',{'start':0,'end':2}),Node('b2','Beat',{'start':2,'end':4}),Node('p','Primitive',{})]];g.add_edge(Edge('b1','b2','PRECEDES'));g.add_edge(Edge('b2','p','USES'));r=affected_subgraph(g,['b2'],1,.2);assert r.start==1.8 and r.end==4.2
def test_fitness():assert compare({'score':8.2,'scores':{'composition':8.0,'typography':9.0}},{'score':8.5,'scores':{'composition':8.5,'typography':8.95}},['composition']).accepted
def test_release_requires_authoritative_semantic():assert release_gate({'score':9.7,'defects':[]},'heuristic')['verdict']=='BLOCK' and release_gate({'score':9.2,'defects':[]},'vision_model')['verdict']=='RELEASE'
