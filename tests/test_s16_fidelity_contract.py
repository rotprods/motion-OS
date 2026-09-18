from __future__ import annotations
import importlib.util,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SCRIPT=ROOT/'scripts/qualify_s16_fidelity.py'
spec=importlib.util.spec_from_file_location('s16q',SCRIPT);assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)

def test_measurement_colors_are_unique():
 assert len(mod.COLORS)==3;assert len(set(mod.COLORS.values()))==3

def test_target_color_oracle_ignores_adjacent_entity():
 im=Image.new('RGBA',(220,220),(0,0,0,0));d=ImageDraw.Draw(im);d.rectangle((30,40,130,180),fill=(*mod.COLORS['column'],255));d.rectangle((131,70,190,160),fill=(*mod.COLORS['question_mark'],255));b=mod.bbox_from_color(im,mod.COLORS['column']);assert b==(30,40,101,141)

def test_visible_geometry_qualifier_cannot_promote_full_9d():
 src=SCRIPT.read_text();assert "'full_9d_fidelity_validated':False" in src;assert 'exact Factor X font/source glyph outline' in src;assert 'original AE graph/Graph Editor curves' in src
