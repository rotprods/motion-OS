from src.qa.alignment import validate_weights,validate_checkpoints,release_readiness
def test_alignment_weights_sum_to_one():
 r=validate_weights('config/alignment_weights.json');assert r['ok'],r
def test_checkpoint_state_is_valid():
 r=validate_checkpoints('state/checkpoints.json');assert r['ok'] and r['count']==23
def test_current_master_is_not_releasable():
 r=release_readiness('state/project_state.json','forensics/semantic_review_v07.json');assert not r['ready'];assert r['hard_defects']
