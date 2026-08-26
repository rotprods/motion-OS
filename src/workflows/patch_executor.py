RULES={'transition_quality':{'occlusion_speed':.86,'motion_blur':1.18},'foreground_crop':{'foreground_crop':.82,'foreground_rotation':-8},'safe_area_clipping':{'headline_scale':.88},'asset_realism':{'surface_detail':1.18,'specular':1.12},'final_frame':{'final_hold':1.18,'camera_drift':.45}}
def patch_parameters(base,codes):
    p=dict(base);applied=[]
    for c in codes:
        ch=RULES.get(c,{})
        for k,v in ch.items():p[k]=round(p.get(k,1)*v,4)
        if ch:applied.append({'defect':c,'changes':ch})
    return p,applied
