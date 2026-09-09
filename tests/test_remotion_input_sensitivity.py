from copy import deepcopy

import pytest

from scripts.verify_remotion_input_sensitivity import compare_frame_bytes, mutate_typography_spec


def _spec():
    return {
        "project": {"fps": 30, "width": 640, "height": 360, "duration_frames": 60},
        "scenes": [
            {
                "id": "scene:test",
                "from": 0,
                "durationInFrames": 30,
                "transition": {"type": "cut"},
                "camera": {"motion": "static"},
                "events": [],
                "layers": [
                    {
                        "id": "layer:test:typography",
                        "layerClass": "TYPOGRAPHY",
                        "z": 6,
                        "semanticRole": "typography",
                        "attentionRole": "secondary",
                        "data": {"text": "ORIGINAL STUDIO TEXT"},
                    }
                ],
            }
        ],
    }


def test_typography_mutation_changes_only_copied_spec_and_returns_target_frame():
    original = _spec()
    before = deepcopy(original)
    mutated, metadata = mutate_typography_spec(original)
    assert original == before
    assert mutated != original
    assert mutated["scenes"][0]["layers"][0]["data"]["text"].startswith("ORIGINAL STUDIO TEXT")
    assert metadata["scene_id"] == "scene:test"
    assert metadata["layer_id"] == "layer:test:typography"
    assert 0 <= metadata["frame_index"] < 30
    assert metadata["original_text_sha256"] != metadata["mutated_text_sha256"]


def test_missing_typography_text_fails_closed():
    spec = _spec()
    spec["scenes"][0]["layers"][0]["data"]["text"] = ""
    with pytest.raises(ValueError, match="no non-empty TYPOGRAPHY"):
        mutate_typography_spec(spec)


def test_invalid_scene_frame_contract_fails_closed():
    spec = _spec()
    spec["scenes"][0]["durationInFrames"] = 0
    with pytest.raises(ValueError, match="durationInFrames"):
        mutate_typography_spec(spec)


def test_frame_comparison_reports_exact_rgb_difference():
    report = compare_frame_bytes(b"abcdef", b"abcxef")
    assert report["raw_frame_bytes"] == 6
    assert report["changed_rgb_bytes"] == 1
    assert report["changed_ratio"] == pytest.approx(1 / 6)
    assert report["baseline_frame_sha256"] != report["variant_frame_sha256"]


def test_identical_raw_frames_report_zero_difference():
    report = compare_frame_bytes(b"abcdef", b"abcdef")
    assert report["changed_rgb_bytes"] == 0
    assert report["changed_ratio"] == 0
    assert report["baseline_frame_sha256"] == report["variant_frame_sha256"]


@pytest.mark.parametrize("baseline,variant", [(b"", b"x"), (b"x", b""), (b"x", b"xx")])
def test_invalid_raw_frame_comparisons_fail_closed(baseline, variant):
    with pytest.raises(ValueError):
        compare_frame_bytes(baseline, variant)
