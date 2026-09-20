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

def test_card_oracle_is_target_isolated_from_adjacent_geometry():
    im=Image.new('RGBA',(220,220),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rounded_rectangle((50,60,150,180),radius=16,fill=(*mod.MEASUREMENT_COLORS['card_audio'],255))
    d.rectangle((151,100,190,135),fill=(120,120,120,255))
    expected=mod.Box(50,60,101,121)
    observed=mod.observe_named(im,expected,'card_audio')
    assert observed is not None
    assert mod.iou(expected,observed)>0.99
    assert mod.centroid(expected,observed)<1

def test_annotation_identity_remains_separate_from_card_identity():
    im=Image.new('RGBA',(220,220),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rectangle((40,40,180,190),fill=(*mod.MEASUREMENT_COLORS['card_visual'],255))
    d.ellipse((55,70,170,150),outline=(*mod.MEASUREMENT_COLORS['annotation_visual'],255),width=6)
    card=mod.observe_named(im,mod.Box(40,40,141,151),'card_visual')
    annotation=mod.observe_named(im,mod.Box(55,70,116,81),'annotation_visual')
    assert card is not None and annotation is not None
    assert mod.iou(mod.Box(40,40,141,151),card)>0.99
    assert mod.iou(mod.Box(55,70,116,81),annotation)>0.90

def test_measurement_palette_is_unique_across_cards_headings_annotations():
    colors=list(mod.MEASUREMENT_COLORS.values())
    assert len(colors)==9
    assert len(set(colors))==9

def test_measured_track_v2_and_annotation_track_are_supported_but_required_for_visible_promotion():
    source=SCRIPT.read_text()
    assert 'motion-os.s14-measured-track/v2' in source
    assert '--annotations' in source
    assert "gates['annotation_geometry']='NOT_RUN'" in source
    assert 'visible_pass=False' in source

def test_full_9d_authority_is_impossible_from_visible_state_qualifier_alone():
    source=SCRIPT.read_text()
    assert "'full_9d_fidelity_validated':False" in source
    assert 'exact annotation vector-path topology/stroke pre-compression' in source
    assert 'isolated original SFX stems' in source
