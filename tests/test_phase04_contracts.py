import json
from pathlib import Path

from jsonschema import Draft202012Validator, validate

ROOT = Path(__file__).resolve().parents[1]


def load_json(rel):
    return json.loads((ROOT / rel).read_text())


def test_phase04_schemas_are_valid_draft_2020_12():
    for rel in ["schemas/feature_pack.schema.json", "schemas/motionstyle2json.schema.json"]:
        Draft202012Validator.check_schema(load_json(rel))


def test_feature_pack_minimal_contract():
    schema = load_json("schemas/feature_pack.schema.json")
    sample = {
        "schema_version": "1.0.0",
        "video_meta": {
            "duration_ms": 1000,
            "fps": 30,
            "resolution": {"w": 1080, "h": 1920},
            "aspect_ratio": "9:16",
        },
        "shots": [
            {
                "id": "S01",
                "start_ms": 0,
                "end_ms": 1000,
                "start_frame": 0,
                "end_frame": 29,
                "confidence": 1.0,
                "method": "fixture",
            }
        ],
        "keyframes": [
            {"id": "KF01", "shot_id": "S01", "frame": 15, "at_ms": 500, "sha256": "fixture"}
        ],
        "ocr": [],
        "color_stats": {},
        "layout_stats": {},
        "motion_stats": {},
        "asset_stats": {},
        "audio_stats": {},
        "extraction_provenance": [
            {"module": "ingest", "method": "fixture", "version": "1"}
        ],
        "warnings": [],
    }
    validate(sample, schema)


def test_motionstyle2json_minimal_contract():
    schema = load_json("schemas/motionstyle2json.schema.json")
    sample = {
        "schema_version": "1.0.0",
        "video": {
            "duration_ms": 1000,
            "fps": 30,
            "resolution": {"w": 1080, "h": 1920},
            "aspect_ratio": "9:16",
        },
        "style_system": {
            "style_family": [{"id": "editorial_minimal", "confidence": 0.9, "evidence_refs": ["KF01"]}],
            "color": {},
            "typography": {},
            "composition": {},
            "motion": {},
            "materials_3d": [],
            "fx": [],
        },
        "camera_rigs": [{"rig_id": "rigC", "type": "ui_plate", "parameters": {}, "confidence": 1.0}],
        "shots": [
            {
                "id": "S01",
                "start_ms": 0,
                "end_ms": 1000,
                "on_screen_text": [],
                "camera_plan": {
                    "rig_id": "rigC",
                    "framing": "medium",
                    "motion": "static",
                    "focus_behavior": "locked",
                    "no_shake": True,
                },
                "depth_plan": {"layers_z": [], "materials_cues": [], "occlusion_events": []},
                "transition_spec": {"type": "cut", "at_ms_global": 0},
                "motion_events": [],
                "micro_choreography": [],
            }
        ],
        "evidence": {"keyframes": [], "timestamps": [], "claims": []},
        "quality": {"coverage": {}, "warnings": [], "assumptions": ["fixture intentionally minimal"]},
        "compiler_targets": {
            "remotion": {
                "project": {"fps": 30, "width": 1080, "height": 1920, "duration_frames": 30},
                "scene_boundaries": [{"shot_id": "S01", "from_frame": 0, "to_frame": 29}],
                "z_order": ["ui", "subject", "background"],
            },
            "framer_motion": {"easing_presets": {}, "motion_contracts": {}},
        },
    }
    validate(sample, schema)


def test_phase_source_plan_graph_traceability_exists():
    required = [
        "copy_pastes/phase_04_a_extraction_pipeline.md",
        "copy_pastes/phase_04_b_motionstyle2json_master.md",
        "copy_pastes/phase_04_c_reverse_engineer_templates_and_style_dna.md",
        "plans/phase_04_visual_dna_extraction_and_style_compiler.md",
        "plans/PLAN_EVOLUTION_PROTOCOL.md",
        "plans/phase_registry.yaml",
        "architecture/phase_learning_graph.mmd",
        "config/visual_dna_taxonomy.yaml",
    ]
    missing = [rel for rel in required if not (ROOT / rel).exists()]
    assert not missing, f"missing phase-04 traceability files: {missing}"
