from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence


def build_reference_conditioning(neighbors: Sequence[Mapping[str, Any]], *, min_similarity: float = 0.65, max_neighbors: int = 3) -> dict[str, Any]:
    """Convert retrieved references into provenance-bearing soft constraints.

    Retrieval is conditioning evidence, not permission to copy exact content. The output intentionally
    separates reusable system-level tendencies from source-specific assets/copy.
    """
    selected=[]
    for n in neighbors:
        similarity=float(n.get("similarity",0.0))
        coverage=float(n.get("evidence_coverage",0.0))
        if similarity < min_similarity or coverage < 0.45:
            continue
        payload=n.get("payload",{}) if isinstance(n.get("payload"),Mapping) else {}
        style=payload.get("style_system",{}) if isinstance(payload,Mapping) else {}
        selected.append({
            "source_id":str(n.get("source_id","unknown")),
            "style_family":str(n.get("style_family","other")),
            "similarity":similarity,
            "evidence_coverage":coverage,
            "style_system":deepcopy(style),
        })
        if len(selected)>=max_neighbors:
            break
    if not selected:
        return {"authority":"none","sources":[],"soft_constraints":{},"forbidden_copy":True,"warnings":["no_reference_neighbor_passed_threshold"]}

    def values(path: str):
        out=[]
        for x in selected:
            cur: Any=x["style_system"]
            for part in path.split("."):
                if not isinstance(cur,Mapping) or part not in cur:
                    cur=None; break
                cur=cur[part]
            if cur not in (None,{},[]): out.append(deepcopy(cur))
        return out

    families=[x["style_family"] for x in selected]
    dominant=max(set(families),key=families.count)
    constraints={
        "style_family_hint":dominant,
        "color_candidates":values("color"),
        "typography_candidates":values("typography"),
        "composition_candidates":values("composition"),
        "motion_candidates":values("motion"),
        "material_candidates":values("materials_3d"),
        "fx_candidates":values("fx"),
    }
    return {
        "authority":"retrieved_evidence_soft_constraint",
        "sources":[{k:x[k] for k in ("source_id","style_family","similarity","evidence_coverage")} for x in selected],
        "soft_constraints":constraints,
        "forbidden_copy":True,
        "copy_policy":"never copy source text, logos, exact scene composition or protected assets; reuse only abstract system-level tendencies",
        "warnings":[],
    }


def apply_reference_conditioning(style_doc: Mapping[str, Any] | None, conditioning: Mapping[str, Any]) -> dict[str, Any]:
    """Attach evidence context without silently overwriting explicitly supplied canonical style tokens."""
    base=deepcopy(dict(style_doc or {}))
    base.setdefault("reference_conditioning",deepcopy(dict(conditioning)))
    if not base.get("style_system") and conditioning.get("soft_constraints"):
        soft=conditioning["soft_constraints"]
        base["style_system"]={
            "style_family":[{"id":soft.get("style_family_hint","other"),"confidence":0.55,"evidence_refs":[f"retrieval:{x['source_id']}" for x in conditioning.get("sources",[])]}],
            "color": (soft.get("color_candidates") or [{}])[0],
            "typography": (soft.get("typography_candidates") or [{}])[0],
            "composition": (soft.get("composition_candidates") or [{}])[0],
            "motion": (soft.get("motion_candidates") or [{}])[0],
            "materials_3d": (soft.get("material_candidates") or [[]])[0],
            "fx": (soft.get("fx_candidates") or [[]])[0],
        }
    return base
