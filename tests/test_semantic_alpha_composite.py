import pytest

from scripts.verify_semantic_alpha_composite import classify_semantic_pixels


def test_semantic_alpha_accepts_preserved_transparent_and_applied_opaque_regions():
    verdict = classify_semantic_pixels((0, 0, 255), (255, 0, 0))
    assert verdict["ok"] is True
    assert verdict["errors"] == []


def test_semantic_alpha_rejects_when_transparent_region_overwrites_base():
    verdict = classify_semantic_pixels((255, 0, 0), (255, 0, 0))
    assert verdict["ok"] is False
    assert "transparent_region_did_not_preserve_base" in verdict["errors"]


def test_semantic_alpha_rejects_when_opaque_region_does_not_apply_overlay():
    verdict = classify_semantic_pixels((0, 0, 255), (0, 0, 255))
    assert verdict["ok"] is False
    assert "opaque_region_did_not_apply_overlay" in verdict["errors"]


def test_semantic_alpha_tolerance_is_bounded_and_explicit():
    assert classify_semantic_pixels((5, 2, 250), (250, 4, 2), tolerance=6)["ok"] is True
    assert classify_semantic_pixels((13, 0, 255), (255, 0, 0), tolerance=12)["ok"] is False
    with pytest.raises(ValueError, match="non-negative"):
        classify_semantic_pixels((0, 0, 255), (255, 0, 0), tolerance=-1)
