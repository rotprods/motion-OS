from src.knowledge.style_signature import canonical_style_family, evidence_coverage, feature_pack_style_vector


def _pack():
    return {
        "video_meta":{"duration_ms":3000},
        "shots":[{"id":"S01"},{"id":"S02"},{"id":"S03"}],
        "keyframes":[{"id":"K1"}],
        "ocr":[],
        "color_stats":{"palette":[{"hex":"#101010","ratio":.6},{"hex":"#F0F0F0","ratio":.3},{"hex":"#1ED760","ratio":.1}]},
        "layout_stats":{"anchors_x":[.1,.5,.9],"anchors_y":[.2,.8],"safe_margin_pct":8},
        "motion_stats":{"tracks":[{"motion_median":2,"camera_likelihood":.2,"global_magnitude":.4,"local_residual_median":1.3}]},
        "fx_stats":{"measurements":[{"contrast":48,"blur_proxy":.25,"highlight_ratio":.05}]},
        "audio_stats":{"authority":"measured","onsets_ms":[100,500,900]},
        "warnings":["provider_unavailable:ocr:tesseract binary missing"],
    }


def test_style_vector_is_deterministic_and_measured():
    a=feature_pack_style_vector(_pack())
    b=feature_pack_style_vector(_pack())
    assert a == b
    assert len(a) == 24
    assert all(isinstance(x,float) for x in a)


def test_evidence_coverage_accepts_explicit_unavailable_ocr():
    assert evidence_coverage(_pack()) == 1.0


def test_canonical_family_prefers_confidence():
    doc={"style_system":{"style_family":[{"id":"a","confidence":.3},{"id":"b","confidence":.9}]}}
    assert canonical_style_family(doc) == "b"
