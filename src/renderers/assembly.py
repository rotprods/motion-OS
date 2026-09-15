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
        if not str(a.path).strip():
            errors.append(f"missing_path:{a.artifact_id}")
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
    if audio_path is not None and not str(audio_path).strip():
        errors.append("empty_master_audio_path")
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


def final_video_label(plan:dict[str,Any]) -> str:
    artifacts=plan.get("artifacts") or []
    if not artifacts:
        raise ValueError("composite plan has no artifacts")
    return "base0" if len(artifacts)==1 else f"v{len(artifacts)-1}"


def ffmpeg_filter_complex(plan:dict[str,Any], *, include_master_audio:bool=False) -> str:
    artifacts=plan["artifacts"]
    if not artifacts:
        raise ValueError("composite plan has no artifacts")
    duration_s=plan["duration_ms"]/1000
    filters=[f"[0:v]trim=duration={duration_s:.3f},setpts=PTS-STARTPTS[base0]"]
    base="[base0]"
    for idx,a in enumerate(artifacts[1:], start=1):
        label=f"v{idx}"; overlay_label=f"ov{idx}"
        start=a["start_ms"]/1000; end=a["end_ms"]/1000
        region_duration=(a["end_ms"]-a["start_ms"])/1000
        filters.append(f"[{idx}:v]trim=duration={region_duration:.3f},setpts=PTS-STARTPTS+{start:.3f}/TB[{overlay_label}]")
        filters.append(f"{base}[{overlay_label}]overlay=eof_action=pass:shortest=0:enable='between(t,{start:.3f},{end:.3f})'[{label}]")
        base=f"[{label}]"
    if include_master_audio:
        if plan.get("audio_policy") != "single_master_audio_graph": raise ValueError("unsupported audio policy")
        if not plan.get("audio_path"): raise ValueError("master audio requested without audio_path")
        audio_input_index=len(artifacts)
        filters.append(f"[{audio_input_index}:a:0]asetpts=PTS-STARTPTS,apad,atrim=duration={duration_s:.3f}[mastera]")
    return ";".join(filters)


def ffmpeg_assembly_argv(plan:dict[str,Any], output_path:str, *, ffmpeg_bin:str="ffmpeg", video_codec:str="libx264", audio_codec:str="aac", overwrite:bool=False) -> list[str]:
    artifacts=plan.get("artifacts") or []
    if not artifacts: raise ValueError("composite plan has no artifacts")
    if not str(output_path).strip(): raise ValueError("output_path must be non-empty")
    if not str(ffmpeg_bin).strip(): raise ValueError("ffmpeg_bin must be non-empty")
    if not str(video_codec).strip(): raise ValueError("video_codec must be non-empty")
    args=[str(ffmpeg_bin), "-y" if overwrite else "-n"]
    for artifact in artifacts:
        path=str(artifact.get("path", ""))
        if not path.strip(): raise ValueError(f"artifact input path missing: {artifact.get('artifact_id')}")
        args.extend(["-i", path])
    audio_path=plan.get("audio_path"); include_master_audio=audio_path is not None
    if include_master_audio:
        if plan.get("audio_policy") != "single_master_audio_graph": raise ValueError("unsupported audio policy")
        if not str(audio_path).strip(): raise ValueError("master audio path must be non-empty")
        if not str(audio_codec).strip(): raise ValueError("audio_codec must be non-empty")
        args.extend(["-i", str(audio_path)])
    filters=ffmpeg_filter_complex(plan, include_master_audio=include_master_audio)
    args.extend(["-filter_complex", filters, "-map", f"[{final_video_label(plan)}]"])
    if include_master_audio: args.extend(["-map", "[mastera]", "-c:a", str(audio_codec)])
    else: args.append("-an")
    duration_s=plan["duration_ms"]/1000
    args.extend(["-c:v", str(video_codec), "-r", str(plan["fps"]), "-t", f"{duration_s:.3f}", str(output_path)])
    return args
