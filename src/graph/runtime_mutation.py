from .model import MotionGraph,Node,Edge
def materialize_defects_and_patches(graph,iteration,defects,patches):
    iter_id=f'I{iteration:03d}';graph.upsert_node(Node(iter_id,'Iteration',{'iteration':iteration,'status':'EVALUATED'}));renderer=graph.query_nodes(kind='Renderer')
    if renderer:graph.add_edge(Edge(renderer[0].id,iter_id,'PRODUCES',{'iteration':iteration}))
    ds=[]
    for i,d in enumerate(defects,1):
        did=f'{iter_id}_D{i:03d}';graph.upsert_node(Node(did,'Defect',{**d,'iteration':iteration,'status':'OPEN'}));graph.add_edge(Edge(iter_id,did,'FAILS',{'severity':d.get('severity','P2')}));ds.append(did)
    ps=[]
    for i,p in enumerate(patches,1):
        pid=f'{iter_id}_P{i:03d}';graph.upsert_node(Node(pid,'Patch',{**p,'iteration':iteration,'status':'PLANNED'}));target=ds[min(i-1,len(ds)-1)] if ds else iter_id;graph.add_edge(Edge(target,pid,'PATCHED_BY',{'priority':p.get('priority',0)}));ps.append(pid)
    return {'iteration_node':iter_id,'defect_nodes':ds,'patch_nodes':ps}
def link_iterations(graph,previous_iteration,next_iteration):
    a=f'I{previous_iteration:03d}';b=f'I{next_iteration:03d}';graph.upsert_node(Node(b,'Iteration',{'iteration':next_iteration,'status':'PLANNED'}));graph.add_edge(Edge(a,b,'SUPERSEDED_BY',{'reason':'gauntlet_iteration'}))
