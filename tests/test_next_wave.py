import json
from pathlib import Path

from scripts.next_wave import compile_next_wave, scopes_overlap


POLICY = json.loads(Path('config/autoloop_policy.json').read_text(encoding='utf-8'))


def base_state():
    return {
        'live_main_sha': 'a' * 40,
        'context_main_sha': 'a' * 40,
        'session_id': 'motion://session/chatgpt/test/1',
        'workstream_seed': 'wave',
        'authority_reconstructed': True,
        'promotion_barrier_active': True,
        'event_semantic_divergence': False,
        'hard_security_blocker': False,
        'active_claims': [],
        'candidates': [],
    }


def candidate(task_id='T1', priority='P1', **overrides):
    raw = {
        'task_id': task_id,
        'priority': priority,
        'title': task_id,
        'scopes': ['file:src/a.py'],
        'status': 'PROPOSED',
        'dependencies_satisfied': True,
        'blocked_external': False,
        'irreversible': False,
        'metrics': {'north_star_value': 5, 'bottleneck_relief': 5},
        'local_profiles': ['quick'],
        'adversarial_tests': ['stale-context'],
    }
    raw.update(overrides)
    return raw


def test_live_main_drift_invalidates_context():
    state = base_state()
    state['context_main_sha'] = 'b' * 40
    state['candidates'] = [candidate()]
    result = compile_next_wave(state, POLICY)
    assert result['decision'] == 'BLOCKED'
    assert result['reason'] == 'STALE_CONTEXT_MAIN_SHA'


def test_event_semantic_divergence_fails_closed():
    state = base_state()
    state['event_semantic_divergence'] = True
    state['candidates'] = [candidate()]
    result = compile_next_wave(state, POLICY)
    assert result['decision'] == 'BLOCKED'
    assert result['reason'] == 'EVENT_SEMANTIC_DIVERGENCE'


def test_barrier_blocks_irreversible_but_not_safe_implementation():
    state = base_state()
    state['candidates'] = [
        candidate('MERGE', 'P0', irreversible=True),
        candidate('SAFE_FIX', 'P1', irreversible=False),
    ]
    result = compile_next_wave(state, POLICY)
    assert result['decision'] == 'EXECUTE'
    assert result['selected']['task_id'] == 'SAFE_FIX'


def test_exact_write_conflict_excludes_task():
    state = base_state()
    state['active_claims'] = [
        {'scope': 'file:src/a.py', 'mode': 'WRITE', 'owner_session': 'motion://session/other/1'}
    ]
    state['candidates'] = [candidate('CONFLICT'), candidate('FREE', scopes=['file:src/b.py'])]
    result = compile_next_wave(state, POLICY)
    assert result['selected']['task_id'] == 'FREE'


def test_read_claim_does_not_block_write_candidate():
    state = base_state()
    state['active_claims'] = [
        {'scope': 'file:src/a.py', 'mode': 'READ', 'owner_session': 'motion://session/other/1'}
    ]
    state['candidates'] = [candidate('T1')]
    assert compile_next_wave(state, POLICY)['selected']['task_id'] == 'T1'


def test_tree_file_overlap_is_detected():
    assert scopes_overlap('tree:src/content/**', 'file:src/content/foo.py')
    assert scopes_overlap('file:src/content/foo.py', 'tree:src/content/**')
    assert not scopes_overlap('tree:src/content/**', 'file:src/render/foo.py')


def test_external_blocker_is_not_selected():
    state = base_state()
    state['candidates'] = [
        candidate('EXTERNAL', 'P0', blocked_external=True),
        candidate('LOCAL', 'P1'),
    ]
    assert compile_next_wave(state, POLICY)['selected']['task_id'] == 'LOCAL'


def test_priority_and_value_choose_highest_safe_wave():
    state = base_state()
    state['promotion_barrier_active'] = False
    state['candidates'] = [
        candidate('P2_BIG', 'P2', metrics={'north_star_value': 10, 'bottleneck_relief': 10}),
        candidate('P0_SMALL', 'P0', metrics={'north_star_value': 1, 'bottleneck_relief': 1}),
    ]
    assert compile_next_wave(state, POLICY)['selected']['task_id'] == 'P0_SMALL'


def test_tie_break_is_deterministic():
    state = base_state()
    state['candidates'] = [candidate('B'), candidate('A')]
    first = compile_next_wave(state, POLICY)
    second = compile_next_wave(state, POLICY)
    assert first == second
    assert first['selected']['task_id'] == 'A'


def test_no_safe_task_returns_blocked_not_invented_work():
    state = base_state()
    state['candidates'] = [candidate('X', blocked_external=True)]
    result = compile_next_wave(state, POLICY)
    assert result['decision'] == 'BLOCKED'
    assert result['reason'] == 'NO_SAFE_HIGH_VALUE_TASK'


def test_packet_forces_fresh_recompile_at_closure():
    state = base_state()
    state['candidates'] = [candidate('T1')]
    result = compile_next_wave(state, POLICY)
    assert result['closure_requirements']['recompute_next_wave_from_live_truth'] is True
    assert result['closure_requirements']['never_chain_stale_packet'] is True
