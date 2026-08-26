from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import hashlib, json

@dataclass(frozen=True)
class RenderAssignment:
    node_id: str
    renderer: str
    reason: str
    fallback: str | None = None

RENDERER_SUPPORT={
    "remotion":{"FOOTAGE_PLATES","SUBJECT","MIDGROUND","PRIMARY_UI","TYPOGRAPHY","FOREGROUND","FX","CAPTIONS_BRAND","BACKGROUND_GRAPHICS","ENVIRONMENT"},
    "hyperframes":{"ENVIRONMENT","BACKGROUND_GRAPHICS","MIDGROUND","PRIMARY_UI","TYPOGRAPHY","FOREGROUND","FX","CAPTIONS_BRAND"},
    "lottie":{"BACKGROUND_GRAPHICS","MIDGROUND","PRIMARY_UI","TYPOGRAPHY","FOREGROUND"},
    "svg_js":{"BACKGROUND_GRAPHICS","MIDGROUND","PRIMARY_UI","TYPOGRAPHY","FOREGROUND","CAPTIONS_BRAND"},
    "video_plate":{"ENVIRONMENT","FOOTAGE_PLATES","SUBJECT"},
}

def _data(node):
    a=getattr(node,"attrs",{}) or {}; return a.get("data",a)

def assign_renderers(graph, *, available=("remotion","hyperframes","lottie","svg_js","video_plate")) -> list[RenderAssignment]:
    available=set(available); out=[]
    for n in graph.nodes:
        if n.kind!="Layer": continue
        d=_data(n); lc=d.get("layer_class","MIDGROUND"); explicit=d.get("renderer")
        candidates=[]
        if explicit: candidates.append(explicit)
        support=d.get("renderer_support") or []
        candidates.extend(support)
        if lc=="FOOTAGE_PLATES": candidates+=["video_plate","remotion"]
        elif lc in {"PRIMARY_UI","TYPOGRAPHY"}: candidates+=["hyperframes","remotion","lottie","svg_js"]
        elif lc=="BACKGROUND_GRAPHICS": candidates+=["lottie","svg_js","hyperframes","remotion"]
        else: candidates+=["remotion","hyperframes","svg_js"]
        chosen=None
        for r in candidates:
            if r in available and lc in RENDERER_SUPPORT.get(r,set()):
                chosen=r; break
        if not chosen: raise RuntimeError(f"No renderer supports layer {n.id} class={lc}")
        out.append(RenderAssignment(n.id,chosen,f"layer_class:{lc}",None if chosen==candidates[0] else candidates[0] if candidates else None))
    return out

def render_manifest(graph, assignments:list[RenderAssignment], *, fps:int,width:int,height:int,duration_ms:int) -> dict[str,Any]:
    unresolved={n.id for n in graph.nodes if n.kind=="Layer"}-{a.node_id for a in assignments}
    if unresolved: raise ValueError(f"Unresolved layers: {sorted(unresolved)}")
    payload={"fps":fps,"width":width,"height":height,"duration_ms":duration_ms,"assignments":[asdict(a) for a in sorted(assignments,key=lambda x:x.node_id)]}
    payload["manifest_hash"]=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return payload
