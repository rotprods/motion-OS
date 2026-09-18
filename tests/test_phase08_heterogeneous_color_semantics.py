import pytest

from src.renderers.color_policy import (
    ArtifactColorBinding,
    BT709_SDR_LIMITED,
    SRGB_FULL,
    color_profile_from_probe,
    ffmpeg_color_filter,
    pixel_family_from_probe,
)


def test_browser_origin_yuv_media_is_not_treated_as_gbr():
    probe = {
        "pix_fmt": "yuv420p",
        "color_primaries": "bt709",
        "color_transfer": "bt709",
        "color_space": "bt709",
        "color_range": "tv",
    }
    assert pixel_family_from_probe("hyperframes", probe) == "yuv"
    profile = color_profile_from_probe("hyperframes", probe, evidence_ref="ffprobe:fixture")
    assert profile.matrix == "bt709"
    assert profile.range == "limited"
    graph = ffmpeg_color_filter(
        ArtifactColorBinding("hyperframes", profile),
        BT709_SDR_LIMITED,
        input_label="0:v",
        output_label="norm",
    )
    assert "matrixin=bt709" in graph
    assert "matrixin=gbr" not in graph


def test_argb_browser_screenshot_media_remains_rgb_family():
    probe = {"pix_fmt": "argb"}
    assert pixel_family_from_probe("lottie", probe) == "rgb"
    graph = ffmpeg_color_filter(
        ArtifactColorBinding("lottie", SRGB_FULL, preserve_alpha=True),
        BT709_SDR_LIMITED,
        input_label="0:v",
        output_label="norm",
    )
    assert "matrixin=gbr" in graph
    assert "format=yuva444p10le" in graph


def test_gbr_planar_formats_are_rgb_family():
    assert pixel_family_from_probe("rgb", {"pix_fmt": "gbrp10le"}) == "rgb"
    assert pixel_family_from_probe("rgba", {"pix_fmt": "gbrap16le"}) == "rgb"


def test_unknown_or_missing_pixel_family_fails_closed():
    with pytest.raises(ValueError, match="unqualified_pixel_format:x:missing"):
        pixel_family_from_probe("x", {})
    with pytest.raises(ValueError, match="unqualified_pixel_format:x:gray"):
        pixel_family_from_probe("x", {"pix_fmt": "gray"})


def test_yuv_without_colorimetry_cannot_be_silently_qualified():
    probe = {"pix_fmt": "yuv420p"}
    assert pixel_family_from_probe("x", probe) == "yuv"
    with pytest.raises(ValueError, match="unqualified_probe_primaries:x:missing"):
        color_profile_from_probe("x", probe, evidence_ref="ffprobe:x")
