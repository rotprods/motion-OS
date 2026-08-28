import json
from pathlib import Path

from scripts.gauntlet_loop import canonical_hash, evaluate_gauntlet
from scripts.next_iteration_metaprompt import (
    compile_continuation_packet,
    render_metaprompt,
    verify_continuation_packet,
)
from scripts.next_wave import compile_next_wave


POLICY = json.loads(Path('config/autoloop_policy.json').read_text(encoding='utf-8'))


def live_state(*, watermark=77, barrier=True):
    return {
        'live_main_sha': 'a' * 40,
        'context_main_sha': 'a' * 40,
        'live_event_watermark': watermark,
        'context_event_watermark': watermark,
        'context_projection_hash': 'b' * 64,
        'event_fabric_snapshot_hash': 'c' * 64,
        'event_fabric_contract_version': 'motion-os.event-fabric/v3',
        'canonical_event_fabric_ready': True,
        'session_id': 'motion://session/chatgpt/autoloop/preprod-001',
        'workstream_seed': 'p08-preprod',
        'authority_reconstructed': True,
        'promotion_barrier_active': barrier,
        'event_semantic_divergence': False,
        'hard_security_blocker': False,
        'active_claims': [
            {'scope': 'authority:release', 'mode': 'EXCLUSIVE_WRITE', 'owner_session': 'motion://session/other/release'}
        ],
        'candidates': [
            {
                'task_id': 'MERGE_RELEASE',
                'priority': 'P0',
                'title': 'merge release',
                'scopes': ['authority:release'],
                'status': 'VERIFIED',
                'dependencies_satisfied': True,
                'blocked_external': False,
                'irreversible': True,
                'metrics': {'north_star_value': 10, 'bottleneck_relief': 10},
                'local_profiles': ['merge'],
                'adversarial_tests': ['combined-head'],
            },
            {
                'task_id': 'SAFE_REPAIR',
                'priority': 'P1',
                'title': 'repair deterministic truth projection',
                'scopes': ['file:src/qa/safe.py', 'root-cause:truth-drift'],
                'status': 'PROPOSED',
                'dependencies_satisfied': True,
                'blocked_external': False,
                'irreversible': False,
                'metrics': {'north_star_value': 8, 'bottleneck_relief': 9, 'correctness_security': 10},
                'local_profiles': ['quick'],
                'adversarial_tests': ['stale-watermark', 'duplicate-event'],
            },
        ],
    }


def closure_state():
    return {
        'project_id': 'motion://project/motion-os',
        'session_id': 'motion://session/chatgpt/autoloop/preprod-001',
        'workstream_id': 'motion://workstream/p08-preprod',
        'correlation_id': 'SAFE_REPAIR',
        'live_main_sha': 'a' * 40,
        'event_watermark': 77,
        'context_projection_hash': 'b' * 64,
        'event_fabric_snapshot_hash': 'c' * 64,
        'authority_state': 'VERIFIED_BRANCH_HEAD_NOT_PROMOTED',
        'branch': 'autoloop/p08-preprod/safe-repair',
        'pr': 999,
        'head_sha': 'd' * 40,
        'completed_work': ['safe repair implemented'],
        'exact_tests': ['quick: PASS'],
        'gauntlet_findings': ['stale event rejected'],
        'blockers': [],
        'external_degraded': [],
        'evidence_refs': ['clean-runner#999'],
        'released_scopes': ['file:src/qa/safe.py', 'root-cause:truth-drift'],
    }


def test_preproduction_tick_selects_safe_work_not_blocked_irreversible_work():
    wave = compile_next_wave(live_state(), POLICY)
    assert wave['decision'] == 'EXECUTE'
    assert wave['selected']['task_id'] == 'SAFE_REPAIR'
    assert wave['authority_binding']['event_watermark'] == 77


def test_outer_gauntlet_progresses_then_verifies():
    first_hash = canonical_hash({'attempt': 1})
    second_hash = canonical_hash({'attempt': 2, 'fixed': True})
    first = evaluate_gauntlet([
        {
            'iteration': 1,
            'strategy': 'tighten freshness gate',
            'result_hash': first_hash,
            'verifier_complete': False,
            'verifier_reason': 'watermark replay still stale',
            'measurable_progress': 0.4,
        }
    ])
    assert first['state'] == 'ITERATE'

    final = evaluate_gauntlet([
        {
            'iteration': 1,
            'strategy': 'tighten freshness gate',
            'result_hash': first_hash,
            'verifier_complete': False,
            'verifier_reason': 'watermark replay still stale',
            'measurable_progress': 0.4,
        },
        {
            'iteration': 2,
            'strategy': 'bind event fabric snapshot identity',
            'result_hash': second_hash,
            'verifier_complete': True,
            'verifier_reason': 'all freshness/replay invariants pass',
            'measurable_progress': 1.0,
        },
    ])
    assert final['state'] == 'VERIFIED'


def test_closure_packet_is_sealed_and_future_prompt_is_data_safe():
    wave = compile_next_wave(live_state(), POLICY)
    packet = compile_continuation_packet(closure_state(), wave)
    assert verify_continuation_packet(packet)
    prompt = render_metaprompt(packet)
    assert 'UNTRUSTED_DATA' in prompt
    assert 'PACKET_SHA256:' in prompt
    assert 'NEXT_TASK_ID_JSON: "SAFE_REPAIR"' in prompt


def test_next_tick_with_bus_advance_invalidates_prior_context_instead_of_chaining():
    next_tick = live_state(watermark=78)
    next_tick['context_event_watermark'] = 77
    next_tick['candidates'] = [next_tick['candidates'][1]]
    decision = compile_next_wave(next_tick, POLICY)
    assert decision['decision'] == 'BLOCKED'
    assert decision['reason'] == 'STALE_CONTEXT_EVENT_WATERMARK'


def test_event_fabric_unavailable_blocks_entire_execution_surface():
    state = live_state()
    state['canonical_event_fabric_ready'] = False
    decision = compile_next_wave(state, POLICY)
    assert decision == {
        'schema': 'motion-os.next-wave/v1',
        'decision': 'BLOCKED',
        'reason': 'CANONICAL_EVENT_FABRIC_NOT_READY',
    }
