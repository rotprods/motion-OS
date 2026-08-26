from dataclasses import dataclass,asdict
@dataclass
class Cause:code:str;confidence:float;dimensions:list[str];candidate_actions:list[str];evidence_required:list[str]
CAUSE_LIBRARY={'transition_quality':Cause('transition_quality',.86,['timing','velocity','occlusion','motion_blur','boundary_continuity'],['slow_occlusion','increase_motion_blur','change_foreground_scale','soften_boundary'],['motion_energy','boundary_mse','inside_delta']),'foreground_crop':Cause('foreground_crop',.82,['composition','foreground_scale','trajectory','safe_area'],['reduce_crop','change_trajectory','reduce_rotation'],['safe_area','edge_intersection','composition_balance']),'asset_realism':Cause('asset_realism',.78,['surface_detail','lighting','specular','relief','texture'],['increase_surface_detail','increase_specular','add_relief','replace_asset'],['local_contrast','edge_density','texture_entropy']),'safe_area_clipping':Cause('safe_area_clipping',.95,['typography','scale','max_width','alignment'],['reduce_headline_scale','reflow_copy','increase_safe_margin'],['bounding_box','safe_area'])}
def analyze(defects):
    out=[]
    for d in defects:
        c=CAUSE_LIBRARY.get(d.get('code'),Cause(d.get('code') or 'unknown',.45,['unknown'],['inspect'],['semantic_review']));p=asdict(c);p['defect_id']=d.get('id');p['severity']=d.get('severity','P2');out.append(p)
    return out
