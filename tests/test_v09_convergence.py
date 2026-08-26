from src.renderers.contracts import detect_renderers
from src.primitives.registry import build_registry,validate_registry,anti_template
from src.workflows.adaptive_search import exploration_ratio,convergence
from src.qa.creative_gate import evaluate

def test_renderer_detection_contract_is_portable():
    r=detect_renderers()
    assert {'hyperframes','remotion','chromium_web'} <= set(r)
    assert all(hasattr(v,'available') for v in r.values())

def test_primitive_registry_production_count():
    v=validate_registry(build_registry());assert v['gte_30'] and v['unique']

def test_anti_template():assert anti_template(['object_occlusion','object_occlusion','object_occlusion'])

def test_adaptive_search_plateau():
    assert exploration_ratio(4,[8.1,8.12,8.13])==.8
    assert convergence([8.1,8.12,8.13,8.14])=='PLATEAU_EXPLORE'

def test_semantic_gate_blocks_non_authoritative():
    review={'provider':{'authoritative':False},'evidence_bound':True,'dimensions':{k:9.5 for k in __import__('src.qa.creative_gate',fromlist=['REQUIRED']).REQUIRED},'defects':[]}
    assert evaluate(review)['verdict']=='BLOCK'
