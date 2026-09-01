from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/qualify_s14_fidelity.py'
spec=importlib.util.spec_from_file_location('s14q',SCRIPT);assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

def test_dynamic_qualifier_module_is_registered_for_dataclass_resolution():
    assert sys.modules['s14q'] is mod
    assert mod.Box.__module__=='s14q'

def test_card_oracle_does_not_absorb_adjacent_same_alpha_geometry():
    im=Image.new('RGBA',(220,220),(0,0,0,0));d=ImageDraw.Draw(im)
    # canonical target
    d.rounded_rectangle((50,60,150,180),radius=16,fill=(120,120,120,255))
    # adjacent element in the padded neighborhood: must not become target authority
    d.rectangle((151,100,190,135),fill=(120,120,120,255))
    expected=mod.Box(50,60,101,121)
    observed=mod.observe_card(im,expected)
    assert observed is not None
    assert mod.iou(expected,observed)>0.97
    assert mod.centroid(expected,observed)<2

def test_full_9d_authority_is_impossible_from_visible_state_qualifier_alone():
    # The contract intentionally has a separate hard-coded false authority bit;
    # visible geometry is never sufficient to self-promote to full 9D.
    source=SCRIPT.read_text()
    assert "'full_9d_fidelity_validated':False" in source
    assert 'annotation vector-path fidelity' in source
    assert 'isolated original SFX stems' in source
