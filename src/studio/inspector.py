from __future__ import annotations
from collections import Counter
from typing import Any
import hashlib, json

def inspect_project(graph, *, render_manifest:dict[str,Any]|None=None) -> dict[str,Any]:
    kinds=Counter(n.kind for n in graph.nodes)
    layers=[n for n in graph.nodes if n.kind=="Layer"]
    provenance_gaps=[]
    for n in graph.nodes:
        attrs=getattr(n,"attrs",{}) or {}; data=attrs.get("data",attrs)
        if n.kind in {"Asset","Artifact"} and not attrs.get("provenance_refs") and not data.get("provenance"):
            provenance_gaps.append(n.id)
    unresolved=[]
    if render_manifest is not None:
        assigned={a["node_id"] for a in render_manifest.get("assignments",[])}
        unresolved=sorted({n.id for n in layers}-assigned)
    scenes=sorted([n for n in graph.nodes if n.kind=="Scene"],key=lambda n:(n.attrs.get("data") or {}).get("start_ms",0))
    timeline=[]
    for s in scenes:
        d=s.attrs.get("data") or {}; timeline.append({"id":s.id,"start_ms":d.get("start_ms"),"end_ms":d.get("end_ms")})
    snapshot={
        "graph_id":getattr(graph,"graph_id",None),"project_id":getattr(graph,"project_id",None),
        "graph_revision":getattr(graph,"graph_revision",None),
        "graph_hash":graph.content_hash() if hasattr(graph,"content_hash") else None,
        "node_counts":dict(sorted(kinds.items())),
        "edge_count":len(graph.edges),"timeline":timeline,
        "provenance_gaps":sorted(provenance_gaps),"unresolved_layers":unresolved,
    }
    snapshot["snapshot_hash"]=hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return snapshot

def recovery_manifest(graph, *, git_sha:str, asset_manifest_hash:str|None, render_manifest:dict[str,Any]|None, qa_summary:dict[str,Any]|None, artifact_refs:list[str]|None=None) -> dict[str,Any]:
    snapshot=inspect_project(graph,render_manifest=render_manifest)
    manifest={
        "git_sha":git_sha,
        "graph_id":snapshot["graph_id"],"graph_revision":snapshot["graph_revision"],"graph_hash":snapshot["graph_hash"],
        "asset_manifest_hash":asset_manifest_hash,
        "render_manifest_hash":(render_manifest or {}).get("manifest_hash"),
        "qa_summary":qa_summary or {},
        "artifact_refs":sorted(artifact_refs or []),
        "zero_context_requirements":{
            "graph_hash_present":bool(snapshot["graph_hash"]),
            "git_sha_present":bool(git_sha),
            "no_unresolved_layers":not snapshot["unresolved_layers"],
            "no_provenance_gaps":not snapshot["provenance_gaps"],
        },
    }
    req=manifest["zero_context_requirements"]
    manifest["recovery_ready"]=all(req.values())
    manifest["manifest_hash"]=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return manifest
