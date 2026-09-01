from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "forensics/references/screenrecording_20260826/golden/s04/s04_contract.json"
CURRENT = ROOT / "forensics/references/screenrecording_20260826/golden/s04/fidelity/s04_fidelity_current.json"
COMPONENT = ROOT / "runtime/remotion/src/golden_s04/S04Cientificamente.tsx"
MEASURED_CAPTIONS = ROOT / "runtime/remotion/src/golden_s04/MeasuredCaptionSystem.tsx"
MEASURED_TRACK = ROOT / "runtime/remotion/src/golden_s04/measuredTrack.ts"
SPEC = ROOT / "runtime/remotion/src/golden_s04/s04Spec.ts"
ROOT_TSX = ROOT / "runtime/remotion/src/Root.tsx"
PACKAGE = ROOT / "runtime/remotion/package.json"
WORKFLOW = ROOT / ".github/workflows/remotion-golden-s04.yml"


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def load_current() -> dict:
    return json.loads(CURRENT.read_text(encoding="utf-8"))


def test_s04_visual_duration_uses_frame_authority() -> None:
    contract = load_contract()
    source = contract["source"]
    assert source["frame_count"] == source["end_frame_exclusive"] - source["start_frame"] == 71
    assert source["fps"] == 30
    assert source["width"] == 512
    assert source["height"] == 1108


def test_s04_historical_action_mapping_is_preserved_and_source_local_consistent() -> None:
    contract = load_contract()
    assert contract["schema_version"] == "motion-os.golden-scene/v2"
    assert contract["supersedes"]["schema_version"] == "motion-os.golden-scene/v1"
    actions = contract["historical_actions"]
    assert [action["id"] for action in actions] == ["A022", "A023", "A024", "A025", "A026", "A027", "A028"]
    start = contract["source"]["start_frame"]
    for action in actions:
        for local, source in zip(action["local"], action["source"], strict=True):
            assert source == start + local
    hero = next(action for action in actions if action["id"] == "A024")
    assert hero["local"] == [11, 15, 20]
    assert hero["values"]["scale"] == [0.84, 1.12, 1.0]
    assert hero["authority"] == "EVIDENCE_BOUND_INFERENCE"


def test_unknown_font_and_source_media_do_not_self_promote() -> None:
    contract = load_contract()
    current = load_current()
    assert contract["asset_policy"]["source_and_clean_plate"] == "DRIVE_ONLY"
    assert contract["asset_policy"]["git"] == "CODE_CONTRACTS_AND_TEXT_EVIDENCE_ONLY"
    assert contract["authority"] == "SOURCE_BOUND_PARTIAL_QUALIFICATION_P0P1_CLOSED"
    assert contract["qualification"]["full_9d_fidelity_validated"] is False
    assert current["promotion"]["canonical_template"] is False
    assert current["promotion"]["issue_48_barrier_open"] is True
    assert any("font" in item.lower() and "glyph" in item.lower() for item in contract["unknowns"])
    spec = SPEC.read_text(encoding="utf-8")
    assert "FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN" in spec
    assert "fontIdentity: 'UNKNOWN'" in spec
    assert "sfxIdentity: 'INFERRED_FROM_MIXED_AUDIO'" in spec


def test_s04_renderer_is_frame_driven_and_audio_is_deterministic() -> None:
    component = COMPONENT.read_text(encoding="utf-8")
    assert "useCurrentFrame" in component
    assert "interpolate(frame" in component
    assert "<Audio src={impact}" in component
    assert "Math.random" not in component
    impact = (COMPONENT.parent / "proceduralImpact.ts").read_text(encoding="utf-8")
    assert "Math.random" not in impact
    assert "Math.imul(1664525" in impact
    spec = SPEC.read_text(encoding="utf-8")
    assert "sfxImpact: 8" in spec
    assert "audioOnsetTiming: 'MEASURED_SOURCE_BOUND'" in spec


def test_measured_overlay_uses_source_bound_bbox_track_and_calibration() -> None:
    track = MEASURED_TRACK.read_text(encoding="utf-8")
    captions = MEASURED_CAPTIONS.read_text(encoding="utf-8")
    assert "REFERENCE_MINUS_INPAINTED_CLEAN_PLATE_COLOR_COMPONENT_BBOX" in track
    assert "frame: 10, x: 96, y: 580, width: 110, height: 12" in track
    assert "frame: 38, x: 58, y: 592, width: 422, height: 88" in track
    assert "frame: 68, x: 86, y: 586, width: 364, height: 60" in track
    assert 'lengthAdjust="spacingAndGlyphs"' in captions
    assert "VISIBLE_BOUNDS_CALIBRATION" in captions
    assert "textLengthDelta" in captions
    assert "fontSizeMultiplier" in captions
    assert "textLength={Math.max(1, box.width + calibration.textLengthDelta)}" in captions
    assert "S04_VISIBLE_BOUNDS_CALIBRATION" in captions


def test_composition_and_physical_workflow_are_registered() -> None:
    root = ROOT_TSX.read_text(encoding="utf-8")
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'id="GoldenS04Cientificamente"' in root
    assert 'id="GoldenS04Overlay"' in root
    assert package["dependencies"]["@remotion/media"] == package["dependencies"]["remotion"]
    assert "verify_s04_golden.py" in workflow
    assert "qualify_s04_fidelity.py" in workflow
    assert "test_s04_fidelity_contract.py" in workflow
    assert "GoldenS04Cientificamente" in workflow
    assert "GoldenS04Overlay" in workflow
    assert "--sequence --image-format=png" in workflow
    assert "actions/upload-artifact@" in workflow


def test_v1_history_is_superseded_not_deleted() -> None:
    contract = load_contract()
    current = load_current()
    assert contract["supersedes"]["commit"] == "0790a005f391327b731464d269e42864c64ea4cb"
    assert current["supersedes"]["commit"] == "0790a005f391327b731464d269e42864c64ea4cb"
    assert current["supersedes"]["state"] == "DEFECTS_FOUND_REPAIR_REQUIRED"
    assert set(current["defect_closure"]) >= {
        "S04-DEF-GEOMETRY-SETUP",
        "S04-DEF-GEOMETRY-HERO",
        "S04-DEF-GEOMETRY-TAIL",
        "S04-DEF-AUDIO-ONSET",
    }
    assert current["defect_closure"]["S04-DEF-GEOMETRY-SETUP"].startswith("CLOSED_BY_")
    assert current["defect_closure"]["S04-DEF-COLOR-HERO"] == "OPEN_P2_PROXY_ONLY"


def test_source_bound_fidelity_gate_requires_evidence_and_remains_partial() -> None:
    contract = load_contract()
    current = load_current()
    gates = contract["declared_p0_p1_gates"]
    assert gates["mean_bbox_iou_min"] == 0.90
    assert gates["mean_centroid_error_px_max"] == 3.0
    assert gates["mean_area_error_pct_max"] == 8.0
    assert gates["primary_audio_onset_error_frames_max"] == 1.5
    assert gates["result"] == "PASS"
    assert contract["qualification"]["drive_full_qualification"] == "1D5bfqJhU6-_fJyKTotUz1wl6WT8T7l4Q"
    assert contract["qualification"]["artifact_id"] == 9734987644
    assert contract["qualification"]["renderer_head"] == "0790a005f391327b731464d269e42864c64ea4cb"
    assert current["promotion"]["p0_p1_measured_layout_audio_repair_closed"] is True
    assert current["promotion"]["full_9d_fidelity_validated"] is False


def test_mean_layout_pass_cannot_be_reinterpreted_as_exact_glyph_fidelity() -> None:
    contract = load_contract()
    current = load_current()
    setup = current["post_repair"]["setup"]
    assert setup["mean_bbox_iou"] >= current["thresholds"]["mean_bbox_iou_min"]
    assert setup["min_bbox_iou"] < current["thresholds"]["mean_bbox_iou_min"]
    assert contract["adversarial_ceiling"]["setup_worst_frame_iou"] == setup["min_bbox_iou"]
    assert contract["adversarial_ceiling"]["status"] == "P2_FIDELITY_CEILING_NOT_ACTION_LAYOUT_BLOCKER"
    assert current["adversarial_residuals"][0]["worst_local_frame"] == 66
    assert "exact original font identity and glyph morphology" in current["blocked_dimensions"]


def test_template_policy_preserves_behavior_without_source_locking_literal_content() -> None:
    contract = load_contract()
    policy = contract["template_policy"]
    assert "measured screen-space trajectories" in policy["preserve"]
    assert "shared-caption-parent behavioral relationship" in policy["preserve"]
    assert "literal caption copy" in policy["do_not_source_lock_as_reusable_truth"]
    assert "unknown original font identity" in policy["do_not_source_lock_as_reusable_truth"]
