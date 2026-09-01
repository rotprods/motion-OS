from __future__ import annotations
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'forensics/references/screenrecording_20260826/golden/s14/s14_contract.json'
ROOT_TSX=ROOT/'runtime/remotion/src/Root.tsx'
SPEC=ROOT/'runtime/remotion/src/golden_s14/s14Spec.ts'
TRACK=ROOT/'runtime/remotion/src/golden_s14/sourceMeasuredTrack.ts'
ANNOTATION_TRACK=ROOT/'runtime/remotion/src/golden_s14/annotationMeasuredTrack.ts'
COMP=ROOT/'runtime/remotion/src/golden_s14/S14AudioVisualTexto.tsx'
WORKFLOW=ROOT/'.github/workflows/remotion-golden-s14.yml'

def test_s14_source_timebase_is_exact():
 d=json.loads(CONTRACT.read_text());s=d['source'];assert s['start_frame']==561;assert s['end_frame_exclusive']==655;assert s['frame_count']==94;assert s['fps']==30;assert (s['width'],s['height'])==(512,1108)

def test_s14_physical_refinement_preserves_historical_parent_actions():
 d=json.loads(CONTRACT.read_text());a={x['id']:x for x in d['refined_actions']};assert a['S14-PHY-001']['refines']=='A076';assert (a['S14-PHY-001']['start_frame'],a['S14-PHY-001']['impact_frame'],a['S14-PHY-001']['settle_frame'])==(572,578,581);assert a['S14-PHY-002']['refines']=='A078';assert (a['S14-PHY-002']['start_frame'],a['S14-PHY-002']['impact_frame'],a['S14-PHY-002']['settle_frame'])==(608,615,621)

def test_state_heading_card_and_annotation_are_one_contract():
 d=json.loads(CONTRACT.read_text());rule=d['state_machine']['rule'];assert 'heading identity' in rule and 'selected media card' in rule and 'annotation identity' in rule

def test_renderer_consumes_measured_track_v2_and_annotation_track():
 root=ROOT_TSX.read_text();spec=SPEC.read_text();track=TRACK.read_text();annotation=ANNOTATION_TRACK.read_text();comp=COMP.read_text();assert "from './golden_s14'" in root;assert 'id={S14_SPEC.compositionId}' in root;assert 'id={S14_SPEC.overlayCompositionId}' in root;assert "sceneId:'S14_AUDIO_VISUAL_TEXTO'" in spec;assert 'MEASURED_VISIBLE_KEYFRAME_PROJECTION_V2' in track;assert 'fullTrackV2DriveId' in track;assert 'measuredS14(frame)' in comp;assert 'MEASURED_VISIBLE_BBOX_PROXY_NOT_EXACT_VECTOR_PATH' in annotation;assert 'measuredS14Annotation(frame)' in comp

def test_measurement_corrections_are_versioned_not_silently_rewritten():
 d=json.loads(CONTRACT.read_text());assert d['schema_version']=='motion-os.golden-s14-contract/v3';h=d['measurement_history'];assert len(h)>=2
 corr=next(x for x in h if x['id']=='S14-MEAS-CORR-001');assert corr['defect_family']=='TRACK_IDENTITY_SWAP_DURING_CROSSING';assert corr['frames']==[52,53,54,55,56];assert corr['preserves_v1'] is True
 annotation=next(x for x in h if x['id']=='S14-MEAS-CORR-002');assert annotation['defect_family']=='STATIC_SUMMARY_COLLAPSED_ANNOTATION_TRAJECTORY';assert annotation['exact_vector_path_authority']=='UNKNOWN'
 assert d['drive_evidence']['full_measured_track_v1'];assert d['drive_evidence']['full_measured_track_v2'];assert d['drive_evidence']['annotation_track_v1']

def test_fallback_heading_calibration_preserves_unknown_font_authority():
 comp=COMP.read_text();spec=SPEC.read_text();contract=json.loads(CONTRACT.read_text())
 assert 'headingVisibleBoundsCalibration' in comp
 assert 'Arial Black,Arial,sans-serif' in comp
 assert "headingFont:'FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN'" in spec
 assert 'exact heading font' in contract['unknowns']

def test_audio_timing_is_source_truth_plus_renderer_calibration():
 spec=SPEC.read_text();comp=COMP.read_text();contract=json.loads(CONTRACT.read_text())
 assert 'sourceTransientProxyFrames:[10.05,14.40,16.80,45.75,50.25,56.25,62.85]' in spec
 assert 'transientLocalFrames:[10,14,17,46,50,56,63]' in spec
 assert 'syntheticHitLeadFrames:1' in spec
 assert 'S14_SPEC.rendererCalibration.syntheticHitLeadFrames' in comp
 assert "sfxIdentity:'UNKNOWN_FROM_MIXED_MASTER'" in spec
 cal=next(x for x in contract['renderer_calibrations'] if x['id']=='S14-RENDER-CAL-001');assert cal['synthetic_hit_lead_frames']==1;assert cal['must_be_physically_reverified'] is True

def test_nested_media_is_source_lock_not_template_truth():
 d=json.loads(CONTRACT.read_text());a={x['id']:x for x in d['refined_actions']};assert a['S14-PHY-004']['authority']=='SOURCE_LOCK';assert 'NESTED_MEDIA_SLOT'==a['S14-PHY-004']['target']

def test_workflow_action_revisions_are_full_git_shas():
 text=WORKFLOW.read_text();uses=[line.split('uses:',1)[1].strip().split()[0] for line in text.splitlines() if 'uses:' in line];assert uses
 for value in uses:
  assert '@' in value
  revision=value.rsplit('@',1)[1]
  assert re.fullmatch(r'[0-9a-f]{40}',revision), f'action pin must be a full 40-char SHA: {value}'
