from pathlib import Path

import src.qa.primitive_fixture_runner as runner
from src.qa.primitive_fixture_runner import (
    IdentityVerification,
    build_fixture_specs,
    contract_evidence,
    execute_physical_fixture,
    fixture_spec,
    qualification_plan,
    write_fixture_specs,
)
from src.qa.primitive_qualification import PrimitiveQualificationLedger, build_fixture_matrix


def test_fixture_specs_cover_exact_live_registry_matrix():
    specs = build_fixture_specs()
    plan = qualification_plan()
    assert len(specs) == len(build_fixture_matrix()) == 135
    assert len({(s.primitive_id, s.renderer) for s in specs}) == 135
    assert plan['registered_primitives'] == 45
    assert plan['renderer_cases'] == 135
    assert plan['cases_by_renderer'] == {'chromium_web': 45, 'hyperframes': 45, 'remotion': 45}
    assert all(s.fixture_id == f'primitive:{s.primitive_id}:renderer:{s.renderer}:v1' for s in specs)
    assert all(len(s.sha256()) == 64 for s in specs)


def test_fixture_payload_is_bound_to_live_primitive_contract():
    case = next(case for case in build_fixture_matrix() if case.primitive_id == 'match_motion' and case.renderer == 'remotion')
    spec = fixture_spec(case)
    assert 'connect_states' in spec.primitive_contract['semantic_intents']
    assert 'preserve_velocity' in spec.primitive_contract['semantic_intents']
    assert spec.primitive_contract['qa']['must_be_motivated'] is True
    assert spec.fps == 30
    assert spec.duration_s == 2.0


def test_fixture_specs_are_materializable_as_deterministic_json(tmp_path):
    paths = write_fixture_specs(tmp_path)
    assert len(paths) == 135
    first = paths[0]
    assert first.exists()
    assert first.suffix == '.json'
    assert first.read_text(encoding='utf-8').startswith('{')


def test_contract_evidence_only_grants_contract_authority():
    spec = next(s for s in build_fixture_specs() if s.primitive_id == 'macro_push' and s.renderer == 'remotion')
    evidence = contract_evidence(spec, test_run_id='contract-run-1')
    ledger = PrimitiveQualificationLedger(evidence=[evidence])
    assert ledger.renderer_state('macro_push', 'remotion') == 'CONTRACT_VERIFIED'
    assert ledger.primitive_state('macro_push') == 'CONTRACT_VERIFIED'


def test_missing_physical_artifact_is_explicit_quarantine(tmp_path):
    spec = next(s for s in build_fixture_specs() if s.primitive_id == 'macro_push' and s.renderer == 'remotion')
    result = execute_physical_fixture(
        spec,
        test_run_id='render-missing-1',
        output_dir=tmp_path,
        executor=lambda _spec, _root: None,
    )
    assert result.evidence.passed is False
    assert result.artifact_path is None
    assert 'artifact_missing' in result.findings
    ledger = PrimitiveQualificationLedger(evidence=[result.evidence])
    assert ledger.renderer_state('macro_push', 'remotion') == 'QUARANTINED'


def test_renderer_exception_becomes_evidence_not_success(tmp_path):
    spec = next(s for s in build_fixture_specs() if s.primitive_id == 'macro_push' and s.renderer == 'hyperframes')

    def explode(_spec, _root):
        raise RuntimeError('renderer unavailable')

    result = execute_physical_fixture(spec, test_run_id='render-exception-1', output_dir=tmp_path, executor=explode)
    assert result.evidence.passed is False
    assert any(item.startswith('renderer_exception:RuntimeError:') for item in result.findings)
    assert 'artifact_missing' in result.findings


def _media(monkeypatch, *, frames=60, sha='a' * 64):
    monkeypatch.setattr(
        runner,
        'probe_media',
        lambda _path: {
            'width': 1080,
            'height': 1920,
            'fps': '30/1',
            'frames': frames,
            'duration_s': frames / 30,
            'sha256': sha,
            'bytes': 17,
            'codec': 'h264',
        },
    )


def test_mechanically_valid_artifact_without_identity_verifier_is_quarantined(monkeypatch, tmp_path):
    spec = next(s for s in build_fixture_specs() if s.primitive_id == 'macro_push' and s.renderer == 'chromium_web')
    artifact = tmp_path / 'blank-but-valid.mp4'
    artifact.write_bytes(b'physical-artifact')
    _media(monkeypatch)
    result = execute_physical_fixture(
        spec,
        test_run_id='no-identity-1',
        output_dir=tmp_path,
        executor=lambda _spec, _root: artifact,
    )
    assert result.evidence.passed is False
    assert 'primitive_identity_unverified' in result.findings


def test_physical_success_requires_visual_clock_artifact_sha_and_identity_proof(monkeypatch, tmp_path):
    spec = next(s for s in build_fixture_specs() if s.primitive_id == 'macro_push' and s.renderer == 'chromium_web')
    artifact = tmp_path / 'out.mp4'
    artifact.write_bytes(b'physical-artifact')
    _media(monkeypatch)
    result = execute_physical_fixture(
        spec,
        test_run_id='physical-pass-1',
        output_dir=tmp_path,
        executor=lambda _spec, _root: artifact,
        identity_verifier=lambda checked_spec, _artifact: IdentityVerification(
            passed=checked_spec.primitive_id == 'macro_push',
            assertions=('macro_push_motion_signature_observed',),
        ),
    )
    assert result.evidence.passed is True
    assert result.evidence.frame_count == 60
    assert result.evidence.fps == 30.0
    assert result.evidence.visual_duration_ms == 2000
    assert result.evidence.artifact_sha256 == 'a' * 64
    assert 'macro_push_motion_signature_observed' in result.evidence.assertions
    ledger = PrimitiveQualificationLedger(evidence=[result.evidence])
    assert ledger.renderer_state('macro_push', 'chromium_web') == 'PHYSICALLY_VERIFIED'


def test_identity_verifier_failure_blocks_physical_authority(monkeypatch, tmp_path):
    spec = next(s for s in build_fixture_specs() if s.primitive_id == 'match_motion' and s.renderer == 'remotion')
    artifact = tmp_path / 'wrong-content.mp4'
    artifact.write_bytes(b'physical-artifact')
    _media(monkeypatch)
    result = execute_physical_fixture(
        spec,
        test_run_id='identity-fail-1',
        output_dir=tmp_path,
        executor=lambda _spec, _root: artifact,
        identity_verifier=lambda _spec, _artifact: IdentityVerification(
            passed=False,
            findings=('match_motion_signature_absent',),
        ),
    )
    assert result.evidence.passed is False
    assert 'match_motion_signature_absent' in result.findings


def test_wrong_frame_count_fails_closed_even_with_identity_proof(monkeypatch, tmp_path):
    spec = next(s for s in build_fixture_specs() if s.primitive_id == 'macro_push' and s.renderer == 'chromium_web')
    artifact = tmp_path / 'wrong.mp4'
    artifact.write_bytes(b'physical-artifact')
    _media(monkeypatch, frames=59, sha='b' * 64)
    result = execute_physical_fixture(
        spec,
        test_run_id='physical-fail-1',
        output_dir=tmp_path,
        executor=lambda _spec, _root: artifact,
        identity_verifier=lambda _spec, _artifact: IdentityVerification(
            passed=True,
            assertions=('macro_push_motion_signature_observed',),
        ),
    )
    assert result.evidence.passed is False
    assert 'frame_count_mismatch' in result.findings
    ledger = PrimitiveQualificationLedger(evidence=[result.evidence])
    assert ledger.renderer_state('macro_push', 'chromium_web') == 'QUARANTINED'
