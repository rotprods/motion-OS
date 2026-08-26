from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import hashlib, json

@dataclass(frozen=True)
class RenderArtifact:
    artifact_id: str
    renderer: str
    path: str
    start_ms: int
    end_ms: int
    width: int
    height: int
    fps: int
    has_alpha: bool = False
    provenance: tuple[str,...] = ()

def validate_artifacts(artifacts:list[RenderArtifact], *, width:int,height:int,fps:int,duration_ms:int) -> list[str]:
    errors=[]
    for a in artifacts:
        if a.start_ms < 0 or a.end_ms <= a.start_ms or a.end_ms > duration_ms:
            errors.append(f"invalid_interval:{a.artifact_id}")
        if (a.width,a.height)!=(width,height):
            errors.append(f"resolution_mismatch:{a.artifact_id}:{a.width}x{a.height}")
        if a.fps != fps:
            errors.append(f"fps_mismatch:{a.artifact_id}:{a.fps}")
    return errors

def build_composite_plan(artifacts:list[RenderArtifact], *, width:int,height:int,fps:int,duration_ms:int,audio_path:str|None=None) -> dict[str,Any]:
    errors=validate_artifacts(artifacts,width=width,height=height,fps=fps,duration_ms=duration_ms)
    if errors: raise ValueError(";".join(errors))
    ordered=sorted(artifacts,key=lambda a:(a.start_ms,a.renderer,a.artifact_id))
    plan={
      "width":width,"height":height,"fps":fps,"duration_ms":duration_ms,
      "audio_path":audio_path,
      "artifacts":[asdict(a) for a in ordered],
      "temporal_policy":"exact_global_clock",
      "color_policy":"normalize_before_composite",
      "audio_policy":"single_master_audio_graph",
      "provenance_required":True,
    }
    plan["plan_hash"]=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return plan

def ffmpeg_filter_complex(plan:dict[str,Any]) -> str:
    filters=[]
    base="[0:v]"
    for idx,a in enumerate(plan["artifacts"][1:], start=1):
        label=f"v{idx}"
        start=a["start_ms"]/1000
        end=a["end_ms"]/1000
        filters.append(f"{base}[{idx}:v]overlay=enable='between(t,{start:.3f},{end:.3f})'[{label}]")
        base=f"[{label}]"
    return ";".join(filters)
