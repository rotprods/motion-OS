from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/qualify_s11_fidelity.py'


def _load_module():
    spec = importlib.util.spec_from_file_location('qualify_s11_fidelity', SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dark_pill_oracle_does_not_absorb_adjacent_arrow_component():
    q = _load_module()
    expected = (20.0, 20.0, 80.0, 30.0)
    image = Image.new('RGBA', (140, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    # Target pill fills its expected screen-space box.
    draw.rounded_rectangle((20, 20, 99, 49), radius=14, fill=(37, 37, 37, 255))
    # Adjacent dark/grey arrow touches the pill boundary from below. A padded
    # connected-component crop would incorrectly enlarge the pill bbox.
    draw.line((60, 49, 60, 75), fill=(45, 45, 45, 255), width=5)
    draw.line((60, 75, 73, 68), fill=(45, 45, 45, 255), width=5)

    observed = q.observe(image, expected, 'dark', wide=True)
    assert observed is not None
    assert observed[0] >= 20
    assert observed[1] >= 20
    assert observed[0] + observed[2] <= 101
    assert observed[1] + observed[3] <= 51
    assert q.iou(expected, observed) >= 0.93


def test_partial_visible_output_qualification_can_never_claim_full_9d():
    source = SCRIPT.read_text(encoding='utf-8')
    assert "'full_9d_fidelity_validated':False" in source
    assert 'exact fonts' in source
    assert 'original AE graph' in source
    assert 'original isolated SFX stems' in source


def test_dark_oracle_uses_zero_padding_but_white_can_remain_bounded():
    source = SCRIPT.read_text(encoding='utf-8')
    assert "pad=0 if kind=='dark' else 18" in source
