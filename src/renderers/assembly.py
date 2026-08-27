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
    z_index: int = 0
    timeline_origin: str = "local_zero"


def validate_artifacts(artifacts:list[RenderArtifact], *, width:int,height:int,fps:int,duration_ms:int) -> list[str]:
    errors=[]
    if not artifacts:
        return ["no_artifacts"]
    for a in artifacts:
        if a.start_ms < 0 or a.end_ms <= a.start_ms or a.end_ms > duration_ms:
            errors.append(f"invalid_interval:{a.artifact_id}")
        if (a.width,a.height)!=(width,height):
            errors.append(f"resolution_mismatch:{a.artifact_id}:{a.width}x{a.height}")
        if a.fps != fps:
            errors.append(f"fps_mismatch:{a.artifact_id}:{a.fps}")
        if not a.provenance:
            errors.append(f"missing_provenance:{a.artifact_id}")
        if a.timeline_origin != "local_zero":
            errors.append(f"unsupported_timeline_origin:{a.artifact_id}:{a.timeline_origin}")

    ordered=sorted(artifacts,key=lambda a:(a.z_index,a.artifact_id))
    base=ordered[0]
    if base.start_ms != 0 or base.end_ms != duration_ms:
        errors.append(f"base_must_cover_timeline:{base.artifact_id}")
    return errors


def build_composite_plan(artifacts:list[RenderArtifact], *, width:int,height:int,fps:int,duration_ms:int,audio_path:str|None=None) -> dict[str,Any]:
    errors=validate_artifacts(artifacts,width=width,height=height,fps=fps,duration_ms=duration_ms)
    if errors: raise ValueError(";".join(errors))
    ordered=sorted(artifacts,key=lambda a:(a.z_index,a.artifact_id))
    plan={
      "width":width,"height":height,"fps":fps,"duration_ms":duration_ms,
      "audio_path":audio_path,
      "artifacts":[asdict(a) for a in ordered],
      "input_order":[a.artifact_id for a in ordered],
      "temporal_policy":"local_zero_to_exact_global_clock",
      "z_order_policy":"ascending_z_index_then_artifact_id",
      "color_policy":"normalize_before_composite",
      "audio_policy":"single_master_audio_graph",
      "provenance_required":True,
    }
    plan["plan_hash"]=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return plan


def ffmpeg_filter_complex(plan:dict[str,Any]) -> str:
    """Build video filters for plan-ordered FFmpeg inputs.

    Render artifacts use local-zero timestamps. Each overlay is trimmed to its
    declared region duration and shifted onto the global timeline before overlay.
    The first artifact is the lowest-z full-timeline base validated by the plan.
    Audio is intentionally excluded: the master AudioGraph is muxed separately.
    """
    artifacts=plan["artifacts"]
    if not artifacts:
        raise ValueError("composite plan has no artifacts")

    duration_s=plan["duration_ms"]/1000
    filters=[f"[0:v]trim=duration={duration_s:.3f},setpts=PTS-STARTPTS[base0]"]
    base="[base0]"
    for idx,a in enumerate(artifacts[1:], start=1):
        label=f"v{idx}"
        overlay_label=f"ov{idx}"
        start=a["start_ms"]/1000
        end=a["end_ms"]/1000
        region_duration=(a["end_ms"]-a["start_ms"])/1000
        filters.append(
            f"[{idx}:v]trim=duration={region_duration:.3f},"
            f"setpts=PTS-STARTPTS+{start:.3f}/TB[{overlay_label}]"
        )
        filters.append(
            f"{base}[{overlay_label}]overlay=eof_action=pass:shortest=0:"
            f"enable='between(t,{start:.3f},{end:.3f})'[{label}]"
        )
        base=f"[{label}]"
    return ";".join(filters)
