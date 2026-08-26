from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any
@dataclass
class Reference:
    id:str; title:str; source:str; source_uri:str; tags:list[str]; style_vector:dict[str,float]; rights:str='reference_only'; attrs:dict[str,Any]|None=None
def cosine(a,b):
    keys=set(a)|set(b);dot=sum(a.get(k,0)*b.get(k,0) for k in keys);na=sum(a.get(k,0)**2 for k in keys)**.5;nb=sum(b.get(k,0)**2 for k in keys)**.5;return dot/(na*nb) if na and nb else 0.0
def rank(references,target_vector,top_k=8):
    rows=[{'reference':asdict(r),'score':round(cosine(r.style_vector,target_vector),4)} for r in references];return sorted(rows,key=lambda x:x['score'],reverse=True)[:top_k]
