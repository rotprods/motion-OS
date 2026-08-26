from dataclasses import dataclass
@dataclass
class Primitive:id:str;family:str;renderer_support:list;compatible_styles:list;energy_range:list;duration_range:list;requires:list;conflicts:list
DATA={'camera':['macro_push','parallax_push','orbit_2_5d','snap_zoom','whip_pan','micro_dolly','rack_focus_fake'],'transitions':['object_occlusion','foreground_pass','match_motion','radial_mask','velocity_blur','light_flash','depth_tunnel','ink_wipe','iris_reveal'],'typography':['mask_reveal','tracking_converge','kinetic_stack','type_tunnel','line_stagger','blur_reveal','word_swap','glyph_slice'],'graphics':['technical_grid_draw','dotted_matrix','blueprint_arc','annotation_trace','graph_growth','crosshair_lock'],'objects':['hero_float','coin_spin','card_stack','image_stack','document_flip','object_land'],'depth':['z_stack','foreground_parallax','depth_fog'],'lighting':['specular_sweep','light_rim'],'masks':['split_mask','shape_morph_mask'],'particles':['dust_field','micro_particle_burst']}
def build_registry():return [Primitive(n,f,['hyperframes','remotion','chromium_web'],['editorial_finance','swiss_brutalist','dark_technical','experimental_kinetic','premium_product'],[.2,.95],[.12,2.5],[],[]) for f,names in DATA.items() for n in names]
def validate_registry(reg):
 ids=[p.id for p in reg];return {'count':len(reg),'unique':len(ids)==len(set(ids)),'families':sorted(set(p.family for p in reg)),'gte_30':len(reg)>=30}
def anti_template(sequence):
 p=[f'repeated:{x}' for x in set(sequence) if sequence.count(x)>2]
 if sequence and all(x in {'mask_reveal','blur_reveal','hero_float'} for x in sequence):p.append('low_motion_diversity')
 return p
