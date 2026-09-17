from __future__ import annotations

import copy
import json

import pytest

from src.reverse_engineering import (
    EditingTemplateError,
    FrameTimelineError,
    build_editing_signature,
    compile_editing_template,
    compile_frame_timeline,
    validate_editing_template,
)


def _feature_pack():
    return {
        "schema_version": "1.0.0",
        "video_meta": {
            "duration_ms": 400,
            "fps": 30.0,
            "resolution": {"w": 1080, "h": 1920},
            "aspect_ratio": "9:16",
            "frame_count": 12,
            "decoded_frame_count": 12,
            "source_sha256": "a" * 64,
        },
        "shots": [
            {"id": "shot_001", "start_ms": 0, "end_ms": 100, "start_frame": 0, "end_frame": 3, "confidence": 1.0, "method": "fixture"},
            {"id": "shot_002", "start_ms": 100, "end_ms": 200, "start_frame": 3, "end_frame": 6, "confidence": 1.0, "method": "fixture"},
            {"id": "shot_003", "start_ms": 200, "end_ms": 300, "start_frame": 6, "end_frame": 9, "confidence": 1.0, "method": "fixture"},
            {"id": "shot_004", "start_ms": 300, "end_ms": 400, "start_frame": 9, "end_frame": 12, "confidence": 1.0, "method": "fixture"},
        ],
        "keyframes": [
            {"id": "kf_1", "shot_id": "shot_001", "frame": 1, "at_ms": 33, "sha256": "1" * 64, "artifact_ref": "frames/000001.png"},
            {"id": "kf_2", "shot_id": "shot_002", "frame": 4, "at_ms": 133, "sha256": "2" * 64, "artifact_ref": "frames/000004.png"},
        ],
        "ocr": [
            {"id": "ocr_1", "frame": 1, "text": "BUY NOW", "bbox": [0.1, 0.2, 0.4, 0.1], "confidence": 0.95, "method": "fixture", "continuity_id": "text_buy", "evidence_refs": ["frame:1"]},
            {"id": "ocr_2", "frame": 4, "text": "50% OFF", "bbox": [0.15, 0.7, 0.3, 0.08], "confidence": 0.93, "method": "fixture", "continuity_id": "text_offer", "evidence_refs": ["frame:4"]},
        ],
        "color_stats": {
            "palette": [
                {"hex": "#0B0B0B", "ratio": 0.7},
                {"hex": "#F97316", "ratio": 0.2},
            ],
            "gradients": [],
            "authority": "measured_pixels",
        },
        "layout_stats": {
            "anchors_x": [0.1, 0.5],
            "anchors_y": [0.2, 0.7],
            "safe_margin_pct": 8.0,
            "evidence_kind": "ocr_boxes",
        },
        "motion_stats": {
            "available": True,
            "authority": "measured",
            "method": "fixture_flow",
            "tracks": [
                {
                    "from_frame": frame,
                    "to_frame": frame + 1,
                    "global_dx": 1.0 + frame * 0.1,
                    "global_dy": 0.1,
                    "global_magnitude": 1.0 + frame * 0.1,
                    "local_residual_median": 0.4,
                    "motion_median": 1.2 + frame * 0.1,
                    "camera_likelihood": 0.72,
                }
                for frame in range(11)
            ],
        },
        "fx_stats": {"labels": ["blur"], "measurements": [{"frame": 1, "contrast": 20.0, "blur_proxy": 0.8, "highlight_ratio": 0.01}]},
        "asset_stats": {"materials": [{"label": "glass_or_polished_candidate", "confidence": 0.6, "evidence_refs": ["frame:1"]}]},
        "audio_stats": {
            "available": True,
            "authority": "measured",
            "method": "fixture_audio",
            "onsets_ms": [100, 200, 300],
            "transcript": [],
        },
        "extraction_provenance": [],
        "warnings": [],
    }


def _motionstyle():
    shots = []
    for index, (shot_id, start, end, transition) in enumerate(
        [
            ("shot_001", 0, 100, "hard_cut"),
            ("shot_002", 100, 200, "whip_pan"),
            ("shot_003", 200, 300, "mask_reveal"),
            ("shot_004", 300, 400, "resolve"),
        ]
    ):
        shots.append(
            {
                "id": shot_id,
                "start_ms": start,
                "end_ms": end,
                "on_screen_text": [],
                "composition_tokens": ["center_anchor"],
                "camera_plan": {
                    "rig_id": "rig_ui",
                    "framing": "medium",
                    "motion": "linear_slide" if index % 2 else "static",
                    "focus_behavior": "locked",
                    "no_shake": True,
                },
                "depth_plan": {"layers_z": [], "materials_cues": [], "occlusion_events": []},
                "transition_spec": {"type": transition, "at_ms_global": end, "supporting_fx": [], "notes": None},
                "motion_events": [],
                "micro_choreography": [
                    {
                        "id": f"step_{index}",
                        "at_ms": start,
                        "at_frame": int(round(start * 30 / 1000)),
                        "target": f"layer_{index}",
                        "action": "enter",
                        "channels": ["x", "opacity"],
                        "from": {"x": -20, "opacity": 0},
                        "to": {"x": 0, "opacity": 1},
                        "duration_ms": 80,
                        "ease": "expoOut",
                        "notes": "structural entrance",
                    }
                ],
            }
        )
    return {
        "schema_version": "1.0.0",
        "video": {"duration_ms": 400, "fps": 30.0, "resolution": {"w": 1080, "h": 1920}, "aspect_ratio": "9:16"},
        "style_system": {
            "style_family": [{"id": "editorial_minimal", "confidence": 0.88, "evidence_refs": ["frame:1", "frame:4"]}],
            "color": {},
            "typography": {},
            "composition": {},
            "motion": {},
            "materials_3d": [],
            "fx": [],
        },
        "camera_rigs": [{"rig_id": "rig_ui", "type": "ui_plate", "parameters": {}, "confidence": 0.9}],
        "shots": shots,
        "evidence": {
            "keyframes": [],
            "timestamps": [],
            "claims": [{"claim_id": "style_1", "label": "editorial_minimal", "confidence": 0.88, "evidence_refs": ["frame:1"], "status": "inferred"}],
        },
        "quality": {"coverage": {}, "warnings": [], "assumptions": []},
        "compiler_targets": {
            "remotion": {"project": {"fps": 30.0, "width": 1080, "height": 1920, "duration_frames": 12}, "scene_boundaries": [], "z_order": []},
            "framer_motion": {"easing_presets": {}, "motion_contracts": {}},
        },
    }


def test_frame_timeline_is_complete_and_evidence_bound():
    timeline = compile_frame_timeline(_feature_pack(), _motionstyle())
    assert [row["frame"] for row in timeline] == list(range(12))
    assert timeline[0]["shot_id"] == "shot_001"
    assert timeline[3]["shot_id"] == "shot_002"
    assert timeline[1]["text_observations"][0]["text"] == "BUY NOW"
    assert timeline[2]["text_observations"] == []
    assert timeline[0]["motion_observation"]["authority"] == "measured"
    assert timeline[11]["motion_observation"] is None
    assert timeline[3]["audio_events"][0]["type"] == "onset_candidate"


def test_shot_gaps_fail_closed():
    pack = _feature_pack()
    pack["shots"][1]["start_frame"] = 4
    with pytest.raises(FrameTimelineError):
        compile_frame_timeline(pack, _motionstyle())


def test_editing_signature_detects_hyper_cadence_and_audio_sync():
    signature = build_editing_signature(_feature_pack(), _motionstyle())
    assert signature["temporal"]["cadence_class"] == "hyper"
    assert signature["temporal"]["shot_count"] == 4
    assert signature["audio"]["cut_onset_sync_ratio"] == 1.0
    assert signature["motion"]["provider_available"] is True


def test_structural_template_strips_literal_source_copy_and_validates():
    template, timeline = compile_editing_template(
        _feature_pack(), _motionstyle(), replication_mode="STRUCTURAL_TEMPLATE"
    )
    validate_editing_template(template)
    payload = json.dumps(template, ensure_ascii=False)
    assert "BUY NOW" not in payload
    assert "50% OFF" not in payload
    assert template["replication_mode"] == "STRUCTURAL_TEMPLATE"
    assert template["qa"]["literal_copy_leakage"] is False
    assert len(timeline) == 12
    text_slots = [slot for slot in template["slots"] if slot["media_type"] == "text"]
    assert text_slots
    assert all(slot["source_binding"] is None for slot in text_slots)


def test_exact_template_preserves_observed_source_binding():
    template, _ = compile_editing_template(
        _feature_pack(), _motionstyle(), replication_mode="RECONSTRUCT_EXACT"
    )
    validate_editing_template(template)
    payload = json.dumps(template, ensure_ascii=False)
    assert "BUY NOW" in payload
    assert "50% OFF" in payload
    assert any(item["class"] == "SOURCE_LOCK" for item in template["invariants"])


def test_style_transfer_is_content_independent_and_deterministic():
    template_a, _ = compile_editing_template(
        _feature_pack(), _motionstyle(), replication_mode="STYLE_TRANSFER"
    )
    template_b, _ = compile_editing_template(
        _feature_pack(), _motionstyle(), replication_mode="STYLE_TRANSFER"
    )
    validate_editing_template(template_a)
    assert template_a["content_hash"] == template_b["content_hash"]
    assert "BUY NOW" not in json.dumps(template_a, ensure_ascii=False)
    copy_slots = [slot for slot in template_a["slots"] if slot["role"] == "PRIMARY_COPY"]
    assert len(copy_slots) == 1


def test_content_hash_detects_mutation():
    template, _ = compile_editing_template(
        _feature_pack(), _motionstyle(), replication_mode="STRUCTURAL_TEMPLATE"
    )
    tampered = copy.deepcopy(template)
    tampered["qa"]["warnings"].append("tampered")
    with pytest.raises(EditingTemplateError):
        validate_editing_template(tampered)


def test_unsupported_mode_fails_closed():
    with pytest.raises(EditingTemplateError):
        compile_editing_template(_feature_pack(), _motionstyle(), replication_mode="MAGIC_CLONE")
