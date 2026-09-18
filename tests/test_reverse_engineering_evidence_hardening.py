from __future__ import annotations

import copy

import pytest

from src.reverse_engineering.frame_timeline import FrameTimelineError, compile_frame_timeline
from src.reverse_engineering.template_compiler import EditingTemplateError, build_editing_signature, compile_editing_template, write_reverse_engineering_bundle


def pack():
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
        "shots": [{"id": "shot_001", "start_ms": 0, "end_ms": 100, "start_frame": 0, "end_frame": 3}],
        "keyframes": [],
        "ocr": [],
        "motion_stats": {
            "available": True,
            "authority": "measured",
            "method": "fixture_flow",
            "tracks": [{
                "from_frame": 0,
                "to_frame": 1,
                "global_dx": 0.1,
                "global_dy": 0.2,
                "global_magnitude": 0.3,
                "local_residual_median": 0.1,
                "motion_median": 0.3,
                "camera_likelihood": 0.4,
            }],
        },
        "audio_stats": {"available": False},
        "color_stats": {},
        "layout_stats": {},
        "fx_stats": {},
        "asset_stats": {},
        "warnings": [],
    }


def motionstyle():
    return {
        "shots": [{
            "id": "shot_001",
            "start_ms": 0,
            "end_ms": 100,
            "camera_plan": {},
            "transition_spec": {},
            "micro_choreography": [{
                "id": "step_1",
                "at_frame": 0,
                "target": "title",
                "action": "enter",
                "authority": "measured",
            }],
            "composition_tokens": [],
        }],
        "style_system": {"style_family": []},
        "evidence": {"claims": []},
        "quality": {"warnings": []},
        "compiler_targets": {"remotion": {"project": {}}},
    }


def test_derived_choreography_cannot_self_promote_to_measured_authority():
    timeline = compile_frame_timeline(pack(), motionstyle())
    assert timeline[0]["choreography_events"][0]["authority"] == "inferred"


@pytest.mark.parametrize("poison", [float("nan"), float("inf"), -0.1, True])
def test_measured_motion_poisoning_fails_closed(poison):
    data = pack()
    data["motion_stats"]["tracks"][0]["motion_median"] = poison
    with pytest.raises(FrameTimelineError, match="motion.motion_median"):
        compile_frame_timeline(data, motionstyle())


def test_camera_likelihood_outside_probability_domain_fails_closed():
    data = pack()
    data["motion_stats"]["tracks"][0]["camera_likelihood"] = 1.01
    with pytest.raises(FrameTimelineError, match="between 0 and 1"):
        compile_frame_timeline(data, motionstyle())


def test_source_identity_requires_real_lowercase_sha256_not_just_length():
    data = pack()
    data["video_meta"]["source_sha256"] = "z" * 64
    with pytest.raises(FrameTimelineError, match="SHA-256"):
        compile_editing_template(data, motionstyle(), replication_mode="RECONSTRUCT_EXACT")


def test_duplicate_measured_motion_frame_cannot_silently_overwrite_evidence():
    data = pack()
    data["motion_stats"]["tracks"].append(copy.deepcopy(data["motion_stats"]["tracks"][0]))
    with pytest.raises(FrameTimelineError, match="duplicate motion observation"):
        compile_frame_timeline(data, motionstyle())


def test_public_signature_builder_rejects_fake_sha_before_timeline_compilation():
    data = pack()
    data["video_meta"]["source_sha256"] = "z" * 64
    with pytest.raises(EditingTemplateError, match="SHA-256"):
        build_editing_signature(data, motionstyle())


@pytest.mark.parametrize("fps", [float("nan"), float("inf"), True])
def test_public_signature_builder_rejects_nonfinite_or_boolean_fps(fps):
    data = pack()
    data["video_meta"]["fps"] = fps
    with pytest.raises(EditingTemplateError, match="fps"):
        build_editing_signature(data, motionstyle())


def test_public_signature_builder_requires_decoded_frame_count_not_duration_estimate():
    data = pack()
    data["video_meta"].pop("decoded_frame_count")
    data["video_meta"]["frame_count"] = 3
    with pytest.raises(EditingTemplateError, match="decoded_frame_count"):
        build_editing_signature(data, motionstyle())


def test_public_signature_builder_rejects_nonfinite_motion_instead_of_zero_laundering():
    data = pack()
    data["motion_stats"]["tracks"][0]["motion_median"] = float("nan")
    with pytest.raises(EditingTemplateError, match="finite"):
        build_editing_signature(data, motionstyle())


def test_bundle_writer_refuses_nonstandard_nan_json(tmp_path):
    with pytest.raises(ValueError):
        write_reverse_engineering_bundle(
            tmp_path,
            {"template_id": "bad", "metric": float("nan")},
            [],
        )
