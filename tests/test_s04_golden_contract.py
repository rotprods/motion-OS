from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "forensics/references/screenrecording_20260826/golden/s04/s04_contract.json"
COMPONENT = ROOT / "runtime/remotion/src/golden_s04/S04Cientificamente.tsx"
MEASURED_CAPTIONS = ROOT / "runtime/remotion/src/golden_s04/MeasuredCaptionSystem.tsx"
MEASURED_TRACK = ROOT / "runtime/remotion/src/golden_s04/measuredTrack.ts"
SPEC = ROOT / "runtime/remotion/src/golden_s04/s04Spec.ts"
ROOT_TSX = ROOT / "runtime/remotion/src/Root.tsx"
PACKAGE = ROOT / "runtime/remotion/package.json"
WORKFLOW = ROOT / ".github/workflows/remotion-golden-s04.yml"


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_s04_visual_duration_uses_frame_authority() -> None:
    contract = load_contract()
    source = contract["source"]
    assert source["frame_count"] == source["end_frame_exclusive"] - source["start_frame"] == 71
    assert source["fps"] == 30
    assert source["width"] == 512
    assert source["height"] == 1108


def test_s04_action_mapping_is_source_local_consistent() -> None:
    contract = load_contract()
    start = contract["source"]["start_frame"]
    for action in contract["actions"]:
        for local, source in zip(action["local"], action["source"], strict=True):
            assert source == start + local
    hero = next(action for action in contract["actions"] if action["id"] == "A024")
    assert hero["local"] == [11, 15, 20]
    assert hero["values"]["scale"] == [0.84, 1.12, 1.0]


def test_unknown_font_and_source_media_do_not_self_promote() -> None:
    contract = load_contract()
    assert contract["asset_policy"]["source_and_clean_plate"] == "DRIVE_ONLY"
    assert contract["asset_policy"]["git"] == "CODE_CONTRACTS_AND_TEXT_EVIDENCE_ONLY"
    # Lifecycle may advance from BLOCKED -> REPAIR_IN_PROGRESS as evidence is
    # gathered, but no contract-only change may self-promote to fidelity authority.
    assert contract["authority"] == "STRUCTURAL_RENDER_EXECUTED_SOURCE_FIDELITY_REPAIR_IN_PROGRESS"
    assert "FIDELITY_VALIDATED" not in contract["authority"]
    spec = SPEC.read_text(encoding="utf-8")
    assert "FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN" in spec
    assert "sourceFidelity: 'BLOCKED_UNTIL_9D_DIFF_REPAIR_PASS'" in spec
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
    # The source-visible bbox remains the target; renderer-specific glyph metrics
    # are an explicit calibration layer rather than a hidden magic number.
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


def test_inventory_discrepancy_history_is_preserved_and_extended() -> None:
    contract = load_contract()
    discrepancies = contract["measured_discrepancies"]
    ids = [item["id"] for item in discrepancies]
    # Historical discrepancy identity is append-only. New physical findings are
    # allowed and expected to extend it; deleting the old three would be a regression.
    assert ids[:3] == ["S04-DISC-001", "S04-DISC-002", "S04-DISC-003"]
    assert {"S04-DISC-004", "S04-DISC-005"}.issubset(ids)
    by_id = {item["id"]: item for item in discrepancies}
    assert by_id["S04-DISC-001"]["inventory_value"] == 146
    assert by_id["S04-DISC-001"]["measured_reference_value"] == 145
    assert by_id["S04-DISC-001"]["status"] == "RENDERER_REPAIRED_GRAPH_BACKPORT_OPEN"
    assert by_id["S04-DISC-002"]["status"] == "RENDERER_REPAIRED_GRAPH_BACKPORT_OPEN"
    assert by_id["S04-DISC-003"]["status"] == "RENDERER_REPAIRED_GRAPH_BACKPORT_OPEN"
    assert by_id["S04-DISC-004"]["status"] == "EVIDENCE_BOUND_STRUCTURAL_INFERENCE"
    assert by_id["S04-DISC-005"]["status"] == "RENDERER_REPAIR_IN_PROGRESS"
    assert contract["renderer_repairs"]["caption_layout"]["authority"] == "MEASURED_HEURISTIC"
    assert contract["renderer_repairs"]["caption_visible_bounds"]["authority"] == "MEASURED_HEURISTIC"
    assert contract["renderer_repairs"]["sfx_onset_alignment"]["authority"] == "MEASURED_SOURCE_BOUND_TIMING_SFX_CLASS_INFERRED"


def test_source_bound_fidelity_gate_cannot_be_satisfied_by_contract_evolution_alone() -> None:
    contract = load_contract()
    gates = contract["qa_gates"]
    assert gates["promotion_veto"] == "P0_OR_P1_DEFECT"
    assert "mean bbox IoU >= 0.90 per caption role" in gates["source_bound_geometry"]
    assert "mean centroid error <= 3px per role" in gates["source_bound_geometry"]
    assert "mean area error <= 8% per role" in gates["source_bound_geometry"]
    assert "primary transient timing absolute error <= 1.5 frames; class/stem identity excluded" in gates["source_bound_audio"]
    assert contract["fidelity_baseline"]["authority"] == "MEASURED_SOURCE_BOUND_LOCAL_RUN"
