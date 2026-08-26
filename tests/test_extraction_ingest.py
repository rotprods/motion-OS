from src.extraction.ingest import normalize_ffprobe


def test_normalize_ffprobe_preserves_rational_fps_and_meta():
    payload = {
        "streams": [
            {"codec_type": "video", "avg_frame_rate": "30000/1001", "width": 1920, "height": 1080, "codec_name": "h264", "nb_frames": "300"},
            {"codec_type": "audio", "codec_name": "aac"},
        ],
        "format": {"duration": "10.010", "bit_rate": "9000000"},
    }
    meta = normalize_ffprobe(payload, source_sha256="abc")
    assert meta.fps_num == 30000
    assert meta.fps_den == 1001
    assert 29.96 < meta.fps < 29.98
    assert meta.duration_ms == 10010
    assert meta.aspect_ratio == "16:9"
    assert meta.audio_tracks == 1
    assert meta.source_sha256 == "abc"


def test_normalize_ffprobe_requires_video_stream():
    import pytest
    with pytest.raises(ValueError):
        normalize_ffprobe({"streams": [{"codec_type": "audio"}]})
