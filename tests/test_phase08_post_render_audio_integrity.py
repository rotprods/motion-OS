import json

import pytest
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


def test_container_duration_cannot_substitute_for_missing_audio_stream_duration():
    stream=_audio()
    stream.pop("duration")
    evidence=verify_master_audio_integrity(
        "final.mp4",
        expected_duration_s=2.0,
        ffprobe_bin="ffprobe",
        runner=_runner([stream], format_duration="2.000"),
    )
    assert not evidence.ok
    assert "missing_audio_stream_duration" in evidence.errors


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("expected_sample_rate", True),
        ("expected_channels", 1.5),
        ("duration_tolerance_s", True),
        ("silence_floor_dbfs", float("nan")),
        ("timeout", 0),
    ],
)
def test_audio_policy_domains_fail_closed(field, value):
    kwargs={
        "media_path":"final.mp4",
        "expected_duration_s":2.0,
        "ffprobe_bin":"ffprobe",
        "runner":_runner([_audio()]),
    }
    kwargs[field]=value
    with pytest.raises(ValueError):
        verify_master_audio_integrity(**kwargs)


def test_speech_window_shape_and_numeric_domains_fail_closed():
    with pytest.raises(ValueError, match="speech_windows"):
        verify_master_audio_integrity(
            "final.mp4",
            expected_duration_s=2.0,
            speech_windows=[(0.0, 0.5)],  # type: ignore[arg-type]
            ffprobe_bin="ffprobe",
            runner=_runner([_audio()]),
        )
    with pytest.raises(ValueError, match="speech_windows"):
        verify_master_audio_integrity(
            "final.mp4",
            expected_duration_s=2.0,
            speech_windows=((True, 0.5),),
            ffprobe_bin="ffprobe",
            runner=_runner([_audio()]),
        )


@pytest.mark.parametrize("channels", [True, 1.5, "1.0"])
def test_probe_channel_type_confusion_cannot_qualify_mono(channels):
    stream=_audio(channels=channels)
    evidence=verify_master_audio_integrity(
        "final.mp4",
        expected_duration_s=2.0,
        expected_channels=1,
        ffprobe_bin="ffprobe",
        runner=_runner([stream]),
    )
    assert not evidence.ok
    assert "channel_mismatch:None" in evidence.errors


@pytest.mark.parametrize("floor", [-1000.0, -121.0, 0.0, 1.0])
def test_silence_floor_cannot_be_weakened_outside_physical_policy(floor):
    with pytest.raises(ValueError, match="between -120"):
        verify_master_audio_integrity(
            "final.mp4",
            expected_duration_s=2.0,
            silence_floor_dbfs=floor,
            ffprobe_bin="ffprobe",
            runner=_runner([_audio()]),
        )
