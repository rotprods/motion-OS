from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from .semantic_behavior import compile_semantic_behaviors, primitive_candidates


DEFAULT_RULES = {
    "no_drift": True,
    "text_integrity": "strict",
    "stable_anchors": True,
    "geometric_continuity": True,
    "one_dominant_idea_per_beat": True,
    "motivated_transitions": True,
    "persistent_ids": True,
}


def compile_motion_system(*, brief: str, style_doc: Mapping[str, Any] | None = None, grammar: Mapping[str, Any] | None = None) -> dict[str, Any]:
    style_doc=style_doc or {}; grammar=grammar or {}
    style=style_doc.get("style_system", style_doc)
    behaviors=compile_semantic_behaviors(brief)
    tokens={
        "spacing":{"base":8,"scale":[4,8,12,16,24,32,48,64]},
        "radii":{"sm":12,"md":18,"lg":24},
        "typography":deepcopy(style.get("typography",{})),
        "palette":deepcopy(style.get("color",{})),
        "grid":deepcopy(style.get("composition",{})),
        "materials":deepcopy(style.get("materials_3d",[])),
        "fx":deepcopy(style.get("fx",[])),
        "easing":deepcopy(grammar.get("easing",["ease_out_cubic","ease_in_out_cubic"])),
    }
    allowed=list(grammar.get("primitives", primitive_candidates(behaviors)))
    forbidden=list(grammar.get("negatives", []))
    return {
        "version":"1.0.0",
        "brief":brief,
        "tokens":tokens,
        "rules":dict(DEFAULT_RULES),
        "semantic_behaviors":[b.to_dict() for b in behaviors],
        "primitive_route":{"allowed":allowed,"forbidden":forbidden,"selected":primitive_candidates(behaviors)},
        "pacing_s":grammar.get("pacing_s"),
        "camera_grammar":grammar.get("camera", grammar.get("ui_camera_default","orthographic_2_5d")),
        "materials_grammar":grammar.get("materials", []),
        "qa":["drift","text_integrity","geometry_continuity","hierarchy","transition_motivation","grammar_fidelity","brand_consistency"],
    }


def compile_scene_contracts(motion_system: Mapping[str, Any], beats: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out=[]
    for i,beat in enumerate(beats):
        out.append({
            "scene_id":beat.get("id",f"S{i+1:02d}"),
            "objective":beat.get("objective") or beat.get("text") or "communicate beat",
            "primary_event":beat.get("primary_event") or (motion_system["primitive_route"]["selected"][:1] or ["reveal_mask"])[0],
            "incoming_continuity":beat.get("incoming_continuity","preserve persistent IDs" if i else "none"),
            "outgoing_continuity":beat.get("outgoing_continuity","transform primary geometry"),
            "persistent_layers":list(beat.get("persistent_layers",[])),
            "new_layers":list(beat.get("new_layers",[])),
            "semantic_target":beat.get("semantic_target") or motion_system["semantic_behaviors"][min(i,len(motion_system["semantic_behaviors"])-1)]["behavior"],
            "grammar_constraints":{"forbidden":motion_system["primitive_route"]["forbidden"],"one_dominant_idea":True},
            "audio_cues":list(beat.get("audio_cues",[])),
            "qa":["text_integrity","hierarchy","continuity","motivated_transition"],
        })
    return out
