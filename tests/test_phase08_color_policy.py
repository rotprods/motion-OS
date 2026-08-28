from dataclasses import replace

import pytest

from src.renderers.color_policy import (
    BT709_SDR_LIMITED,
    DISPLAY_P3_SRGB_FULL,
    SRGB_FULL,
    ArtifactColorBinding,
    ColorProfile,
    build_color_normalization_plan,
    ffmpeg_color_filter,
    ffmpeg_output_color_args,
    validate_color_plan,
)


def test_plan_binds_every_artifact_and_is_deterministic():
    profiles = {
        "base": BT709_SDR_LIMITED,
        "ui": SRGB_FULL,
        "p3": DISPLAY_P3_SRGB_FULL,
    }
    a = build_color_normalization_plan(["base", "ui", "p3"], profiles, alpha_artifacts={"ui"})
    b = build_color_normalization_plan(["p3", "base", "ui"], profiles, alpha_artifacts={"ui"})
    assert a.plan_hash == b.plan_hash
    assert [binding.artifact_id for binding in a.bindings] == ["base", "p3", "ui"]
    assert validate_color_plan(a, ["base", "ui", "p3"]) == []


def test_missing_profile_fails_closed():
    with pytest.raises(ValueError, match="missing_color_profile:overlay"):
        build_color_normalization_plan(["base", "overlay"], {"base": BT709_SDR_LIMITED})


def test_extra_profile_fails_closed_instead_of_silent_ignore():
    with pytest.raises(ValueError, match="unbound_color_profiles:ghost"):
        build_color_normalization_plan(
            ["base"],
            {"base": BT709_SDR_LIMITED, "ghost": SRGB_FULL},
        )


def test_hdr_input_requires_explicit_qualified_tone_map():
    hdr = ColorProfile(
        profile_id="hdr-fixture",
        primaries="bt709",
        transfer="bt709",
        matrix="bt709",
        range="limited",
        hdr=True,
        evidence=("fixture",),
    )
    with pytest.raises(ValueError, match="hdr_requires_explicit_tone_map:hdr"):
        build_color_normalization_plan(["hdr"], {"hdr": hdr})


def test_unknown_colorimetry_is_not_guessed():
    unknown = ColorProfile(
        profile_id="unknown",
        primaries="unknown",
        transfer="bt709",
        matrix="bt709",
        range="limited",
        evidence=("ffprobe:unknown",),
    )
    with pytest.raises(ValueError, match="unsupported_primaries:unknown"):
        build_color_normalization_plan(["x"], {"x": unknown})


def test_missing_color_evidence_fails_closed():
    guessed = replace(SRGB_FULL, profile_id="guessed", evidence=())
    with pytest.raises(ValueError, match="missing_color_evidence:guessed"):
        build_color_normalization_plan(["ui"], {"ui": guessed})


def test_ffmpeg_filter_converts_browser_ui_to_bt709_and_preserves_alpha():
    binding = ArtifactColorBinding("ui", SRGB_FULL, preserve_alpha=True)
    result = ffmpeg_color_filter(binding, BT709_SDR_LIMITED, input_label="1:v", output_label="norm1")
    assert result.startswith("[1:v]zscale=")
    assert "primariesin=bt709" in result
    assert "transferin=iec61966-2-1" in result
    assert "matrixin=rgb" in result
    assert "rangein=full" in result
    assert "transfer=bt709" in result
    assert "matrix=bt709" in result
    assert "range=limited" in result
    assert "format=yuva444p10le" in result
    assert result.endswith("[norm1]")


def test_opaque_filter_uses_non_alpha_working_format():
    binding = ArtifactColorBinding("base", BT709_SDR_LIMITED, preserve_alpha=False)
    result = ffmpeg_color_filter(binding, BT709_SDR_LIMITED, input_label="0:v", output_label="norm0")
    assert "format=yuv444p10le" in result
    assert "yuva444p10le" not in result


def test_output_metadata_is_explicit_and_tokenized():
    args = ffmpeg_output_color_args(BT709_SDR_LIMITED)
    assert args == [
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-colorspace", "bt709",
        "-color_range", "tv",
    ]


def test_tampered_plan_hash_is_detected():
    plan = build_color_normalization_plan(["base"], {"base": BT709_SDR_LIMITED})
    tampered = replace(plan, plan_hash="0" * 64)
    assert "plan_hash_mismatch" in validate_color_plan(tampered, ["base"])


def test_unqualified_backend_and_tonemap_are_rejected():
    with pytest.raises(ValueError, match="unsupported_color_backend"):
        build_color_normalization_plan(["base"], {"base": BT709_SDR_LIMITED}, backend="colorspace")
    with pytest.raises(ValueError, match="unsupported_tone_map_policy"):
        build_color_normalization_plan(["base"], {"base": BT709_SDR_LIMITED}, tone_map_policy="guess")
