from __future__ import annotations
from dataclasses import dataclass
from typing import Any

SUPPORTED_LAYER_TYPES=frozenset({"shape","text","image","precomp","null"})
SUPPORTED_FEATURES=frozenset({"transform","opacity","position","scale","rotation","shape_path","fill","stroke","trim_path","mask","marker"})

@dataclass(frozen=True)
class LottieValidation:
    supported: bool
    unsupported: tuple[str,...]
    warnings: tuple[str,...]

def validate_lottie_subset(doc: dict[str,Any]) -> LottieValidation:
    unsupported=[]; warnings=[]
    for layer in doc.get("layers",[]):
        typ=layer.get("type")
        if typ not in SUPPORTED_LAYER_TYPES: unsupported.append(f"layer_type:{typ}")
        for feature in layer.get("features",[]):
            if feature not in SUPPORTED_FEATURES: unsupported.append(f"feature:{feature}")
        if layer.get("expressions"): unsupported.append("expressions")
        if layer.get("text") and layer.get("rasterized_text"): warnings.append("rasterized_text_breaks_text_integrity")
    return LottieValidation(not unsupported,tuple(sorted(set(unsupported))),tuple(sorted(set(warnings))))

def compile_vector_subgraph_to_lottie(elements:list[dict[str,Any]], *, width=1080,height=1920,fps=30,in_frame=0,out_frame=300,markers=None) -> dict[str,Any]:
    layers=[]
    for idx,el in enumerate(elements):
        typ=el.get("type","shape")
        if typ not in SUPPORTED_LAYER_TYPES:
            raise ValueError(f"Unsupported Lottie layer type: {typ}")
        layers.append({"ind":idx+1,"nm":el["id"],"type":typ,"features":list(el.get("features",[])),"data":el.get("data",{})})
    doc={"v":"5.12.0","fr":fps,"ip":in_frame,"op":out_frame,"w":width,"h":height,"layers":layers,"markers":markers or []}
    result=validate_lottie_subset(doc)
    if not result.supported: raise ValueError("Unsupported Lottie subset: "+",".join(result.unsupported))
    return doc

def embed_contract(*, asset_id:str, lottie_path:str, target_renderer:str) -> dict[str,Any]:
    if target_renderer not in {"remotion","hyperframes"}: raise ValueError("target_renderer must be remotion or hyperframes")
    return {"asset_id":asset_id,"kind":"lottie","path":lottie_path,"target_renderer":target_renderer,"stable_ids_required":True,"text_integrity":"strict"}
