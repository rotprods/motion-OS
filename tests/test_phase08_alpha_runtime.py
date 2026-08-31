from src.renderers import runtime_verifier
from src.renderers.runtime_verifier import pixel_format_has_alpha, verify_render_artifact


def _media(*, pix_fmt='yuva444p10le', has_alpha=True):
    return {
        'codec': 'fixture',
        'pix_fmt': pix_fmt,
        'has_alpha': has_alpha,
        'width': 1080,
        'height': 1920,
        'fps': '30/1',
        'frames': 60,
        'duration_s': 2.0,
        'sha256': 'a' * 64,
        'bytes': 1234,
    }


def test_pixel_format_alpha_classifier_is_conservative():
    assert pixel_format_has_alpha('yuva444p10le') is True
    assert pixel_format_has_alpha('gbrap16le') is True
    assert pixel_format_has_alpha('rgba') is True
    assert pixel_format_has_alpha('argb') is True
    assert pixel_format_has_alpha('yuv420p') is False
    assert pixel_format_has_alpha('rgb24') is False
    assert pixel_format_has_alpha('pal8') is False
    assert pixel_format_has_alpha(None) is False


def test_required_alpha_is_verified_from_physical_pixel_format(monkeypatch):
    monkeypatch.setattr(runtime_verifier,'probe_media',lambda path:_media())
    evidence=verify_render_artifact(
        'hyperframes','overlay.mov',
        expected_width=1080,expected_height=1920,expected_fps=30,expected_duration_s=2.0,
        expected_has_alpha=True,
    )
    assert evidence.available is True
    assert evidence.authority == 'renderer_executed'
    assert evidence.probes['observed_has_alpha'] is True
    assert evidence.probes['observed_pix_fmt'] == 'yuva444p10le'
    assert evidence.probes['artifact_integrity_errors'] == []


def test_required_alpha_fails_closed_when_physical_stream_is_opaque(monkeypatch):
    monkeypatch.setattr(runtime_verifier,'probe_media',lambda path:_media(pix_fmt='yuv420p',has_alpha=False))
    evidence=verify_render_artifact(
        'hyperframes','overlay.mp4',
        expected_width=1080,expected_height=1920,expected_fps=30,expected_duration_s=2.0,
        expected_has_alpha=True,
    )
    assert evidence.available is False
    assert evidence.authority == 'compiler_ready'
    assert 'alpha_mismatch' in evidence.probes['artifact_integrity_errors']
    assert evidence.reason == 'alpha_mismatch'


def test_explicit_opaque_contract_detects_unexpected_alpha(monkeypatch):
    monkeypatch.setattr(runtime_verifier,'probe_media',lambda path:_media())
    evidence=verify_render_artifact(
        'remotion','base.mov',
        expected_width=1080,expected_height=1920,expected_fps=30,expected_duration_s=2.0,
        expected_has_alpha=False,
    )
    assert evidence.available is False
    assert 'alpha_mismatch' in evidence.probes['artifact_integrity_errors']


def test_legacy_call_without_alpha_expectation_remains_backward_compatible(monkeypatch):
    monkeypatch.setattr(runtime_verifier,'probe_media',lambda path:_media(pix_fmt='yuv420p',has_alpha=False))
    evidence=verify_render_artifact(
        'remotion','base.mp4',
        expected_width=1080,expected_height=1920,expected_fps=30,expected_duration_s=2.0,
    )
    assert evidence.available is True
    assert evidence.probes['expected_has_alpha'] is None
