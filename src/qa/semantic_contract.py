from __future__ import annotations
from dataclasses import dataclass
from typing import Any
SEMANTIC_DIMENSIONS=['focal_hierarchy','composition_balance','typography_integrity','style_coherence','asset_realism','motion_motivation','transition_motivation','narrative_clarity','brand_adherence','final_frame_memorability']
@dataclass
class SemanticDefect:
    code:str; severity:str; dimension:str; description:str; beat_id:str|None=None; frame_range:tuple[int,int]|None=None; confidence:float=1.0; evidence:list[str]|None=None
def validate_semantic_report(report:dict[str,Any])->dict[str,Any]:
    missing=[d for d in SEMANTIC_DIMENSIONS if d not in report.get('scores',{})]
    if missing: raise ValueError(f'Missing semantic dimensions: {missing}')
    for d in report.get('defects',[]):
        if d.get('severity') not in {'P0','P1','P2','P3'}: raise ValueError(f'Invalid severity: {d}')
        if d.get('dimension') not in SEMANTIC_DIMENSIONS: raise ValueError(f'Invalid dimension: {d}')
    return report
def release_gate(technical_defects:list[dict],metric_defects:list[dict],semantic_report:dict|None,target:float=9.0)->dict:
    hard=[d for d in technical_defects+metric_defects if d.get('severity') in {'P0','P1'}]
    if hard:return {'status':'BLOCKED','reason':'HARD_DEFECTS','hard_defects':hard}
    if semantic_report is None:return {'status':'BLOCKED','reason':'SEMANTIC_VISION_QA_REQUIRED'}
    validate_semantic_report(semantic_report);semantic_hard=[d for d in semantic_report.get('defects',[]) if d.get('severity') in {'P0','P1'}];avg=sum(semantic_report['scores'].values())/len(semantic_report['scores'])
    if semantic_hard:return {'status':'BLOCKED','reason':'SEMANTIC_HARD_DEFECTS','hard_defects':semantic_hard,'semantic_mean':round(avg,3)}
    if avg<target:return {'status':'ITERATE','reason':'SEMANTIC_SCORE_BELOW_TARGET','semantic_mean':round(avg,3)}
    return {'status':'ACCEPT','reason':'ALL_GATES_PASSED','semantic_mean':round(avg,3)}
