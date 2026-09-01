from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import hashlib, json
from src.graph.model import Edge
from src.graph.impact import descendant_invalidation

@dataclass(frozen=True)
class RepairMutation:
    target_node_id: str
    operation: str
    field: str
    value: Any
    rationale: str

@dataclass(frozen=True)
class RepairCandidateSpec:
    candidate_id: str
    defect_id: str
    strategy: str
    mutations: tuple[RepairMutation,...]
    affected_nodes: tuple[str,...]
    regression_protected: tuple[str,...]
    score: float | None = None

def plan_repair_candidates(graph, defect_id:str, *, strategies=("minimal","structural","renderer_swap")) -> list[RepairCandidateSpec]:
    defect=graph.node(defect_id)
    dd=(defect.attrs.get("data") or {})
    qa_ids=[e.source for e in graph.edges if e.target==defect_id and e.kind=="FLAGS"]
    targets=[]
    for qid in qa_ids:
        targets += [e.target for e in graph.edges if e.source==qid and e.kind=="EVALUATES"]
    target=targets[0] if targets else defect_id
    impact=descendant_invalidation(graph,[target])
    all_ids={n.id for n in graph.nodes}
    protected=tuple(sorted(all_ids-set(impact.invalidated)))
    out=[]
    for idx,strategy in enumerate(strategies,1):
        if strategy=="minimal":
            muts=(RepairMutation(target,"set","qa_repair","minimal",f"repair {dd.get('code','defect')} with smallest valid delta"),)
        elif strategy=="structural":
            muts=(RepairMutation(target,"set","layout_strategy","structural_recompose","change topology rather than cosmetic overlay"),)
        else:
            muts=(RepairMutation(target,"set","renderer_preference","alternate_capable_renderer","test backend-specific root cause"),)
        out.append(RepairCandidateSpec(f"repair:{defect_id}:{idx}",defect_id,strategy,muts,tuple(impact.invalidated),protected))
    return out

def attach_repair_candidates(graph, candidates:list[RepairCandidateSpec]) -> list[str]:
    """Attach repair candidates while preserving defect lineage and mutation truth.

    ``DERIVED_FROM`` records which defect caused the candidate to exist. ``MUTATES``
    records only the actual graph nodes named by RepairMutation. Missing defects,
    missing mutation targets, and mutation-free candidates fail closed before any
    candidate node is written.
    """
    ids=[]
    existing={n.id for n in graph.nodes}
    for c in candidates:
        if c.defect_id not in existing:
            raise ValueError(f"repair defect target missing: {c.defect_id}")
        if not c.mutations:
            raise ValueError(f"repair candidate has no mutations: {c.candidate_id}")

        mutation_targets=tuple(sorted({m.target_node_id for m in c.mutations}))
        missing=[target for target in mutation_targets if target not in existing]
        if missing:
            raise ValueError(f"repair mutation target missing: {missing}")
        if c.candidate_id in existing:
            raise ValueError(f"repair candidate identity collision: {c.candidate_id}")

        graph.add_node(graph.typed_node(c.candidate_id,"RepairCandidate",data={
            "defect_id":c.defect_id,"strategy":c.strategy,
            "mutations":[asdict(m) for m in c.mutations],
            "affected_nodes":list(c.affected_nodes),"regression_protected":list(c.regression_protected),
        },authority="inferred",provenance_refs=[c.defect_id]))
        graph.add_edge(Edge(c.candidate_id,c.defect_id,"DERIVED_FROM",{"id":f"e_{c.candidate_id}_defect"}))
        for target in mutation_targets:
            graph.add_edge(Edge(c.candidate_id,target,"MUTATES",{"id":f"e_{c.candidate_id}_mutates_{target}"}))
        existing.add(c.candidate_id)
        ids.append(c.candidate_id)
    return ids

def choose_candidate(candidates:list[RepairCandidateSpec], scores:dict[str,float], *, regression_pass:dict[str,bool]) -> dict[str,Any]:
    eligible=[c for c in candidates if regression_pass.get(c.candidate_id,False) and c.candidate_id in scores]
    if not eligible: return {"decision":"HOLD","winner":None,"reason":"no_candidate_passed_regression"}
    winner=max(eligible,key=lambda c:(scores[c.candidate_id],c.strategy=="structural"))
    return {"decision":"PROMOTE","winner":winner.candidate_id,"score":scores[winner.candidate_id],"protected_nodes":list(winner.regression_protected)}

def tournament_hash(candidates:list[RepairCandidateSpec]) -> str:
    payload=[{"id":c.candidate_id,"strategy":c.strategy,"mutations":[asdict(m) for m in c.mutations],"affected":list(c.affected_nodes)} for c in candidates]
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
