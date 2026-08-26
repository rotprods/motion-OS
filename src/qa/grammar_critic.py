from __future__ import annotations

from typing import Any, Mapping, Sequence


GRAMMAR_DIMENSIONS = (
    "hierarchy_under_motion",
    "beat_focus",
    "motion_intent",
    "transition_motivation",
    "product_ui_authenticity",
    "material_consistency",
    "audio_visual_sync",
    "final_hold_stability",
    "text_integrity",
)


def score_grammar(observations: Mapping[str, float], *, hard_failures: Sequence[str] = ()) -> dict[str, Any]:
    dims={k:max(0.0,min(1.0,float(observations.get(k,0.0)))) for k in GRAMMAR_DIMENSIONS}
    mean_score=sum(dims.values())/len(dims)
    hard=set(hard_failures)
    if dims["text_integrity"] < 0.98:
        hard.add("text_integrity")
    if dims["beat_focus"] < 0.7:
        hard.add("beat_focus")
    return {
        "dimensions":dims,
        "mean":round(mean_score,4),
        "hard_failures":sorted(hard),
        "passed":mean_score >= 0.9 and not hard,
    }


def enforce_primitive_route(selected: Sequence[str], *, allowed: Sequence[str], forbidden: Sequence[str]) -> dict[str, Any]:
    allowed_set=set(allowed); forbidden_set=set(forbidden)
    violations=[]
    for primitive in selected:
        if primitive in forbidden_set:
            violations.append(f"forbidden:{primitive}")
        elif allowed_set and primitive not in allowed_set:
            violations.append(f"not_allowed:{primitive}")
    return {"passed":not violations,"violations":violations,"selected":list(selected)}
