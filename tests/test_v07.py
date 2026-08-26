from src.workflows.candidate_generator import generate
from src.workflows.root_cause import analyze
from src.workflows.tournament import rank
from src.cache.content_store import ContentStore
import tempfile
def test_candidate_diversity():
 c=generate({},['transition_quality']);assert len(c)==3 and len({x.strategy for x in c})==3 and c[0].params!=c[1].params
def test_root_cause_evidence_contract():
 r=analyze([{'id':'D1','code':'transition_quality','severity':'P2'}]);assert r[0]['confidence']>.8 and 'boundary_mse' in r[0]['evidence_required']
def test_tournament_promotes_one():
 rows=[{'id':'A','metrics':{'outside_invariance':1,'boundary_continuity':50,'motion_energy':100,'contrast':30,'edge_density':.2,'entropy':6,'risk':.2}},{'id':'B','metrics':{'outside_invariance':2,'boundary_continuity':40,'motion_energy':80,'contrast':35,'edge_density':.22,'entropy':6.2,'risk':.3}},{'id':'C','metrics':{'outside_invariance':1.2,'boundary_continuity':45,'motion_energy':95,'contrast':34,'edge_density':.21,'entropy':6.1,'risk':.25}}];assert sum(x.promoted for x in rank(rows))==1
def test_cache_key_deterministic():
 with tempfile.TemporaryDirectory() as td:s=ContentStore(td);assert s.key({'a':1,'b':2})==s.key({'b':2,'a':1})
