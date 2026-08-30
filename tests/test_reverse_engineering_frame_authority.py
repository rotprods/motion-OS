from __future__ import annotations

import copy

import pytest

from src.reverse_engineering.frame_timeline import FrameTimelineError, compile_frame_timeline
from src.reverse_engineering.template_compiler import compile_editing_template


def _pack():
    return {
        "video_meta": {
            "duration_ms": 100,
            "fps": 30.0,
            "resolution": {"w": 1920, "h": 1080},
            "aspect_ratio": "16:9",
            "frame_count": 3,
            "decoded_frame_count": 3,
            "source_sha256": "a" * 64,
        },
        "shots": [
            {"id": "shot_001", "start_ms": 0, "end_ms": 100, "start_frame": 0, "end_frame": 3},
        ],
        "keyframes": [],
        "ocr": [],
        "motion_stats": {"available": False},
        "audio_stats": {"available": False},
        "color_stats": {},
        "layout_stats": {},
        "fx_stats": {},
        "asset_stats": {},
        "warnings": [],
    }


def _motionstyle():
    return {
        "shots": [
            {
                "id": "shot_001",
                "start_ms": 0,
                "end_ms": 100,
                "camera_plan": {},
                "transition_spec": {},
                "micro_choreography": [],
                "composition_tokens": [],
            }
        ],
        "style_system": {"style_family": []},
        "evidence": {"claims": []},
        "quality": {"warnings": []},
        "compiler_targets": {"remotion": {"project": {}}},
    }


def test_authoritative_frame_timeline_requires_decoded_frame_count():
    pack = _pack()
    del pack["video_meta"]["decoded_frame_count"]
    # Legacy frame_count and duration*fps remain present, but neither is accepted as
    # proof that the timeline covers every frame actually decoded from the source.
    with pytest.raises(FrameTimelineError, match="decoded_frame_count is required"):
        compile_frame_timeline(pack, _motionstyle())


def test_duration_derived_estimate_cannot_authorize_reconstruct_exact():
    pack = _pack()
    del pack["video_meta"]["decoded_frame_count"]
    with pytest.raises(FrameTimelineError, match="decoded_frame_count is required"):
        compile_editing_template(pack, _motionstyle(), replication_mode="RECONSTRUCT_EXACT")


def test_decoded_frame_count_must_be_positive_integer_not_boolean():
    for invalid in (True, 0, -1, 3.5, "3.5"):
        pack = copy.deepcopy(_pack())
        pack["video_meta"]["decoded_frame_count"] = invalid
        with pytest.raises(FrameTimelineError):
            compile_frame_timeline(pack, _motionstyle())


def test_valid_decoded_frame_authority_is_exposed_per_frame():
    timeline = compile_frame_timeline(_pack(), _motionstyle())
    assert len(timeline) == 3
    assert all(row["authority"]["frame_index"] == "measured_decode" for row in timeline)
    assert all(row["authority"]["frame_count"] == "decoded_frame_count" for row in timeline)
