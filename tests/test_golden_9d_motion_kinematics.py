from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "qualification/golden_9d/compile_motion_kinematics.py"
MANIFEST = ROOT / "qualification/golden_9d/golden_motion_sources.json"


def load_module():
    spec = importlib.util.spec_from_file_location("golden_motion_kinematics", COMPILER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_keyframe_parser_and_interpolator_preserve_frame_geometry():
    m = load_module()
    text = "const TRACK:KF[]=[{frame:0,x:0,y:10,width:20,height:30},{frame:2,x:4,y:6,width:24,height:34}];"
    rows = m.parse_keyframed_boxes(text, "TRACK")
    out = m.interpolate_keyframes(rows)
    assert [r["frame"] for r in out] == [0, 1, 2]
    assert out[1]["x"] == 2
    assert out[1]["y"] == 8
    assert out[1]["width"] == 22
    assert out[1]["height"] == 32


def test_indexed_tuple_parser_preserves_nulls_and_factor_proxy():
    m = load_module()
    text = "const FACTOR:(RawFactor|null)[]=[null,[1,2,3,4,0.5],[2,3,3,4,1]];"
    rows = m.parse_indexed_tuples(text, "FACTOR", factor=True)
    assert rows[0] is None
    assert rows[1] == {"frame": 1, "x": 1.0, "y": 2.0, "width": 3.0, "height": 4.0, "opacity_proxy": 0.5}
    assert rows[2]["opacity_proxy"] == 1.0


def test_empty_track_uses_python_false_and_does_not_crash():
    m = load_module()
    result = m.kinematics([], 30, "TEST")
    assert result == {"authority": "TEST", "visible": False}


def test_descending_screen_y_is_valid_physical_upward_translation_when_size_is_stable():
    m = load_module()
    rows = [
        {"frame": 0, "x": 10.0, "y": 100.0, "width": 20.0, "height": 20.0},
        {"frame": 1, "x": 10.0, "y": 90.0, "width": 20.0, "height": 20.0},
        {"frame": 2, "x": 10.0, "y": 80.0, "width": 20.0, "height": 20.0},
        {"frame": 3, "x": 10.0, "y": 70.0, "width": 20.0, "height": 20.0},
        {"frame": 4, "x": 10.0, "y": 60.0, "width": 20.0, "height": 20.0},
    ]
    result = m.kinematics(rows, 30, "TEST", canvas={"width": 512, "height": 1108}, projection_mode="FULL_FRAME_NO_INTERPOLATION")
    assert result["samples"][1]["direction"] == "UP"
    assert result["samples"][1]["transform_class"] == "TRANSLATION_DOMINANT"
    assert result["metrics"]["max_speed_px_per_frame"] == 10.0


def test_bbox_growth_cannot_be_mislabeled_as_centroid_translation():
    m = load_module()
    rows = [
        {"frame": 0, "x": 100.0, "y": 530.0, "width": 336.0, "height": 32.0},
        {"frame": 1, "x": 96.0, "y": 514.0, "width": 340.0, "height": 64.0},
        {"frame": 2, "x": 92.0, "y": 500.0, "width": 348.0, "height": 92.0},
        {"frame": 3, "x": 84.0, "y": 496.0, "width": 362.0, "height": 104.0},
    ]
    result = m.kinematics(rows, 30, "TEST", projection_mode="FULL_FRAME_NO_INTERPOLATION")
    assert any(s.get("transform_class") == "SCALE_OR_REVEAL_DOMINANT" for s in result["samples"])
    segment = result["motion_segments"][0]
    assert segment["dominant_transform_class"] in {"SCALE_OR_REVEAL_DOMINANT", "MIXED_TRANSLATION_AND_SCALE"}
    assert "BBOX_SHAPE_CHANGE_CONFLATES_TRANSLATION_WITH_SCALE_OR_REVEAL" in segment["caveats"]
    assert segment["curve_proxy_confidence"] == "LOW"


def test_visibility_build_caps_translation_curve_authority():
    m = load_module()
    rows = [
        {"frame": 0, "x": 96.0, "y": 580.0, "width": 110.0, "height": 12.0, "opacity_proxy": 0.32},
        {"frame": 1, "x": 92.0, "y": 577.0, "width": 354.0, "height": 51.0, "opacity_proxy": 1.0},
        {"frame": 2, "x": 89.0, "y": 578.0, "width": 359.0, "height": 56.0, "opacity_proxy": 1.0},
        {"frame": 3, "x": 86.0, "y": 580.0, "width": 365.0, "height": 60.0, "opacity_proxy": 1.0},
        {"frame": 4, "x": 82.0, "y": 582.0, "width": 374.0, "height": 62.0, "opacity_proxy": 1.0},
    ]
    result = m.kinematics(rows, 30, "TEST", projection_mode="FULL_FRAME_NO_INTERPOLATION")
    assert result["samples"][1]["transform_class"] == "SCALE_OR_REVEAL_DOMINANT"
    segment = result["motion_segments"][0]
    assert segment["dominant_transform_class"] == "SCALE_OR_REVEAL_DOMINANT"
    assert segment["curve_authority"] == "BBOX_CENTROID_SPEED_PROXY_NOT_PURE_TRANSLATION_CURVE"


def test_boundary_clipping_caps_curve_authority_instead_of_inventing_hidden_easing():
    m = load_module()
    rows = [
        {"frame": 0, "x": 12.0, "y": 100.0, "width": 30.0, "height": 30.0},
        {"frame": 1, "x": 6.0, "y": 100.0, "width": 30.0, "height": 30.0},
        {"frame": 2, "x": 0.0, "y": 100.0, "width": 28.0, "height": 30.0},
        {"frame": 3, "x": 0.0, "y": 100.0, "width": 18.0, "height": 30.0},
        {"frame": 4, "x": 0.0, "y": 100.0, "width": 8.0, "height": 30.0},
    ]
    result = m.kinematics(rows, 30, "TEST", canvas={"width": 512, "height": 1108}, projection_mode="FULL_FRAME_NO_INTERPOLATION")
    assert result["boundary_clipped_sample_count"] == 3
    segment = result["motion_segments"][0]
    assert segment["screen_boundary_clipped"] is True
    assert segment["curve_proxy_confidence"] == "LOW"
    assert segment["curve_authority"] == "VISIBLE_OUTPUT_CLIPPED_PROXY_NOT_HIDDEN_OBJECT_CURVE"
    assert "SCREEN_BOUNDARY_CLIPPING_DISTORTS_VISIBLE_BBOX_KINEMATICS" in segment["caveats"]


def test_scene_clip_rect_can_expose_bottom_reveal_hidden_by_full_canvas():
    m = load_module()
    rows = [
        {"frame": 0, "x": 30.0, "y": 858.0, "width": 230.0, "height": 156.0},
        {"frame": 1, "x": 30.0, "y": 846.0, "width": 230.0, "height": 168.0},
        {"frame": 2, "x": 30.0, "y": 836.0, "width": 230.0, "height": 178.0},
        {"frame": 3, "x": 30.0, "y": 828.0, "width": 230.0, "height": 186.0},
    ]
    result = m.kinematics(rows, 30, "TEST", clip_rect=[0, 0, 512, 1014], projection_mode="FULL_FRAME_NO_INTERPOLATION")
    assert result["boundary_clipped_sample_count"] == 4
    assert all("BOTTOM" in s["screen_clip_flags"] for s in result["samples"])
    assert result["motion_segments"][0]["curve_authority"] == "VISIBLE_OUTPUT_CLIPPED_PROXY_NOT_HIDDEN_OBJECT_CURVE"


def test_keyframe_linear_projection_cannot_claim_original_easing():
    m = load_module()
    rows = [
        {"frame": i, "x": float(i * i), "y": 10.0, "width": 20.0, "height": 20.0}
        for i in range(6)
    ]
    result = m.kinematics(rows, 30, "TEST", projection_mode="KEYFRAME_LINEAR_RENDERER_PROJECTION")
    assert result["motion_segments"]
    for segment in result["motion_segments"]:
        assert segment["curve_proxy_confidence"] in {"LOW", "NONE"}
        assert "KEYFRAME_LINEAR_INTERPOLATION_CAN_SHAPE_SPEED_PROFILE" in segment["caveats"]
        assert segment["curve_authority"] != "ORIGINAL_AFTER_EFFECTS_GRAPH_EDITOR"


def test_source_lock_range_is_measured_but_excluded_from_structural_motion_grammar():
    m = load_module()
    rows = [
        {"frame": f, "x": 10.0, "y": float(100 - f), "width": 20.0, "height": 20.0}
        for f in range(84, 92)
    ]
    result = m.kinematics(
        rows,
        30,
        "TEST",
        canvas={"width": 512, "height": 1108},
        projection_mode="FULL_FRAME_NO_INTERPOLATION",
        structural_exclude_ranges=[[87, 91]],
    )
    assert result["structural_excluded_sample_count"] == 5
    assert next(s for s in result["samples"] if s["frame"] == 87)["structural_template_eligible"] is False
    assert any(not seg["structural_template_eligible"] for seg in result["motion_segments"])


def test_motion_manifest_is_pinned_to_live_golden_heads_and_s16_reflow_is_source_lock():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["schema_version"] == "motion-os.golden-motion-sources/v2"
    expected = {
        "S04_CIENTIFICAMENTE": "8ec35a259399d7b196b40627d782315a019e65e2",
        "S11_UI_LIST": "988e91893cb498f720b9c2656b3d6d85f2d56300",
        "S14_AUDIO_VISUAL_TEXTO": "12592bd8f8149767fafcb0ad0aa6036250ce540c",
        "S16_FACTOR_X": "8e6fcb79d0d7958c0f023f128297059c97a7e674",
    }
    for scene, sha in expected.items():
        assert manifest["scenes"][scene]["ref"] == sha
    s16 = manifest["scenes"]["S16_FACTOR_X"]
    assert s16["projection_mode"] == "FULL_FRAME_NO_INTERPOLATION"
    assert s16["structural_exclude_ranges"] == [[87, 91]]
    assert s16["clip_rect"] == [0, 0, 512, 1014]


def test_curve_authority_is_explicitly_behavioral_not_original_after_effects_graph_editor():
    source = COMPILER.read_text()
    assert "BEHAVIORAL_PROXY_ONLY_NOT_ORIGINAL_AFTER_EFFECTS_GRAPH_EDITOR" in source
    assert "RENDERER_PROJECTION_BEHAVIOR_PROXY_NOT_MEASURED_ORIGINAL_EASING" in source
    assert "VISIBLE_OUTPUT_CLIPPED_PROXY_NOT_HIDDEN_OBJECT_CURVE" in source
    assert "BBOX_CENTROID_SPEED_PROXY_NOT_PURE_TRANSLATION_CURVE" in source
