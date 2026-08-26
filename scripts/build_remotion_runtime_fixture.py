from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.compilers.remotion import compile_remotion_scene_spec, validate_scene_coverage


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runtime" / "remotion" / "src" / "runtimeSpec.json"
EVIDENCE = ROOT / "runtime" / "remotion" / "compiler_evidence.json"


def _shot(shot_id: str, start_ms: int, transition: str, camera_motion: str, event_frame: int) -> dict:
    return {
        "id": shot_id,
        "start_ms": start_ms,
        "end_ms": start_ms + 1000,
        "on_screen_text": [],
        "camera_plan": {
            "rig_id": "rigC_ui_plate",
            "framing": "medium",
            "motion": camera_motion,
            "z_drift": 0.0,
            "focus_behavior": "locked",
            "no_shake": True,
        },
        "depth_plan": {
            "layers_z": [
                {"id": "background", "z_index": 0, "parallax_ratio": 0.0},
                {"id": "subject", "z_index": 10, "parallax_ratio": 0.25},
                {"id": "ui", "z_index": 20, "parallax_ratio": 0.0},
            ],
            "materials_cues": [],
            "occlusion_events": [],
        },
        "transition_spec": {
            "type": transition,
            "at_ms_global": start_ms,
            "supporting_fx": [],
            "notes": "runtime proof transition",
        },
        "motion_events": [],
        "micro_choreography": [
            {
                "id": f"{shot_id}_event",
                "at_ms": round((event_frame % 30) * 1000 / 30),
                "at_frame": event_frame,
                "target": "runtime_orbit",
                "action": "material_highlight",
                "channels": ["glow", "scale"],
                "from": {"glow": 0.0, "scale": 0.95},
                "to": {"glow": 1.0, "scale": 1.0},
                "duration_ms": 180,
                "ease": "ease_out_cubic",
                "notes": "visible runtime event pulse",
            }
        ],
    }


def build_doc() -> dict:
    return {
        "schema_version": "1.0.0",
        "video": {
            "duration_ms": 3000,
            "fps": 30,
            "resolution": {"w": 640, "h": 360},
            "aspect_ratio": "16:9",
        },
        "style_system": {
            "style_family": [{"id": "editorial_minimal", "confidence": 1.0, "evidence_refs": ["fixture:runtime"]}],
            "color": {},
            "typography": {},
            "composition": {},
            "motion": {},
            "materials_3d": [],
            "fx": [],
        },
        "camera_rigs": [{"rig_id": "rigC_ui_plate", "type": "ui_plate", "parameters": {}, "confidence": 1.0}],
        "shots": [
            _shot("S01", 0, "cut", "static", 12),
            _shot("S02", 1000, "slide", "linear_slide", 43),
            _shot("S03", 2000, "match_move", "micro_drift", 75),
        ],
        "evidence": {"keyframes": [], "timestamps": [], "claims": []},
        "quality": {"coverage": {}, "warnings": [], "assumptions": ["runtime verification fixture, not creative benchmark"]},
        "compiler_targets": {
            "remotion": {
                "project": {"fps": 30, "width": 640, "height": 360, "duration_frames": 90},
                "scene_boundaries": [
                    {"shot_id": "S01", "from_frame": 0, "to_frame": 29},
                    {"shot_id": "S02", "from_frame": 30, "to_frame": 59},
                    {"shot_id": "S03", "from_frame": 60, "to_frame": 89},
                ],
                "z_order": ["ui", "subject", "background"],
            },
            "framer_motion": {"easing_presets": {}, "motion_contracts": {}},
        },
    }


def main() -> int:
    doc = build_doc()
    spec = compile_remotion_scene_spec(doc)
    errors = validate_scene_coverage(spec)
    if errors:
        raise SystemExit(f"scene coverage failed: {errors}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
    OUT.write_text(payload, encoding="utf-8")
    evidence = {
        "schema": "motion-os.remotion-compiler-evidence/v1",
        "source": "scripts/build_remotion_runtime_fixture.py",
        "compiler": "src.compilers.remotion.compile_remotion_scene_spec",
        "spec_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "project": spec["project"],
        "scene_count": len(spec["scenes"]),
        "scene_ids": [s["id"] for s in spec["scenes"]],
        "event_count": sum(len(s["events"]) for s in spec["scenes"]),
        "coverage_errors": errors,
        "authority": "deterministic_compiler_fixture",
        "creative_authority": "none",
    }
    EVIDENCE.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
