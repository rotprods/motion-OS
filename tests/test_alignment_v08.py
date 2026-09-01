import json

from src.qa.alignment import (
    release_readiness,
    validate_canonical_truth,
    validate_checkpoints,
    validate_weight_parity,
    validate_weights,
)


def test_alignment_weights_sum_to_one():
    result = validate_weights('config/alignment_weights.json')
    assert result['ok'], result


def test_alignment_weight_sources_have_semantic_parity():
    result = validate_weight_parity(
        'config/alignment_weights.json',
        'config/alignment_weights.yaml',
    )
    assert result['ok'], result


def test_checkpoint_state_is_valid():
    result = validate_checkpoints('state/checkpoints.json')
    assert result['ok'] and result['count'] == 23


def test_canonical_truth_surfaces_agree_on_high_risk_facts():
    result = validate_canonical_truth(
        'state/project_state.json',
        'state/checkpoints.json',
        'STATE.md',
        'TASKS.md',
        'HANDOFF.md',
    )
    assert result['ok'], result


def test_historical_v07_review_is_regression_evidence_not_current_release_authority():
    result = release_readiness(
        'state/project_state.json',
        'forensics/semantic_review_v07.json',
        expected_candidate_id='RC09E',
        expected_media_sha256='rc09e-authoritative-hash-required',
    )
    assert not result['ready']
    assert 'candidate_id_mismatch' in result['binding_errors']
    assert 'media_sha256_mismatch' in result['binding_errors']


def test_release_evidence_binding_fails_closed_on_candidate_or_hash_mismatch(tmp_path):
    state = tmp_path / 'state.json'
    review = tmp_path / 'review.json'
    state.write_text(json.dumps({'release_status': 'READY'}))
    review.write_text(json.dumps({
        'candidate_id': 'RC09E',
        'media': {'sha256': 'correct-hash'},
        'mean_score': 9.5,
        'defects': [],
    }))

    good = release_readiness(
        state,
        review,
        expected_candidate_id='RC09E',
        expected_media_sha256='correct-hash',
    )
    assert good['ready'] is True

    wrong_candidate = release_readiness(
        state,
        review,
        expected_candidate_id='RC10',
        expected_media_sha256='correct-hash',
    )
    assert wrong_candidate['ready'] is False
    assert wrong_candidate['binding_errors'] == ['candidate_id_mismatch']

    wrong_hash = release_readiness(
        state,
        review,
        expected_candidate_id='RC09E',
        expected_media_sha256='tampered-hash',
    )
    assert wrong_hash['ready'] is False
    assert wrong_hash['binding_errors'] == ['media_sha256_mismatch']
