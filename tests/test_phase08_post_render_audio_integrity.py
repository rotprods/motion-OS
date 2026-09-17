import json
from types import SimpleNamespace

from src.renderers.master_audio_integrity import verify_master_audio_integrity


def _runner(streams, *, format_duration='2.000', pcm=None):
    def run(argv, **kwargs):
        if 'ffprobe' in argv[0]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({'streams':streams,'format':{'duration':format_duration}}),
                stderr='',
            )
        return SimpleNamespace(returncode=0, stdout=pcm if pcm is not None else b'\x00\x08'*16000, stderr=b'')
    return run


def _audio(duration='2.000', *, rate='48000', channels=2):
    return {'index':1,'codec_type':'audio','codec_name':'aac','sample_rate':rate,'channels':channels,'duration':duration}


def test_missing_audio_stream_fails_closed():
    evidence=verify_master_audio_integrity(
        'final.mp4',expected_duration_s=2.0,ffprobe_bin='ffprobe',runner=_runner([]),
    )
    assert not evidence.ok
    assert evidence.errors == ('audio_stream_count:0',)


def test_multiple_audio_streams_violate_single_master_contract():
    evidence=verify_master_audio_integrity(
        'final.mp4',expected_duration_s=2.0,ffprobe_bin='ffprobe',runner=_runner([_audio(),_audio()]),
    )
    assert not evidence.ok
    assert evidence.errors == ('audio_stream_count:2',)


def test_duration_sample_rate_and_channels_are_bound_to_final_bytes():
    evidence=verify_master_audio_integrity(
        'final.mp4',expected_duration_s=2.0,duration_tolerance_s=1/30,
        ffprobe_bin='ffprobe',runner=_runner([_audio('1.800',rate='44100',channels=1)]),
    )
    assert not evidence.ok
    assert 'sample_rate_mismatch:44100' in evidence.errors
    assert 'channel_mismatch:1' in evidence.errors
    assert any(error.startswith('audio_duration_mismatch:') for error in evidence.errors)


def test_non_silent_speech_windows_prove_audio_survived_mux():
    pcm=(b'\xd0\x07')*16000
    evidence=verify_master_audio_integrity(
        'final.mp4',expected_duration_s=2.0,ffprobe_bin='ffprobe',ffmpeg_bin='ffmpeg',
        speech_windows=((0.0,0.8),(0.9,0.8)),runner=_runner([_audio()],pcm=pcm),
    )
    assert evidence.ok
    assert len(evidence.window_rms_dbfs) == 2
    assert all(value > -65 for value in evidence.window_rms_dbfs)


def test_present_but_silent_audio_cannot_qualify_when_speech_window_is_required():
    evidence=verify_master_audio_integrity(
        'final.mp4',expected_duration_s=2.0,ffprobe_bin='ffprobe',ffmpeg_bin='ffmpeg',
        speech_windows=((0.2,0.8),),runner=_runner([_audio()],pcm=b'\x00\x00'*16000),
    )
    assert not evidence.ok
    assert evidence.errors == ('silent_speech_window:0.200',)
