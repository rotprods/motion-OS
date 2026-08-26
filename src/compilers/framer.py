from __future__ import annotations

from typing import Any, Mapping


def compile_framer_contracts(doc: Mapping[str, Any]) -> dict[str, Any]:
    target = doc["compiler_targets"]["framer_motion"]
    presets = dict(target.get("easing_presets", {}))
    contracts = dict(target.get("motion_contracts", {}))
    # Canonical minimum contracts are deterministic and brand-agnostic.
    defaults = {
        "headlineIn": {"initial":{"opacity":0,"y":18},"animate":{"opacity":1,"y":0},"transition":{"ease":"ease_out_cubic","duration":0.24}},
        "underlineDraw": {"initial":{"scaleX":0},"animate":{"scaleX":1},"transition":{"ease":"ease_out_cubic","duration":0.28}},
        "glassCardEnter": {"initial":{"opacity":0,"y":20,"scale":0.985},"animate":{"opacity":1,"y":0,"scale":1},"transition":{"ease":"ease_out_cubic","duration":0.32}},
        "portalFrameDrawOn": {"initial":{"pathLength":0},"animate":{"pathLength":1},"transition":{"ease":"ease_out_cubic","duration":0.42}},
        "cursorTyping": {"initial":{"opacity":0},"animate":{"opacity":1},"transition":{"duration":0.08}},
        "parallaxDrift": {"initial":{"x":0,"y":0},"animate":{"x":6,"y":-4},"transition":{"ease":"linear","duration":1.2}},
    }
    for key, value in defaults.items():
        contracts.setdefault(key, value)
    presets.setdefault("ease_out_cubic", [0.215,0.61,0.355,1.0])
    presets.setdefault("ease_in_out_cubic", [0.645,0.045,0.355,1.0])
    return {"easing_presets":presets,"motion_contracts":contracts}


def validate_contracts(compiled: Mapping[str, Any]) -> list[str]:
    errors=[]
    required={"headlineIn","underlineDraw","glassCardEnter","portalFrameDrawOn","cursorTyping","parallaxDrift"}
    missing=required-set(compiled.get("motion_contracts",{}))
    if missing:
        errors.append("missing_contracts:"+",".join(sorted(missing)))
    if "ease_out_cubic" not in compiled.get("easing_presets",{}):
        errors.append("missing_ease_out_cubic")
    return errors
