from __future__ import annotations
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SCRIPT=ROOT/'scripts/qualify_s16_audio.py';CONTRACT=ROOT/'forensics/references/screenrecording_20260826/golden/s16/s16_contract.json'
spec=importlib.util.spec_from_file_location('s16audioq',SCRIPT);assert spec and spec.loader;mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)

def test_s16_audio_proxy_frames_are_contract_authority():
 d=json.loads(CONTRACT.read_text());events=[float(x['local_frame']) for x in d['audio_transient_proxies']];assert events==mod.REQUIRED

def test_peak_search_is_local():
 sc=[(9.9/30,.4),(10.4/30,.9),(13/30,3.0)];p=mod.peak_near(sc,10.0,1.4);assert p is not None;assert abs(p[0]*30-10.4)<1e-9

def test_audio_proxy_never_self_promotes_stem_or_timbre_fidelity():
 s=SCRIPT.read_text();assert "'full_audio_fidelity_validated':False" in s;assert 'isolated source SFX stems' in s;assert 'source SFX identity/timbre' in s
