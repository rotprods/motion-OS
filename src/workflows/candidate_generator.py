from copy import deepcopy
from dataclasses import dataclass
@dataclass
class Candidate:id:str;strategy:str;params:dict;target_dimensions:list[str];rationale:str;risk:float
def generate(base,defect_codes):
    a=deepcopy(base);a.update({'occlusion_speed':.78,'motion_blur':1.30,'foreground_crop':.78,'foreground_rotation':-6,'trajectory_y':-30});b=deepcopy(base);b.update({'occlusion_speed':1.08,'motion_blur':1.06,'foreground_crop':.66,'foreground_rotation':10,'trajectory_y':55});c=deepcopy(base);c.update({'occlusion_speed':.92,'motion_blur':1.16,'foreground_crop':.88,'foreground_rotation':-16,'trajectory_y':10,'secondary_ring':1.0});return [Candidate('CAND_A','cinematic_occlusion',a,['transition_quality','motion_choreography','composition'],'Slower readable occlusion with stronger blur and cleaner crop.',.24),Candidate('CAND_B','fast_diagonal_pass',b,['transition_quality','composition'],'Fast diagonal pass with reduced crop and blur.',.32),Candidate('CAND_C','layered_match_motion',c,['transition_quality','motion_choreography','style_coherence'],'Moderate occlusion plus secondary ring for match-motion continuity.',.28)]
