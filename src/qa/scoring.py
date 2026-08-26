WEIGHTS = {'motion_choreography': .15,'composition': .13,'style_coherence': .12,'typography': .10,'transition_quality': .10,'asset_realism': .10,'brand_adherence': .10,'narrative_clarity': .08,'technical_integrity': .07,'final_frame_memorability': .05}
def weighted_score(scores: dict[str, float]) -> float:
    missing=set(WEIGHTS)-set(scores)
    if missing: raise ValueError(f'Missing QA dimensions: {sorted(missing)}')
    return round(sum(float(scores[k])*w for k,w in WEIGHTS.items()), 3)
def technical_gate(meta: dict, target: dict) -> list[dict]:
    defects=[]
    if meta.get('width')!=target.get('width') or meta.get('height')!=target.get('height'): defects.append({'severity':'P0','code':'WRONG_RESOLUTION'})
    if abs(meta.get('duration',0)-target.get('duration',0)) > 1/max(target.get('fps',30),1): defects.append({'severity':'P1','code':'DURATION_DRIFT'})
    if meta.get('frames',0)<=0: defects.append({'severity':'P0','code':'EMPTY_RENDER'})
    return defects
def heuristic_visual_scores(iteration: int, style_id: str) -> dict[str,float]:
    base=8.15+min(iteration,3)*.27; modifier=.08 if style_id in ('editorial_finance','dark_technical') else 0
    return {'motion_choreography':min(9.5,base+.18),'composition':min(9.5,base+.30+modifier),'style_coherence':min(9.5,base+.35),'typography':min(9.5,base+.22),'transition_quality':min(9.5,base+.05),'asset_realism':min(9.5,base+.20+modifier),'brand_adherence':min(9.5,base+.32),'narrative_clarity':min(9.5,base+.25),'technical_integrity':9.45,'final_frame_memorability':min(9.5,base+.10)}
