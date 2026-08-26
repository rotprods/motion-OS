from src.graph.model import MotionGraph,Node,Edge
def test_graph_validation_and_topology():
 g=MotionGraph();g.add_node(Node('a','Brief'));g.add_node(Node('b','Beat'));g.add_node(Node('c','Renderer'));g.add_edge(Edge('a','b','PRECEDES'));g.add_edge(Edge('b','c','PRECEDES'));order=g.topo_sort();assert order.index('a')<order.index('c');assert g.validate()['dependency_cycle'] is None
def test_query():
 g=MotionGraph([Node('a','Asset',{'license':'original'}),Node('b','Beat',{})],[]);assert g.query_nodes(kind='Asset')[0].id=='a'
