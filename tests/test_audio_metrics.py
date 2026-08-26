from src.extraction.audio_metrics import av_sync_metrics, transcript_coverage


def test_av_sync_metrics_are_timestamp_based():
    metrics = av_sync_metrics([100, 500, 1000], [90, 520, 970], tolerance_ms=40)
    assert metrics["hit_rate"] == 1.0
    assert metrics["mean_abs_delta_ms"] == 20.0


def test_transcript_coverage_merges_overlaps():
    result = transcript_coverage([
        {"start_ms": 0, "end_ms": 500},
        {"start_ms": 400, "end_ms": 900},
    ], 1000)
    assert result == {"covered_ms": 900, "ratio": 0.9}
