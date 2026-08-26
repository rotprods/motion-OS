from __future__ import annotations

from copy import deepcopy
from math import ceil
from pathlib import Path
from typing import Any, Mapping
import json


KNOWN_STYLES = {
    "editorial_minimal", "neon_dark", "ui_saas_glow", "frosted_atmosphere",
    "eco_handdrawn_green", "kinetic_type", "3d_soft_pastel", "data_map_minimal",
    "print_editorial", "minimal_orbit", "portal_glass_ui", "premium_product",
    "dark_technical", "experimental_kinetic", "other",
}


def _evidence_refs(pack: Mapping[str, Any]) -> list[str]:
    refs = [str(k.get("id")) for k in pack.get("keyframes", []) if k.get("id")]
    return refs[:8]


def infer_style_family(pack: Mapping[str, Any]) -> dict[str, Any]:
    layout = dict(pack.get("layout_stats") or {})
    motion = dict(pack.get("motion_stats") or {})
    fx = dict(pack.get("fx_stats") or {})
    pattern = layout.get("pattern") or layout.get("global", {}).get("pattern")
    energy = motion.get("energy") or motion.get("tempo", {}).get("energy")
    fx_names = set(fx.get("labels") or fx.get("fx") or [])
    if "glass" in fx_names or "bloom" in fx_names and pattern == "floating_cards":
        label, confidence = "portal_glass_ui", 0.74
    elif pattern == "floating_cards":
        label, confidence = "ui_saas_glow", 0.65
    elif energy == "high":
        label, confidence = "experimental_kinetic", 0.58
    elif pattern == "centered_hero":
        label, confidence = "editorial_minimal", 0.55
    else:
        label, confidence = "other", 0.3
    return {"id": label, "confidence": confidence, "evidence_refs": _evidence_refs(pack)}


def _camera_plan(shot: Mapping[str, Any], motion_stats: Mapping[str, Any]) -> dict[str, Any]:
    motion_class = motion_stats.get("camera_motion", {}).get("classification") or "static"
    if motion_class == "camera_dominant":
        motion = "linear_slide"
    else:
        motion = "static"
    return {"rig_id":"rigC_ui_plate","framing":"medium","motion":motion,"z_drift":None,"focus_behavior":"locked","no_shake":True}


def normalize_feature_pack(pack: Mapping[str, Any]) -> dict[str, Any]:
    video = deepcopy(pack["video_meta"])
    fps = float(video["fps"])
    width, height = video["resolution"]["w"], video["resolution"]["h"]
    duration_ms = int(video["duration_ms"])
    refs = _evidence_refs(pack)
    style = infer_style_family(pack)
    assumptions: list[str] = []
    shots_out = []
    scene_boundaries = []
    for index, shot in enumerate(pack.get("shots", []), start=1):
        start_ms, end_ms = int(shot["start_ms"]), int(shot["end_ms"])
        from_frame = round(start_ms * fps / 1000)
        to_frame = max(from_frame, round(end_ms * fps / 1000) - 1)
        scene_boundaries.append({"shot_id":shot["id"],"from_frame":from_frame,"to_frame":to_frame})
        shot_ocr = [x for x in pack.get("ocr", []) if x.get("shot_id") in {None, shot["id"]}]
        choreography = []
        for j, item in enumerate(shot_ocr):
            target = item.get("continuity_id") or item.get("id") or f"text_{j+1}"
            at = start_ms + min(120*j, max(0, end_ms-start_ms-1))
            choreography.extend([
                {"id":f"{shot['id']}_{target}_enter","at_ms":at,"at_frame":round(at*fps/1000),"target":target,"action":"enter","channels":["y","opacity"],"from":{"y":12,"opacity":0},"to":{"y":0,"opacity":1},"duration_ms":180,"ease":"ease_out_cubic","notes":"Evidence-bound text block enters."},
                {"id":f"{shot['id']}_{target}_settle","at_ms":min(end_ms-1,at+180),"at_frame":round(min(end_ms-1,at+180)*fps/1000),"target":target,"action":"settle","channels":["y","opacity"],"from":{"y":0,"opacity":1},"to":{"y":0,"opacity":1},"duration_ms":0,"ease":"linear","notes":"Text locks without drift."},
            ])
        if len(choreography) < 12:
            assumptions.append(f"{shot['id']}: micro_choreography has <12 measured steps; no synthetic events were invented")
        shots_out.append({
            "id":shot["id"], "start_ms":start_ms, "end_ms":end_ms,
            "on_screen_text":[{"text":x.get("text"),"bbox":x.get("bbox"),"confidence":x.get("confidence")} for x in shot_ocr],
            "palette":[x.get("hex") for x in pack.get("color_stats", {}).get("palette", []) if x.get("hex")],
            "composition_tokens":[pack.get("layout_stats", {}).get("pattern","other")],
            "camera_plan":_camera_plan(shot, pack.get("motion_stats", {})),
            "depth_plan":{"layers_z":[{"id":"background","z_index":0,"parallax_ratio":0.0},{"id":"subject","z_index":1,"parallax_ratio":0.2},{"id":"ui","z_index":2,"parallax_ratio":0.35}],"materials_cues":[],"occlusion_events":[]},
            "transition_spec":{"type":"cut" if index>1 else "none","at_ms_global":start_ms,"supporting_fx":[],"notes":"Normalized from shot boundary; refine only with measured transition evidence."},
            "motion_events":[], "micro_choreography":choreography,
        })
    result = {
        "schema_version":"1.0.0",
        "video":{"duration_ms":duration_ms,"fps":fps,"resolution":{"w":width,"h":height},"aspect_ratio":video["aspect_ratio"]},
        "style_system":{
            "style_family":[style],
            "color":deepcopy(pack.get("color_stats", {})),
            "typography":{"families":[],"treatments":[]},
            "composition":deepcopy(pack.get("layout_stats", {})),
            "motion":deepcopy(pack.get("motion_stats", {})),
            "materials_3d":[x.get("label") for x in pack.get("asset_stats", {}).get("materials", []) if x.get("label")],
            "fx":list(pack.get("fx_stats", {}).get("labels", [])),
            "timing_rules":[],"failure_modes":[],"mitigations":[],
        },
        "camera_rigs":[{"rig_id":"rigC_ui_plate","type":"ui_plate","parameters":{"distortion":"none"},"confidence":0.6}],
        "shots":shots_out,
        "evidence":{"keyframes":deepcopy(pack.get("keyframes", [])),"timestamps":[],"claims":[{"claim_id":"style_family_01","label":style["id"],"confidence":style["confidence"],"evidence_refs":refs,"status":"inferred"}]},
        "quality":{"coverage":{"keyframe_count":len(refs)},"warnings":list(pack.get("warnings", [])),"assumptions":assumptions},
        "compiler_targets":{
            "remotion":{"project":{"fps":fps,"width":width,"height":height,"duration_frames":max(1,ceil(duration_ms*fps/1000))},"scene_boundaries":scene_boundaries,"z_order":["ui","subject","background"]},
            "framer_motion":{"easing_presets":{"ease_out_cubic":[0.215,0.61,0.355,1.0]},"motion_contracts":{}},
        },
    }
    return result


def validate_motionstyle(doc: Mapping[str, Any], schema_path: str | Path = "schemas/motionstyle2json.schema.json") -> None:
    import jsonschema
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    jsonschema.validate(instance=dict(doc), schema=schema)
