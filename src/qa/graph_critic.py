from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from src.graph.model import Edge

@dataclass(frozen=True)
class GraphQAFinding:
    code: str
    severity: str
    node_id: str
    message: str
    evidence: tuple[str,...] = ()

def inspect_graph_contract(graph) -> list[GraphQAFinding]:
    findings=[]
    validation=graph.validate_typed() if hasattr(graph,"validate_typed") else graph.validate()
    if not validation.get("ok", not validation.get("broken_edges")):
        findings.append(GraphQAFinding("GRAPH_INVALID","P0",getattr(graph,"graph_id","graph"),"typed graph validation failed",(str(validation),)))
    for n in graph.nodes:
        attrs=getattr(n,"attrs",{}) or {}
        data=attrs.get("data",attrs)
        if n.kind in {"Asset","Layer","Composition","Artifact"} and not attrs.get("provenance_refs") and not data.get("provenance"):
            findings.append(GraphQAFinding("MISSING_PROVENANCE","P1",n.id,"render-affecting node lacks provenance"))
        if n.kind=="Layer" and data.get("layer_class")=="TYPOGRAPHY":
            if data.get("text_integrity") not in {None,"strict"}:
                findings.append(GraphQAFinding("TEXT_INTEGRITY_WEAK","P0",n.id,"typography text integrity is not strict"))
    for scene in [n for n in graph.nodes if n.kind=="Scene"]:
        primary=[]
        for e in graph.edges:
            if e.source==scene.id and e.kind=="CONTAINS":
                child=graph.node(e.target)
                if child.kind=="Layer":
                    d=(child.attrs.get("data") or {})
                    if d.get("attention_role")=="primary": primary.append(child.id)
        if len(primary)>1:
            findings.append(GraphQAFinding("COMPETING_PRIMARY_MOTION","P1",scene.id,f"multiple primary attention layers: {primary}"))
    return findings

def attach_findings(graph, findings:list[GraphQAFinding], *, run_id:str="qa_run") -> list[str]:
    created=[]
    if run_id not in {n.id for n in graph.nodes}:
        graph.add_node(graph.typed_node(run_id,"Run",data={"kind":"graph_qa"},authority="authoritative",provenance_refs=["graph_critic"]))
    for idx,f in enumerate(findings,1):
        qid=f"qa:{idx:03d}:{f.code.lower()}"
        did=f"defect:{idx:03d}:{f.code.lower()}"
        graph.add_node(graph.typed_node(qid,"QAResult",data={"code":f.code,"severity":f.severity,"message":f.message,"evidence":list(f.evidence),"target":f.node_id},authority="authoritative",provenance_refs=["graph_critic"]))
        graph.add_node(graph.typed_node(did,"Defect",data={"code":f.code,"severity":f.severity,"message":f.message},authority="authoritative",provenance_refs=[qid]))
        graph.add_edge(Edge(qid,f.node_id,"EVALUATES",{"id":f"e_{qid}_target"}))
        graph.add_edge(Edge(qid,did,"FLAGS",{"id":f"e_{qid}_{did}"}))
        graph.add_edge(Edge(qid,run_id,"PRODUCED_BY",{"id":f"e_{qid}_{run_id}"}))
        created += [qid,did]
    return created
