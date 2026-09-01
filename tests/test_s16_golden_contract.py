from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'forensics/references/screenrecording_20260826/golden/s16/s16_contract.json'
SPEC=ROOT/'runtime/remotion/src/golden_s16/s16Spec.ts'
TRACK=ROOT/'runtime/remotion/src/golden_s16/sourceMeasuredTrack.ts'
COMP=ROOT/'runtime/remotion/src/golden_s16/S16FactorX.tsx'
ROOT_TSX=ROOT/'runtime/remotion/src/Root.tsx'
WORKFLOW=ROOT/'.github/workflows/remotion-golden-s16.yml'

def test_s16_source_timebase_and_scene_boundary_are_exact():
 d=json.loads(CONTRACT.read_text());s=d['source'];assert s['start_frame']==727;assert s['end_frame_exclusive']==819;assert s['frame_count']==92;assert s['fps']==30;assert (s['width'],s['height'])==(512,1108)

def test_s16_foreground_payoff_actions_are_source_bound():
 d=json.loads(CONTRACT.read_text());a={x['id']:x for x in d['actions']};assert a['S16-PHY-002']['local']==[2,5,23];assert a['S16-PHY-003']['local']==[9,10,25];assert a['S16-PHY-004']['local']==[19,23,54];assert a['S16-PHY-005']['local']==[54,54,87]

def test_s16_depth_is_partial_order_not_hallucinated_total_order():
 d=json.loads(CONTRACT.read_text());edges={(x['front'],x['behind']) for x in d['depth_partial_order']};assert ('COLUMN','SUBJECT_PLATE') in edges;assert ('QUESTION_MARK','SUBJECT_PLATE') in edges;assert ('FACTOR_X','COLUMN') in edges;assert ('FACTOR_X','QUESTION_MARK') in edges;assert d['unresolved_depth_relation']['authority']=='UNKNOWN';assert set(d['unresolved_depth_relation']['pair'])=={'COLUMN','QUESTION_MARK'}

def test_s16_camera_authority_is_phase_scoped():
 d=json.loads(CONTRACT.read_text());ph=d['camera_phases'];assert ph[0]['local']==[0,87];assert ph[0]['class']=='STATIC_SOURCE_FRAMING_WITH_NATIVE_SUBJECT_MOTION';assert ph[1]['local']==[87,92];assert ph[1]['class']=='GLOBAL_UPWARD_REFLOW_OR_VIEWPORT_SHIFT';assert ph[1]['template_policy']=='SOURCE_LOCK_UNLESS_INDEPENDENTLY_PROVEN_EDITORIAL';assert ph[1]['cause'].startswith('UNKNOWN')

def test_calm_hold_is_an_invariant_not_a_missing_animation_bug():
 d=json.loads(CONTRACT.read_text());r=d['retention_grammar'];assert r['payoff_hold_local']==[54,87];assert r['payoff_hold_frames']==33;assert 'extra editorial motion would reduce fidelity' in r['principle'];source=COMP.read_text();assert 'infinite' not in source.lower();assert 'repeat' not in source.lower()

def test_renderer_uses_measured_tracks_and_semantic_registration():
 root=ROOT_TSX.read_text();spec=SPEC.read_text();track=TRACK.read_text();comp=COMP.read_text();assert "from './golden_s16'" in root;assert 'id={S16_SPEC.compositionId}' in root;assert 'id={S16_SPEC.overlayCompositionId}' in root;assert "sceneId:'S16_FACTOR_X'" in spec;assert 'measuredS16(frame)' in comp;assert 'MEASURED_SOURCE_BOUND_PROJECTION_V1' in track

def test_source_ui_reveal_is_source_lock_not_editing_dna():
 d=json.loads(CONTRACT.read_text());a={x['id']:x for x in d['actions']};assert a['S16-PHY-006']['domain']=='source_lock';assert a['S16-PHY-006']['template_policy']=='EXCLUDE_FROM_STRUCTURAL_EDITING_DNA';assert 'screen-recording/Reels UI' in d['source_locks']

def test_factor_font_and_foreground_assets_remain_unknown_source_identity():
 d=json.loads(CONTRACT.read_text());spec=SPEC.read_text();assert "factorFont:'FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN'" in spec;assert 'exact Factor X font/source text metrics' in d['unknowns'];assert 'exact original column 3D/raster asset' in d['unknowns'];assert 'exact question-mark 3D/raster asset' in d['unknowns']

def test_audio_source_events_remain_distinct_from_renderer_calibration():
 spec=SPEC.read_text();assert 'sourceTransientProxyFrames:[0.37,4.64,9.73,14.44,20.95,23.20,36.37]' in spec;assert 'structuralHitFrames:[0,5,10,14,21,23,36]' in spec;assert 'syntheticHitLeadFrames:1' in spec;assert 'MUST_BE_PHYSICALLY_QUALIFIED_IN_S16' in spec

def test_column_opacity_calibration_has_monotonic_runtime_domain_and_preserves_mapping():
 spec=SPEC.read_text();comp=COMP.read_text()
 match=re.search(r"columnOpacityByY:\{\s*input:\[([^\]]+)\],\s*output:\[([^\]]+)\]",spec,re.S)
 assert match, 'column opacity calibration must be explicit in S16_SPEC'
 inputs=[float(x.strip()) for x in match.group(1).split(',')]
 outputs=[float(x.strip()) for x in match.group(2).split(',')]
 assert len(inputs)==len(outputs)>=2
 assert all(b>a for a,b in zip(inputs,inputs[1:])),inputs
 assert dict(zip(inputs,outputs))=={792.0:1.0,807.0:.86,828.0:.52,858.0:.20}
 assert 'columnOpacityFromY(box.y)' in comp
 assert '[858,828,807,792]' not in comp

def test_workflow_action_pins_are_full_shas():
 if not WORKFLOW.exists():return
 text=WORKFLOW.read_text();uses=[line.split('uses:',1)[1].strip().split()[0] for line in text.splitlines() if 'uses:' in line]
 for value in uses:
  assert re.fullmatch(r'.+@[0-9a-f]{40}',value),value
