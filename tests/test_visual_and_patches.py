from src.graph.patch_planner import plan_patches
from src.assets.provenance import AssetRecord,coverage
def test_patch_planner_targets_low_dimension():
 p=plan_patches({'composition':8.0,'typography':9.2},[],target=9.0);assert p and p[0]['dimension']=='composition'
def test_provenance_coverage():
 rs=[AssetRecord('a','/x','hero','generated',None,'original',True),AssetRecord('b','/y','x','web',None,'unknown',False)];assert coverage(rs)==0.5
