
def release_gate(report,semantic_provider,target=9.0):
    hard=[d for d in report.get("defects",[]) if d.get("severity") in ("P0","P1")]
    authoritative=semantic_provider in {"vision_model","human_review","multimodal_critic"}
    if hard: return {"verdict":"BLOCK","reason":"HARD_DEFECTS"}
    if not authoritative: return {"verdict":"BLOCK","reason":"SEMANTIC_VISION_NOT_AUTHORITATIVE"}
    if report["score"]<target: return {"verdict":"ITERATE","reason":"BELOW_TARGET"}
    return {"verdict":"RELEASE","reason":"ALL_GATES_PASSED"}
