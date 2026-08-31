from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'forensics/references/screenrecording_20260826/golden/s11/s11_contract.json'
MEASURED = ROOT / 'forensics/references/screenrecording_20260826/golden/s11/fidelity/s11_measured_visible_track.json'
ROOT_TSX = ROOT / 'runtime/remotion/src/Root.tsx'
SPEC_TS = ROOT / 'runtime/remotion/src/golden_s11/s11Spec.ts'
COMP_TSX = ROOT / 'runtime/remotion/src/golden_s11/S11UiList.tsx'
TRACK_TS = ROOT / 'runtime/remotion/src/golden_s11/sourceMeasuredTrack.ts'


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


def test_remotion_registration_and_spec_are_semantically_bound():
    root=ROOT_TSX.read_text()
    spec=SPEC_TS.read_text()
    assert "from './golden_s11'" in root
    assert 'id={S11_SPEC.compositionId}' in root
    assert 'component={S11UiList}' in root
    assert 'id={S11_SPEC.overlayCompositionId}' in root
    assert 'component={S11Overlay}' in root
    assert "compositionId: 'GoldenS11UiList'" in spec
    assert "overlayCompositionId: 'GoldenS11Overlay'" in spec
    assert "sceneId: 'S11_UI_LIST'" in spec
    assert "sourceFidelity: 'BLOCKED_UNTIL_SOURCE_BOUND_DIFF'" in spec


def test_audio_domain_is_not_silently_dropped():
    source=COMP_TSX.read_text()
    assert 'Sequence from={54}' in source
    assert 'Sequence from={85}' in source
    assert 'Sequence from={93}' in source
    assert 'Sequence from={102}' in source
    assert 'makeUiHitDataUri' in source


def test_source_bound_repair_uses_measured_visible_tracks_not_generic_stagger():
    measured=json.loads(MEASURED.read_text())
    assert measured['authority']=='MEASURED_SOURCE_VISIBLE_HEURISTIC'
    assert measured['first_visible']=={'row_x':77,'row_diamond':82,'row_megaphone':88}
    assert measured['tracks']['pill'][0]==[0,98,530,336,32]
    assert measured['tracks']['pill'][-1]==[129,42,322,448,141]
    assert measured['tracks']['boxed_absolutamente'][0]==[54,190,424,212,30]
    assert measured['tracks']['boxed_absolutamente'][-1]==[129,182,280,235,34]
    source=COMP_TSX.read_text()
    track=TRACK_TS.read_text()
    assert "from './sourceMeasuredTrack'" in source
    assert 'measuredS11(frame)' in source
    assert "rowFirstVisible:{x:77,diamond:82,megaphone:88}" in track


def test_measured_track_keeps_original_project_unknowns_explicit():
    measured=json.loads(MEASURED.read_text())
    unknowns=set(measured['unknowns'])
    assert 'exact fonts' in unknowns
    assert 'original AE parenting' in unknowns
    assert 'original isolated SFX' in unknowns
