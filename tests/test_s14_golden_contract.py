from __future__ import annotations
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'forensics/references/screenrecording_20260826/golden/s14/s14_contract.json'
ROOT_TSX=ROOT/'runtime/remotion/src/Root.tsx'
SPEC=ROOT/'runtime/remotion/src/golden_s14/s14Spec.ts'
TRACK=ROOT/'runtime/remotion/src/golden_s14/sourceMeasuredTrack.ts'
COMP=ROOT/'runtime/remotion/src/golden_s14/S14AudioVisualTexto.tsx'
WORKFLOW=ROOT/'.github/workflows/remotion-golden-s14.yml'

def test_s14_source_timebase_is_exact():
 d=json.loads(CONTRACT.read_text());s=d['source'];assert s['start_frame']==561;assert s['end_frame_exclusive']==655;assert s['frame_count']==94;assert s['fps']==30;assert (s['width'],s['height'])==(512,1108)

def test_s14_physical_refinement_preserves_historical_parent_actions():
 d=json.loads(CONTRACT.read_text());a={x['id']:x for x in d['refined_actions']};assert a['S14-PHY-001']['refines']=='A076';assert (a['S14-PHY-001']['start_frame'],a['S14-PHY-001']['impact_frame'],a['S14-PHY-001']['settle_frame'])==(572,578,581);assert a['S14-PHY-002']['refines']=='A078';assert (a['S14-PHY-002']['start_frame'],a['S14-PHY-002']['impact_frame'],a['S14-PHY-002']['settle_frame'])==(608,615,621)

def test_state_heading_card_and_annotation_are_one_contract():
 d=json.loads(CONTRACT.read_text());rule=d['state_machine']['rule'];assert 'heading identity' in rule and 'selected media card' in rule and 'annotation identity' in rule

def test_renderer_consumes_measured_track_v2_and_registers_semantically():
 root=ROOT_TSX.read_text();spec=SPEC.read_text();track=TRACK.read_text();comp=COMP.read_text();assert "from './golden_s14'" in root;assert 'id={S14_SPEC.compositionId}' in root;assert 'id={S14_SPEC.overlayCompositionId}' in root;assert "sceneId:'S14_AUDIO_VISUAL_TEXTO'" in spec;assert 'MEASURED_VISIBLE_KEYFRAME_PROJECTION_V2' in track;assert 'fullTrackV2DriveId' in track;assert 'measuredS14(frame)' in comp

def test_heading_identity_swap_is_versioned_not_silently_rewritten():
 d=json.loads(CONTRACT.read_text());assert d['schema_version']=='motion-os.golden-s14-contract/v2';h=d['measurement_history'];assert len(h)>=1;corr=next(x for x in h if x['id']=='S14-MEAS-CORR-001');assert corr['defect_family']=='TRACK_IDENTITY_SWAP_DURING_CROSSING';assert corr['frames']==[52,53,54,55,56];assert corr['preserves_v1'] is True;assert d['drive_evidence']['full_measured_track_v1'];assert d['drive_evidence']['full_measured_track_v2']

def test_fallback_heading_calibration_never_claims_exact_font_identity():
 comp=COMP.read_text();spec=SPEC.read_text();assert 'headingVisibleBoundsCalibration' in comp;assert 'does not identify the unknown original font' in comp;assert 'Arial Black,Arial,sans-serif' in comp;assert "headingFont:'FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN'" in spec

def test_audio_timing_is_present_but_timbre_authority_is_not_inflated():
 spec=SPEC.read_text();comp=COMP.read_text();assert 'transientLocalFrames:[10,14,17,46,50,56,63]' in spec;assert "sfxIdentity:'UNKNOWN_FROM_MIXED_MASTER'" in spec;assert 'makeS14Hit' in comp

def test_nested_media_is_source_lock_not_template_truth():
 d=json.loads(CONTRACT.read_text());a={x['id']:x for x in d['refined_actions']};assert a['S14-PHY-004']['authority']=='SOURCE_LOCK';assert 'NESTED_MEDIA_SLOT'==a['S14-PHY-004']['target']

def test_workflow_action_revisions_are_full_git_shas():
 text=WORKFLOW.read_text();uses=[line.split('uses:',1)[1].strip().split()[0] for line in text.splitlines() if 'uses:' in line];assert uses
 for value in uses:
  assert '@' in value
  revision=value.rsplit('@',1)[1]
  assert re.fullmatch(r'[0-9a-f]{40}',revision), f'action pin must be a full 40-char SHA: {value}'
