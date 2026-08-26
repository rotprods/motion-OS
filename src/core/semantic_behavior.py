from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


SEMANTIC_BEHAVIORS = {
    "autonomy": ("controller_node", "central node orchestrates dependent modules"),
    "copilot": ("secondary_panel", "small secondary panel supports primary workspace"),
    "productivity": ("parallel_branching", "work branches into simultaneous coordinated paths"),
    "bottleneck": ("geometric_narrowing", "flow constricts through a narrow passage"),
    "coordination": ("synchronized_convergence", "independent elements converge on a shared beat"),
    "growth": ("controlled_expansion", "scale or count accumulates without chaotic overshoot"),
    "focus": ("noise_collapse", "peripheral elements reduce until one task remains"),
    "save": ("toggle_confirmation", "state toggles then settles with explicit confirmation"),
    "streak": ("mechanical_accumulation", "counter advances and locks into a reward state"),
    "discover": ("candidate_reveal", "multiple options resolve to one selected recommendation"),
    "sync": ("phase_alignment", "separate modules align to a shared temporal state"),
}


@dataclass(frozen=True)
class SemanticBehavior:
    concept: str
    behavior: str
    visual_contract: str
    confidence: float
    evidence: str

    def to_dict(self):
        return asdict(self)


def compile_semantic_behaviors(text: str, *, min_confidence: float = 0.5) -> list[SemanticBehavior]:
    normalized=text.casefold()
    found=[]
    for concept,(behavior,contract) in SEMANTIC_BEHAVIORS.items():
        if concept in normalized:
            found.append(SemanticBehavior(concept,behavior,contract,0.95,f"keyword:{concept}"))
    if not found:
        found.append(SemanticBehavior("other","single_focus_reveal","one dominant idea enters, resolves, and settles",min_confidence,"fallback:no_controlled_semantic_match"))
    return found


def primitive_candidates(behaviors: Iterable[SemanticBehavior]) -> list[str]:
    mapping={
        "controller_node":["node_expand","dependency_connect","settle"],
        "secondary_panel":["seed_to_card","panel_expand","settle"],
        "parallel_branching":["split","stagger","synchronized_settle"],
        "geometric_narrowing":["mask_narrow","flow_compress","release"],
        "synchronized_convergence":["parallel_enter","converge","settle"],
        "controlled_expansion":["count_up","scale_expand","settle"],
        "noise_collapse":["peripheral_fade","focus_lock","hold_readability"],
        "toggle_confirmation":["toggle","micro_pulse","settle"],
        "mechanical_accumulation":["count_up","badge_unlock","settle"],
        "candidate_reveal":["stagger_in","snap_focus","save_toggle"],
        "phase_alignment":["multi_device_flow","snap_grid","settle"],
        "single_focus_reveal":["reveal_mask","settle"],
    }
    out=[]
    for item in behaviors:
        out.extend(mapping.get(item.behavior,["reveal_mask","settle"]))
    return list(dict.fromkeys(out))
