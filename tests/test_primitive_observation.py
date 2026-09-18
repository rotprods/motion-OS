from pathlib import Path

import src.qa.primitive_observation as observation
from src.qa.primitive_fixture_runner import build_fixture_specs
from src.qa.primitive_observation import observe_fixture_artifact, verify_observation_binding


def _spec():
    return next(s for s in build_fixture_specs() if s.primitive_id == 'macro_push' and s.renderer == 'remotion')


def test_observation_pack_is_bound_to_fixture_artifact_and_measured_signals(monkeypatch, tmp_path):
    spec = _spec()
    artifact = tmp_path / 'out.mp4'
    artifact.write_bytes(b'video')
    monkeypatch.setattr(observation, 'probe_media', lambda _path: {
        'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': '30/1',
        'frames': 60, 'duration_s': 2.0, 'sha256': 'a' * 64, 'bytes': 5,
    })
    monkeypatch.setattr(observation, 'extract_frames_ffmpeg', lambda *_args, **_kwargs: [
        {'frame': 0, 'path': 'a.png', 'sha256': '1' * 64},
        {'frame': 1, 'path': 'b.png', 'sha256': '2' * 64},
    ])
    monkeypatch.setattr(observation, 'change_scores_from_records', lambda _records: [0.2])
    monkeypatch.setattr(observation, 'optical_flow_opencv', lambda _records: {
        'available': True, 'authority': 'measured', 'tracks': [{'camera_likelihood': 0.9}],
    })
    monkeypatch.setattr(observation, 'ocr_tesseract', lambda *_args, **_kwargs: {
        'available': False, 'authority': 'unavailable', 'blocks': [],
    })
    monkeypatch.setattr(observation, 'fx_material_heuristics', lambda _records: (
        {'authority': 'measured_heuristic', 'labels': [], 'measurements': []},
        {'authority': 'inferred_from_measured_pixels', 'materials': []},
    ))
    pack = observe_fixture_artifact(spec, artifact)
    assert pack.fixture_sha256 == spec.sha256()
    assert pack.artifact_sha256 == 'a' * 64
    assert pack.primitive_id == 'macro_push'
    assert pack.frame_change['pairs'] == 1
    assert pack.frame_change['active_pair_ratio'] == 1.0
    assert len(pack.frame_evidence) == 2
    assert len(pack.content_hash()) == 64
    ok, findings = verify_observation_binding(spec, pack, artifact)
    assert ok is True
    assert findings == ()


def test_observation_binding_rejects_artifact_substitution(monkeypatch, tmp_path):
    spec = _spec()
    artifact = tmp_path / 'out.mp4'
    artifact.write_bytes(b'video')
    media = {
        'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': '30/1',
        'frames': 60, 'duration_s': 2.0, 'sha256': 'a' * 64, 'bytes': 5,
    }
    monkeypatch.setattr(observation, 'probe_media', lambda _path: dict(media))
    monkeypatch.setattr(observation, 'extract_frames_ffmpeg', lambda *_args, **_kwargs: [
        {'frame': 0, 'path': 'a.png', 'sha256': '1' * 64},
        {'frame': 1, 'path': 'b.png', 'sha256': '2' * 64},
    ])
    monkeypatch.setattr(observation, 'change_scores_from_records', lambda _records: [0.2])
    monkeypatch.setattr(observation, 'optical_flow_opencv', lambda _records: {'available': False, 'authority': 'unavailable', 'tracks': []})
    monkeypatch.setattr(observation, 'ocr_tesseract', lambda *_args, **_kwargs: {'available': False, 'authority': 'unavailable', 'blocks': []})
    monkeypatch.setattr(observation, 'fx_material_heuristics', lambda _records: ({'authority': 'measured_heuristic'}, {'authority': 'inferred_from_measured_pixels'}))
    pack = observe_fixture_artifact(spec, artifact)
    media['sha256'] = 'b' * 64
    ok, findings = verify_observation_binding(spec, pack, artifact)
    assert ok is False
    assert 'artifact_binding_mismatch' in findings
