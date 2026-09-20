import json
from pathlib import Path

import pytest
from jsonschema import validate

from src.normalization.motionstyle import normalize_feature_pack

ROOT = Path(__file__).resolve().parents[1]


def load_schema():
    return json.loads((ROOT / "schemas/motionstyle2json.schema.json").read_text())


def automotive_pack(with_measured_events=True, with_transition=True):
    events = []
    if with_measured_events:
        actions = [
            ("camera_move", ["x", "z", "yaw"]),
            ("parallax_shift", ["x", "z"]),
            ("roto_lock", ["mask"]),
            ("focus_pull", ["focus"]),
            ("speed_ramp", ["velocity"]),
            ("occlude", ["occlusion"]),
            ("cross_plane", ["z", "occlusion"]),
            ("reveal", ["mask", "opacity"]),
            ("camera_move", ["z", "yaw"]),
            ("speed_ramp", ["velocity"]),
            ("material_highlight", ["glow", "color"]),
            ("settle", ["x", "y", "z", "yaw"]),
        ]
        for i, (action, channels) in enumerate(actions):
            events.append({
                "shot_id": "S01",
                "id": f"ev_{i:02d}",
                "at_ms": i * 70,
                "at_frame": round(i * 70 * 30 / 1000),
                "target": "hero" if i < 2 or i > 7 else "wheel_aperture",
                "action": action,
                "channels": channels,
                "from": {},
                "to": {},
                "duration_ms": 70,
                "ease": "ease_in_out_cubic",
                "notes": "measured fixture event",
            })
    transitions = []
    if with_transition:
        transitions.append({
            "shot_id": "S01",
            "approach": {"camera_motion": "dolly_in", "hero_lock": True},
            "feature_acquisition": {"target": "wheel", "tracking": "evidence_bound"},
            "transformation": {"operation": "aperture_open"},
            "crossing": {"plane": "wheel_aperture", "occlusion_threshold": 1.0},
            "handoff": {"motion_vector_match": True},
            "resolve": {"center_lock": True},
            "focus_plane": {"from": "wheel", "to": "incoming_hero"},
            "occlusion_pct": {"from": 0, "to": 100},
            "mask_topology": "circular",
            "screen_anchor": {"x": 0.5, "y": 0.52},
            "motion_vector": {"x": 0.1, "y": 0.0, "z": -1.0},
            "speed_curve": {"type": "accelerate_then_settle"},
            "motion_blur": {"direction": "radial_directional"},
            "incoming_scene_relation": "behind_aperture",
            "audio_impulse": {"kind": "transient", "at_ms": 760},
            "confidence": 0.91,
            "evidence_refs": ["KF01", "KF02"],
        })
    return {
        "video_meta": {"duration_ms": 1000, "fps": 30, "resolution": {"w": 1080, "h": 1920}, "aspect_ratio": "9:16"},
        "shots": [{"id": "S01", "start_ms": 0, "end_ms": 1000, "start_frame": 0, "end_frame": 29, "confidence": 1.0, "method": "fixture", "hero_plan": {"target": "car", "transform_6dof": {"x": 0, "y": 0, "z": 0, "yaw": 0, "pitch": 0, "roll": 0}, "screen_anchor": {"x": .5, "y": .6}, "identity_lock": True}}],
        "keyframes": [{"id": "KF01", "shot_id": "S01", "frame": 8, "at_ms": 267, "sha256": "a"}, {"id": "KF02", "shot_id": "S01", "frame": 23, "at_ms": 767, "sha256": "b"}],
        "ocr": [], "color_stats": {}, "layout_stats": {"pattern": "centered_hero"},
        "motion_stats": {"camera_motion": {"classification": "camera_dominant", "primitive": "arc_pan", "rig_id": "rigD_automotive_orbit", "framing": "medium", "focus_behavior": "rack_focus", "no_shake": True, "transform_6dof": {"x": 1.0, "y": .3, "z": -2.0, "yaw": 18, "pitch": -2, "roll": 0}, "pivot_target": "car", "screen_anchor": {"x": .5, "y": .55}, "velocity_curve": {"type": "ease_in_out"}}},
        "asset_stats": {}, "audio_stats": {}, "fx_stats": {"labels": ["motion_blur", "roto"]},
        "transition_stats": transitions,
        "micro_choreography": events,
        "warnings": [],
    }


def test_automotive_causal_fixture_is_schema_valid():
    doc = normalize_feature_pack(automotive_pack())
    validate(doc, load_schema())


def test_6dof_and_automotive_rig_survive_normalization():
    doc = normalize_feature_pack(automotive_pack())
    camera = doc["shots"][0]["camera_plan"]
    assert camera["rig_id"] == "rigD_automotive_orbit"
    assert camera["motion"] == "arc_pan"
    assert camera["focus_behavior"] == "rack_focus"
    assert camera["pivot_target"] == "car"
    assert camera["transform_6dof"] == {"x": 1.0, "y": .3, "z": -2.0, "yaw": 18, "pitch": -2, "roll": 0}


def test_causal_transition_survives_normalization_without_flattening():
    doc = normalize_feature_pack(automotive_pack())
    causal = doc["shots"][0]["transition_spec"]["causal"]
    assert causal["feature_acquisition"]["target"] == "wheel"
    assert causal["crossing"]["plane"] == "wheel_aperture"
    assert causal["incoming_scene_relation"] == "behind_aperture"
    assert causal["occlusion_pct"] == {"from": 0, "to": 100}
    assert causal["confidence"] == pytest.approx(.91)


def test_measured_micro_choreography_is_preserved_and_meets_gate():
    doc = normalize_feature_pack(automotive_pack())
    shot = doc["shots"][0]
    assert len(shot["micro_choreography"]) >= 12
    assert {x["action"] for x in shot["micro_choreography"]} >= {"camera_move", "speed_ramp", "roto_lock", "cross_plane", "occlude"}
    assert not any("micro_choreography has <12" in a for a in doc["quality"]["assumptions"])


def test_missing_measured_events_are_not_fabricated_to_hit_twelve():
    doc = normalize_feature_pack(automotive_pack(with_measured_events=False))
    assert doc["shots"][0]["micro_choreography"] == []
    assert any("micro_choreography has <12 measured steps; no synthetic events were invented" in a for a in doc["quality"]["assumptions"])


def test_missing_causal_evidence_stays_null_not_invented():
    doc = normalize_feature_pack(automotive_pack(with_transition=False))
    assert doc["shots"][0]["transition_spec"]["causal"] is None


def test_generativ_video_compiler_exposes_boundary_condition_invariants():
    doc = normalize_feature_pack(automotive_pack())
    gv = doc["compiler_targets"]["generative_video"]
    assert "plausible spatial trajectory" in gv["boundary_condition_rule"]
    assert "hero_identity" in gv["preserve"]
    assert "transition_geometry" in gv["preserve"]


def test_schema_rejects_invalid_6dof_type():
    doc = normalize_feature_pack(automotive_pack())
    doc["shots"][0]["camera_plan"]["transform_6dof"]["yaw"] = "eighteen degrees"
    with pytest.raises(Exception):
        validate(doc, load_schema())


def test_schema_rejects_unknown_micro_choreography_channel():
    doc = normalize_feature_pack(automotive_pack())
    doc["shots"][0]["micro_choreography"][0]["channels"] = ["magic_camera"]
    with pytest.raises(Exception):
        validate(doc, load_schema())
