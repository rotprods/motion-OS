from __future__ import annotations

from math import sqrt
from typing import Any, Mapping, Sequence


def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int,float)) else None


def element_state_error(reference: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, float | bool]:
    """Deterministic state error for vectorizable layers; zero is exact."""
    keys=("x","y","w","h","opacity")
    sq=[]
    for key in keys:
        a,b=_num(reference.get(key)),_num(candidate.get(key))
        if a is not None and b is not None:
            sq.append((a-b)**2)
    transform_ref=reference.get("transform") or {}
    transform_cand=candidate.get("transform") or {}
    for key in ("rotate",):
        a,b=_num(transform_ref.get(key)),_num(transform_cand.get(key))
        if a is not None and b is not None:
            sq.append((a-b)**2)
    text_ref=(reference.get("text_state") or {}).get("content")
    text_cand=(candidate.get("text_state") or {}).get("content")
    return {
        "rmse": round(sqrt(sum(sq)/len(sq)),6) if sq else 0.0,
        "text_exact": text_ref == text_cand,
        "visibility_exact": reference.get("visible") == candidate.get("visible"),
    }


def frame_fidelity(reference_elements: Sequence[Mapping[str, Any]], candidate_elements: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ref={e["id"]:e for e in reference_elements}
    cand={e["id"]:e for e in candidate_elements}
    missing=sorted(set(ref)-set(cand))
    extra=sorted(set(cand)-set(ref))
    common=sorted(set(ref)&set(cand))
    errors=[element_state_error(ref[i],cand[i]) for i in common]
    return {
        "missing_ids":missing,
        "extra_ids":extra,
        "id_integrity":not missing and not extra,
        "mean_state_rmse":round(sum(float(e["rmse"]) for e in errors)/len(errors),6) if errors else 0.0,
        "text_integrity":all(bool(e["text_exact"]) for e in errors),
        "visibility_integrity":all(bool(e["visibility_exact"]) for e in errors),
    }


def timeline_fidelity(reference_frames: Sequence[Mapping[str, Any]], candidate_frames: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ref={int(f["f"]):f for f in reference_frames}
    cand={int(f["f"]):f for f in candidate_frames}
    frames=sorted(set(ref)|set(cand))
    missing=[f for f in frames if f not in cand]
    extra=[f for f in frames if f not in ref]
    per=[]
    for f in frames:
        if f in ref and f in cand:
            score=frame_fidelity(ref[f].get("elements",[]), cand[f].get("elements",[]))
            score["f"]=f
            per.append(score)
    return {
        "missing_frames":missing,
        "extra_frames":extra,
        "frame_count_exact":not missing and not extra,
        "id_integrity":all(x["id_integrity"] for x in per),
        "text_integrity":all(x["text_integrity"] for x in per),
        "mean_state_rmse":round(sum(x["mean_state_rmse"] for x in per)/len(per),6) if per else 0.0,
        "per_frame":per,
    }


def choose_encoding(stability: str, *, text_typing: bool=False, high_motion: bool=False) -> str:
    if text_typing or high_motion:
        return "per_frame"
    if stability == "static":
        return "dense_keyframes"
    if stability == "low_motion":
        return "hybrid"
    return "per_frame"
