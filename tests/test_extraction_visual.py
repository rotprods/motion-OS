from src.extraction.visual import dominant_palette, contrast_ratio, gradient_candidate, infer_layout


def test_palette_and_gradient_are_deterministic():
    p = dominant_palette([(250,250,250)] * 8 + [(15,15,15)] * 2, max_colors=2, quant_step=16)
    assert len(p) == 2
    assert p[0]["ratio"] == 0.8
    g = gradient_candidate((0,0,0), (255,255,255))
    assert g["detected"] is True and g["confidence"] == 1.0


def test_contrast_and_layout():
    assert contrast_ratio((0,0,0),(255,255,255)) > 20
    layout = infer_layout([(0.3,0.2,0.7,0.4),(0.35,0.5,0.65,0.7)])
    assert layout["pattern"] == "centered_hero"
    assert layout["safe_margin_pct"] >= 20
