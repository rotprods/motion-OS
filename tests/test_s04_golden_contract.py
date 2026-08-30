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
    assert contract["authority"] == "STRUCTURAL_RENDER_EXECUTED_SOURCE_FIDELITY_BLOCKED"
    spec = SPEC.read_text(encoding="utf-8")
    assert "FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN" in spec
    assert "sourceFidelity: 'BLOCKED_UNTIL_9D_DIFF'" in spec


def test_s04_renderer_is_frame_driven_and_audio_is_deterministic() -> None:
    component = COMPONENT.read_text(encoding="utf-8")
    assert "useCurrentFrame" in component
    assert "interpolate(frame" in component
    assert "<Audio src={impact}" in component
    assert "Math.random" not in component
    impact = (COMPONENT.parent / "proceduralImpact.ts").read_text(encoding="utf-8")
    assert "Math.random" not in impact
    assert "Math.imul(1664525" in impact


def test_measured_overlay_uses_source_bound_bbox_track() -> None:
    track = MEASURED_TRACK.read_text(encoding="utf-8")
    captions = MEASURED_CAPTIONS.read_text(encoding="utf-8")
    assert "REFERENCE_MINUS_INPAINTED_CLEAN_PLATE_COLOR_COMPONENT_BBOX" in track
    assert "frame: 10, x: 96, y: 580, width: 110, height: 12" in track
    assert "frame: 38, x: 58, y: 592, width: 422, height: 88" in track
    assert "frame: 68, x: 86, y: 586, width: 364, height: 60" in track
    assert 'lengthAdjust="spacingAndGlyphs"' in captions
    assert "textLength={box.width}" in captions


def test_composition_and_physical_workflow_are_registered() -> None:
    root = ROOT_TSX.read_text(encoding="utf-8")
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'id="GoldenS04Cientificamente"' in root
    assert 'id="GoldenS04Overlay"' in root
    assert package["dependencies"]["@remotion/media"] == package["dependencies"]["remotion"]
    assert "verify_s04_golden.py" in workflow
    assert "GoldenS04Cientificamente" in workflow
    assert "GoldenS04Overlay" in workflow
    assert "--sequence --image-format=png" in workflow
    assert "actions/upload-artifact@" in workflow


def test_inventory_discrepancies_are_preserved_and_renderer_repaired() -> None:
    contract = load_contract()
    discrepancies = contract["measured_discrepancies"]
    assert [item["id"] for item in discrepancies] == ["S04-DISC-001", "S04-DISC-002", "S04-DISC-003"]
    assert discrepancies[0]["inventory_value"] == 146
    assert discrepancies[0]["measured_reference_value"] == 145
    assert all(item["status"] == "RENDERER_REPAIRED_GRAPH_BACKPORT_OPEN" for item in discrepancies)
    assert contract["renderer_repairs"]["caption_layout"]["authority"] == "MEASURED_HEURISTIC"
