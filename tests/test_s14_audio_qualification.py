from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/qualify_s14_audio.py'
CONTRACT=ROOT/'forensics/references/screenrecording_20260826/golden/s14/s14_contract.json'
spec=importlib.util.spec_from_file_location('s14audioq',SCRIPT);assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)

def test_s14_audio_qualifier_uses_source_contract_events():
 d=json.loads(CONTRACT.read_text());events=mod._source_events(d)
 assert events==[10.05,14.40,16.80,45.75,50.25,56.25,62.85]

def test_peak_selection_is_local_and_does_not_jump_to_adjacent_event():
 scores=[(10/30,.2),(10.8/30,.9),(12/30,2.0)]
 peak=mod._peak_near(scores,10.05,radius_frames=1.2)
 assert peak is not None
 assert abs(peak[0]*30-10.8)<1e-6

def test_audio_qualification_cannot_self_promote_full_fidelity():
 source=SCRIPT.read_text()
 assert "'full_audio_fidelity_validated': False" in source
 assert 'isolated source SFX stems' in source
 assert 'source SFX identity/timbre' in source
