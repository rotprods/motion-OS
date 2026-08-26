import json
from pathlib import Path
from src.primitives.registry import anti_template
suite=json.loads(Path('benchmarks/briefs/suite.json').read_text())
style_sequences={'editorial_finance':['technical_grid_draw','macro_push','mask_reveal','object_occlusion','parallax_push','hero_float','match_motion'],'swiss_brutalist':['technical_grid_draw','snap_zoom','kinetic_stack','split_mask','foreground_pass','line_stagger'],'dark_technical':['annotation_trace','parallax_push','specular_sweep','depth_tunnel','crosshair_lock','velocity_blur'],'experimental_kinetic':['tracking_converge','type_tunnel','whip_pan','foreground_pass','glyph_slice','depth_tunnel'],'premium_product':['hero_float','macro_push','specular_sweep','foreground_parallax','object_occlusion','light_flash']}
rows=[]
for b in suite:
 seq=style_sequences[b['style']];problems=anti_template(seq);rows.append({'id':b['id'],'style':b['style'],'complexity':b['complexity'],'primitive_sequence':seq,'anti_template_problems':problems,'structural_pass':not problems,'semantic_label':'PENDING_RENDER_AND_MULTIMODAL'})
summary={'briefs':len(rows),'styles':len(set(x['style'] for x in rows)),'structural_pass':sum(x['structural_pass'] for x in rows),'semantic_labeled':sum(x['semantic_label']!='PENDING_RENDER_AND_MULTIMODAL' for x in rows),'rows':rows};Path('reports/benchmark_25.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:summary[k] for k in ['briefs','styles','structural_pass','semantic_labeled']},indent=2))
