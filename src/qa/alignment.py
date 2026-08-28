import json
from pathlib import Path

ALLOWED_CP = {
    'NOT_STARTED', 'SPECIFIED', 'PARTIAL', 'FUNCTIONAL',
    'ROBUST', 'PRODUCTION', 'BLOCKED'
}


def _read_json(path):
    return json.loads(Path(path).read_text())


def validate_weights(path):
    doc = _read_json(path)
    families = ['global_domains', 'creative', 'engineering', 'autonomy', 'trust']
    sums = {k: round(sum(float(v) for v in doc[k].values()), 6) for k in families}
    bad = {k: v for k, v in sums.items() if abs(v - 1) > 1e-6}
    return {'ok': not bad, 'sums': sums, 'bad': bad}


def validate_checkpoints(path):
    rows = _read_json(path)
    bad = [r for r in rows if r.get('status') not in ALLOWED_CP]
    ids = [r['id'] for r in rows]
    return {
        'ok': not bad and len(ids) == len(set(ids)),
        'count': len(rows),
        'invalid': bad,
    }


def validate_canonical_truth(project_state_path, checkpoints_path, state_md_path, tasks_md_path, handoff_md_path):
    """Fail closed on high-risk cross-surface truth contradictions.

    project_state.json is the machine current-state view. Human/operator surfaces are
    validated projections for release status, working master and production runtime
    authority; they are not permitted to independently drift on these facts.
    """
    state = _read_json(project_state_path)
    checkpoints = {row['id']: row for row in _read_json(checkpoints_path)}
    state_md = Path(state_md_path).read_text()
    tasks_md = Path(tasks_md_path).read_text()
    handoff_md = Path(handoff_md_path).read_text()
    errors = []

    master = state.get('working_master')
    release_status = state.get('release_status')
    remotion = state.get('capabilities', {}).get('remotion_production_runtime', {})

    if not master:
        errors.append('project_state:working_master_missing')
    else:
        if f'Working master: **{master}**' not in state_md:
            errors.append('STATE:working_master_mismatch')
        if f'**{master} is the logical working master.**' not in handoff_md:
            errors.append('HANDOFF:working_master_mismatch')

    if release_status == 'BLOCKED' and 'Release: **BLOCKED**' not in state_md:
        errors.append('STATE:release_status_mismatch')

    if remotion.get('authority') == 'VERIFIED':
        cp9 = checkpoints.get('CP9')
        if not cp9 or cp9.get('status') != 'PRODUCTION':
            errors.append('checkpoints:remotion_not_production')
        if 'Remotion production runtime: **VERIFIED**' not in state_md:
            errors.append('STATE:remotion_verified_missing')
        if '- [x] **P0-02 Remotion runtime**' not in tasks_md:
            errors.append('TASKS:remotion_still_blocking')
        if 'Remotion physical production runtime: **VERIFIED**' not in handoff_md:
            errors.append('HANDOFF:remotion_verified_missing')

    p0 = state.get('p0_blockers', [])
    if any('Remotion' in item for item in p0):
        errors.append('project_state:verified_remotion_in_p0')

    return {'ok': not errors, 'errors': errors}


def release_readiness(
    project_state_path,
    semantic_review_path,
    *,
    expected_candidate_id=None,
    expected_media_sha256=None,
):
    """Evaluate release evidence, optionally binding it to an exact candidate/media hash.

    Historical semantic evidence can remain useful regression evidence, but it cannot
    authorize a different current candidate when an expected binding is supplied.
    """
    state = _read_json(project_state_path)
    review = _read_json(semantic_review_path)
    hard = [d for d in review.get('defects', []) if d.get('severity') in {'P0', 'P1'}]

    binding_errors = []
    if expected_candidate_id is not None and review.get('candidate_id') != expected_candidate_id:
        binding_errors.append('candidate_id_mismatch')
    if expected_media_sha256 is not None:
        observed = review.get('media', {}).get('sha256')
        if observed != expected_media_sha256:
            binding_errors.append('media_sha256_mismatch')

    mean_score = review.get('mean_score', 0)
    ready = (
        state.get('release_status') == 'READY'
        and not hard
        and mean_score >= 9
        and not binding_errors
    )
    return {
        'ready': ready,
        'state_release_status': state.get('release_status'),
        'semantic_mean': mean_score,
        'hard_defects': hard,
        'binding_errors': binding_errors,
    }
