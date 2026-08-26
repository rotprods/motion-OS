from src.qa.scoring import weighted_score
from src.workflows.gauntlet import next_action
def test_weighted_score_perfect():
 dims=['motion_choreography','composition','style_coherence','typography','transition_quality','asset_realism','brand_adherence','narrative_clarity','technical_integrity','final_frame_memorability'];assert weighted_score({k:10 for k in dims})==10
def test_gauntlet_accept():assert next_action(9.2,0,0,2,True)=='ACCEPT'
