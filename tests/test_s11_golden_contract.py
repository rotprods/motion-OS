from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'forensics/references/screenrecording_20260826/golden/s11/s11_contract.json'
ROOT_TSX = ROOT / 'runtime/remotion/src/Root.tsx'
SPEC_TS = ROOT / 'runtime/remotion/src/golden_s11/s11Spec.ts'
COMP_TSX = ROOT / 'runtime/remotion/src/golden_s11/S11UiList.tsx'


def test_s11_source_timing_is_frame_authoritative():
    data=json.loads(CONTRACT.read_text())
    src=data['source']
    assert src['start_frame']==405
    assert src['end_frame_exclusive']==535
    assert src['frame_count']==130
    assert src['fps']==30
    assert src['width']==512 and src['height']==1108


def test_s11_atomic_row_and_word_anchors_are_explicit():
    data=json.loads(CONTRACT.read_text())
    actions={a['id']:a for a in data['actions']}
    assert actions['A061.3']['local']==[50,54,63]
    assert actions['A062.1']['local']==[82,85,88]
    assert actions['A062.2']['local']==[90,93,96]
    assert actions['A062.3']['local']==[99,102,105]


def test_new_source_lock_is_visible_evidence_not_rewritten_history():
    data=json.loads(CONTRACT.read_text())
    discovered=[a for a in data['actions'] if a['id']=='S11-DISC-001'][0]
    assert discovered['authority']=='MEASURED_VISIBLE'
    assert discovered['status']=='NEW_OBSERVABLE_ACTION_NOT_IN_PARENT_INVENTORY'


def test_shared_group_is_hypothesis_not_original_ae_claim():
    data=json.loads(CONTRACT.read_text())
    h=[a for a in data['actions'] if a['id']=='S11-HYP-001'][0]
    assert h['authority']=='EVIDENCE_BOUND_INFERENCE'
    assert h['status']=='RECONSTRUCTION_HYPOTHESIS'


def test_remotion_registration_and_spec_are_explicit():
    root=ROOT_TSX.read_text()
    spec=SPEC_TS.read_text()
    assert 'GoldenS11UiList' in root
    assert 'GoldenS11Overlay' in root
    assert "sceneId: 'S11_UI_LIST'" in spec
    assert "sourceFidelity: 'BLOCKED_UNTIL_SOURCE_BOUND_DIFF'" in spec


def test_audio_domain_is_not_silently_dropped():
    source=COMP_TSX.read_text()
    assert 'Sequence from={54}' in source
    assert 'Sequence from={85}' in source
    assert 'Sequence from={93}' in source
    assert 'Sequence from={102}' in source
    assert 'makeUiHitDataUri' in source
