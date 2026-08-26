from __future__ import annotations
def exploration_ratio(iteration,score_history):
    if len(score_history)>=3 and max(score_history[-3:])-min(score_history[-3:])<.12:return .8
    return max(.3,.7-iteration*.08)
def strategy_pool(defect):
    m={'transition_quality':['object_occlusion','typography_match_cut','depth_tunnel','whip_pan'],'asset_realism':['replace_asset','relight_asset','increase_relief','change_camera_distance'],'typography':['reflow_copy','reduce_scale','change_hierarchy','mask_reveal'],'final_frame_memorability':['hero_lockup','contrast_anchor','camera_still','brand_resolve']};return m.get(defect,['layout_recompose','motion_retime','asset_replace'])
def convergence(score_history,target=9.0):
    if score_history and score_history[-1]>=target:return 'TARGET_REACHED'
    if len(score_history)>=4 and max(score_history[-4:])-min(score_history[-4:])<.08:return 'PLATEAU_EXPLORE'
    return 'CONTINUE'
