from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping
import hashlib
import json
import re

_ALLOWED_PRIMARIES={"bt709","smpte432"}; _ALLOWED_TRANSFERS={"bt709","iec61966-2-1"}; _ALLOWED_MATRICES={"bt709","gbr"}; _ALLOWED_RANGES={"limited","full"}; _HDR_TRANSFER_TOKENS={"smpte2084","arib-std-b67"}; _RANGE_ALIASES={"tv":"limited","mpeg":"limited","limited":"limited","pc":"full","jpeg":"full","full":"full"}; _SAFE_FILTER_LABEL=re.compile(r"^[A-Za-z0-9_.:-]+$")

@dataclass(frozen=True)
class ColorProfile:
    profile_id:str; primaries:str; transfer:str; matrix:str; range:str; hdr:bool=False; evidence:tuple[str,...]=()
    def validate(self)->None:
        if not self.profile_id.strip(): raise ValueError("color profile requires profile_id")
        if self.primaries not in _ALLOWED_PRIMARIES: raise ValueError(f"unsupported_primaries:{self.primaries}")
        if self.transfer not in _ALLOWED_TRANSFERS: raise ValueError(f"unsupported_transfer:{self.transfer}")
        if self.matrix not in _ALLOWED_MATRICES: raise ValueError(f"unsupported_matrix:{self.matrix}")
        if self.range not in _ALLOWED_RANGES: raise ValueError(f"unsupported_range:{self.range}")
        if not self.evidence: raise ValueError(f"missing_color_evidence:{self.profile_id}")
        if any(not isinstance(item,str) or not item.strip() for item in self.evidence): raise ValueError(f"invalid_color_evidence:{self.profile_id}")

BT709_SDR_LIMITED=ColorProfile("bt709_sdr_limited","bt709","bt709","bt709","limited",evidence=("canonical_working_space",))
SRGB_FULL=ColorProfile("srgb_full","bt709","iec61966-2-1","gbr","full",evidence=("declared_browser_ui_space",))
DISPLAY_P3_SRGB_FULL=ColorProfile("display_p3_srgb_full","smpte432","iec61966-2-1","gbr","full",evidence=("declared_display_p3_space",))

def color_profile_from_probe(artifact_id:str, probe:Mapping[str,Any], *, evidence_ref:str)->ColorProfile:
    if not artifact_id.strip(): raise ValueError("probe profile requires artifact_id")
    if not evidence_ref.strip(): raise ValueError("probe profile requires evidence_ref")
    primaries=str(probe.get("color_primaries") or "").strip().lower(); transfer=str(probe.get("color_transfer") or "").strip().lower(); matrix=str(probe.get("color_space") or "").strip().lower(); range_raw=str(probe.get("color_range") or "").strip().lower()
    if transfer in _HDR_TRANSFER_TOKENS: raise ValueError(f"hdr_source_detected_requires_tone_map:{artifact_id}:{transfer}")
    if primaries not in _ALLOWED_PRIMARIES: raise ValueError(f"unqualified_probe_primaries:{artifact_id}:{primaries or 'missing'}")
    if transfer not in _ALLOWED_TRANSFERS: raise ValueError(f"unqualified_probe_transfer:{artifact_id}:{transfer or 'missing'}")
    if matrix not in _ALLOWED_MATRICES: raise ValueError(f"unqualified_probe_matrix:{artifact_id}:{matrix or 'missing'}")
    normalized_range=_RANGE_ALIASES.get(range_raw)
    if normalized_range is None: raise ValueError(f"unqualified_probe_range:{artifact_id}:{range_raw or 'missing'}")
    profile=ColorProfile(f"observed:{artifact_id}",primaries,transfer,matrix,normalized_range,evidence=(evidence_ref,)); profile.validate(); return profile

@dataclass(frozen=True)
class ArtifactColorBinding:
    artifact_id:str; source:ColorProfile; preserve_alpha:bool=False
    def validate(self)->None:
        if not self.artifact_id.strip(): raise ValueError("artifact color binding requires artifact_id")
        self.source.validate()

@dataclass(frozen=True)
class ColorNormalizationPlan:
    target:ColorProfile; bindings:tuple[ArtifactColorBinding,...]; backend:str; tone_map_policy:str; authority:str; plan_hash:str

def _canonical_payload(*,target,bindings,backend,tone_map_policy,authority):
    return {"target":asdict(target),"bindings":[{"artifact_id":b.artifact_id,"source":asdict(b.source),"preserve_alpha":b.preserve_alpha} for b in sorted(bindings,key=lambda x:x.artifact_id)],"backend":backend,"tone_map_policy":tone_map_policy,"authority":authority}

def build_color_normalization_plan(artifact_ids,source_profiles,*,alpha_artifacts=frozenset(),target=BT709_SDR_LIMITED,backend="zscale",tone_map_policy="reject_hdr"):
    if not artifact_ids: raise ValueError("no_artifacts")
    if len(set(artifact_ids))!=len(artifact_ids): raise ValueError("duplicate_artifact_id")
    artifact_set=set(artifact_ids); unknown_alpha=set(alpha_artifacts)-artifact_set
    if unknown_alpha: raise ValueError("unbound_alpha_artifacts:"+",".join(sorted(unknown_alpha)))
    if backend!="zscale": raise ValueError(f"unsupported_color_backend:{backend}")
    if tone_map_policy!="reject_hdr": raise ValueError(f"unsupported_tone_map_policy:{tone_map_policy}")
    target.validate()
    if target.hdr: raise ValueError("hdr_target_not_supported")
    extra=set(source_profiles)-artifact_set
    if extra: raise ValueError("unbound_color_profiles:"+",".join(sorted(extra)))
    bindings=[]
    for artifact_id in artifact_ids:
        profile=source_profiles.get(artifact_id)
        if profile is None: raise ValueError(f"missing_color_profile:{artifact_id}")
        profile.validate()
        if profile.hdr: raise ValueError(f"hdr_requires_explicit_tone_map:{artifact_id}")
        binding=ArtifactColorBinding(artifact_id,profile,artifact_id in alpha_artifacts); binding.validate(); bindings.append(binding)
    authority="IMPLEMENTED"; payload=_canonical_payload(target=target,bindings=tuple(bindings),backend=backend,tone_map_policy=tone_map_policy,authority=authority); plan_hash=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return ColorNormalizationPlan(target,tuple(sorted(bindings,key=lambda x:x.artifact_id)),backend,tone_map_policy,authority,plan_hash)

def _validate_filter_label(label:str)->None:
    if not label or not _SAFE_FILTER_LABEL.fullmatch(label): raise ValueError("unsafe_ffmpeg_filter_label")

def ffmpeg_color_filter(binding:ArtifactColorBinding,target:ColorProfile,*,input_label:str,output_label:str)->str:
    binding.validate(); target.validate(); source=binding.source
    if source.hdr or target.hdr: raise ValueError("hdr_color_conversion_not_qualified")
    _validate_filter_label(input_label); _validate_filter_label(output_label)
    zscale=("zscale="+f"primariesin={source.primaries}:transferin={source.transfer}:matrixin={source.matrix}:rangein={source.range}:primaries={target.primaries}:transfer={target.transfer}:matrix={target.matrix}:range={target.range}")
    pixel_format="yuva444p10le" if binding.preserve_alpha else "yuv444p10le"
    return f"[{input_label}]{zscale},format={pixel_format}[{output_label}]"

def ffmpeg_output_color_args(target:ColorProfile=BT709_SDR_LIMITED)->list[str]:
    target.validate()
    if target.hdr: raise ValueError("hdr_output_not_qualified")
    if target.matrix=="gbr": raise ValueError("rgb_matrix_output_metadata_not_qualified")
    return ["-color_primaries",target.primaries,"-color_trc",target.transfer,"-colorspace",target.matrix,"-color_range","tv" if target.range=="limited" else "pc"]

def validate_color_plan(plan,artifact_ids):
    errors=[]; expected=set(artifact_ids); actual={b.artifact_id for b in plan.bindings}
    if actual!=expected:
        missing=sorted(expected-actual); extra=sorted(actual-expected)
        if missing: errors.append("missing_bindings:"+",".join(missing))
        if extra: errors.append("extra_bindings:"+",".join(extra))
    if plan.authority!="IMPLEMENTED": errors.append("invalid_authority_state")
    try:
        plan.target.validate(); [b.validate() for b in plan.bindings]
    except ValueError as exc: errors.append(str(exc))
    payload=_canonical_payload(target=plan.target,bindings=plan.bindings,backend=plan.backend,tone_map_policy=plan.tone_map_policy,authority=plan.authority); observed=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    if observed!=plan.plan_hash: errors.append("plan_hash_mismatch")
    return errors
