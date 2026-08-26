from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable
from collections import defaultdict, deque
import json

@dataclass
class Node:
    id: str
    kind: str
    attrs: dict[str, Any] = field(default_factory=dict)

@dataclass
class Edge:
    source: str
    target: str
    kind: str
    attrs: dict[str, Any] = field(default_factory=dict)

@dataclass
class MotionGraph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    def _node_ids(self): return {n.id for n in self.nodes}
    def add_node(self,node):
        if node.id in self._node_ids(): raise ValueError(f'Duplicate node id: {node.id}')
        self.nodes.append(node)
    def upsert_node(self,node):
        for i,n in enumerate(self.nodes):
            if n.id==node.id:self.nodes[i]=node;return
        self.nodes.append(node)
    def add_edge(self,edge):
        ids=self._node_ids()
        if edge.source not in ids or edge.target not in ids: raise ValueError(f'Edge references missing node: {edge.source}->{edge.target}')
        self.edges.append(edge)
    def node(self,node_id):
        for n in self.nodes:
            if n.id==node_id:return n
        raise KeyError(node_id)
    def query_nodes(self,kind=None,attrs=None):
        attrs=attrs or {};return [n for n in self.nodes if (not kind or n.kind==kind) and all(n.attrs.get(k)==v for k,v in attrs.items())]
    def topo_sort(self,dependency_edge_kinds=('REQUIRES','PRECEDES')):
        kinds=set(dependency_edge_kinds);ids=self._node_ids();indeg={i:0 for i in ids};adj=defaultdict(list)
        for e in self.edges:
            if e.kind in kinds:adj[e.source].append(e.target);indeg[e.target]+=1
        q=deque(sorted(i for i,d in indeg.items() if d==0));order=[]
        while q:
            u=q.popleft();order.append(u)
            for v in adj[u]:
                indeg[v]-=1
                if indeg[v]==0:q.append(v)
        if len(order)!=len(ids):raise ValueError('Dependency cycle detected')
        return order
    def validate(self):
        ids=self._node_ids();broken=[asdict(e) for e in self.edges if e.source not in ids or e.target not in ids];cycles=None
        try:self.topo_sort()
        except ValueError as exc:cycles=str(exc)
        return {'nodes':len(self.nodes),'edges':len(self.edges),'broken_edges':broken,'dependency_cycle':cycles}
    def to_dict(self):return {'nodes':[asdict(n) for n in self.nodes],'edges':[asdict(e) for e in self.edges]}
    @classmethod
    def from_dict(cls,data):return cls(nodes=[Node(**n) for n in data.get('nodes',[])],edges=[Edge(**e) for e in data.get('edges',[])])
    @classmethod
    def load(cls,path):
        with open(path,'r',encoding='utf-8') as f:return cls.from_dict(json.load(f))
    def dump(self,path):
        with open(path,'w',encoding='utf-8') as f:json.dump(self.to_dict(),f,indent=2,ensure_ascii=False)
