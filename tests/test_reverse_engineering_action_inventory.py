from __future__ import annotations

import pytest

from src.reverse_engineering.action_inventory import (
    ActionInventoryError,
    actions_covering_frame,
    adjudicate_peak,
    detect_local_peaks,
    gauntlet_coverage_from_frame_metrics,
    validate_action_inventory,
)


def inventory():
    mapping = {"after_effects":"ae", "remotion":"remotion", "hyperframes":"gsap"}
    return {
        "schema_version":"1.0.0",
        "video_id":"fixture",
        "source_sha256":"a"*64,
        "fps":30,
        "scenes":[
            {"scene_id":"S1","start_frame":0,"end_frame":5,"role":"hook","description":"a"},
            {"scene_id":"S2","start_frame":5,"end_frame":10,"role":"resolve","description":"b"},
        ],
        "actions":[
            {"action_id":"A1","scene_id":"S1","start_frame":0,"impact_frame":2,"end_frame":4,"start_ms":0,"end_ms":133,"domain":"transition","verb":"mask_reveal","target":"x","function":"hook","parameters":{},"audio_link":None,"z_role":"BACKGROUND","temporal_mode":"discrete","motion_origin":"editorial","authority":"evidence_bound_inference","confidence":0.8,"evidence_refs":["frame:0-4"],"renderer_mapping":mapping},
            {"action_id":"A2","scene_id":"S2","start_frame":5,"impact_frame":7,"end_frame":9,"start_ms":167,"end_ms":300,"domain":"caption","verb":"scale_punch","target":"y","function":"payoff","parameters":{},"audio_link":None,"z_role":"CAPTIONS","temporal_mode":"discrete","motion_origin":"editorial","authority":"evidence_bound_inference","confidence":0.9,"evidence_refs":["frame:5-9"],"renderer_mapping":mapping},
        ],
    }


def metrics(values):
    return {"frames":[{"frame": frame, "mad": value, "flow_p90": value} for frame, value in enumerate(values)]}


def test_inventory_validates_and_frame_lookup():
    value = inventory()
    validate_action_inventory(value)
    assert actions_covering_frame(value, 2) == ("A1",)
    assert actions_covering_frame(value, 7) == ("A2",)


def test_action_outside_scene_fails_closed():
    value = inventory()
    value["actions"][0]["end_frame"] = 6
    with pytest.raises(Exception):
        validate_action_inventory(value)


def test_missing_renderer_mapping_fails_closed():
    value = inventory()
    del value["actions"][0]["renderer_mapping"]["hyperframes"]
    with pytest.raises(Exception):
        validate_action_inventory(value)


def test_staggered_action_requires_explicit_subevents():
    value = inventory()
    value["actions"][1]["temporal_mode"] = "staggered"
    with pytest.raises(ActionInventoryError):
        validate_action_inventory(value)


def test_subevent_must_stay_inside_parent_window():
    value = inventory()
    value["actions"][1]["temporal_mode"] = "staggered"
    value["actions"][1]["subevents"] = [{
        "subevent_id":"A2.1", "start_frame":4, "impact_frame":7, "end_frame":8,
        "verb":"word_reveal", "target":"word", "parameters":{},
        "authority":"evidence_bound_inference", "confidence":0.8, "evidence_refs":["frame:4-8"]
    }]
    with pytest.raises(Exception):
        validate_action_inventory(value)


def test_continuous_action_adjudicates_internal_peak_without_fake_keyframe():
    value = inventory()
    value["actions"][1]["start_frame"] = 5
    value["actions"][1]["impact_frame"] = 5
    value["actions"][1]["end_frame"] = 9
    value["actions"][1]["temporal_mode"] = "continuous"
    row = adjudicate_peak(value, 7, tolerance_frames=1)
    assert row.status == "continuous"


def test_detect_peaks_and_gauntlet_coverage():
    values = [0, 1, 5, 1, 0, 0, 2, 9, 2, 0]
    peaks = detect_local_peaks(values, percentile=70, min_separation=2)
    assert 2 in peaks and 7 in peaks
    report = gauntlet_coverage_from_frame_metrics(inventory(), metrics(values))
    assert report["observable_action_closed"]
    assert report["mad_p90_coverage"] == 1.0
    assert report["deep_unexplained_frames"] == []
    assert report["frame_metric_identity"] == "explicit_contiguous_zero_based"


def test_unmapped_peak_is_visible_failure():
    value = inventory()
    value["actions"][1]["start_frame"] = 6
    values = [0] * 10
    values[5] = 10
    report = gauntlet_coverage_from_frame_metrics(value, metrics(values))
    assert not report["observable_action_closed"]
    assert 5 in report["uncovered_mad_frames"]


def test_frame_metric_reorder_duplicate_truncation_and_nonfinite_poison_fail_closed():
    value = inventory()

    reordered = metrics([0] * 10)
    reordered["frames"][4]["frame"], reordered["frames"][5]["frame"] = 5, 4
    with pytest.raises(ActionInventoryError, match="identity/order mismatch"):
        gauntlet_coverage_from_frame_metrics(value, reordered)

    duplicated = metrics([0] * 10)
    duplicated["frames"][5]["frame"] = 4
    with pytest.raises(ActionInventoryError, match="identity/order mismatch"):
        gauntlet_coverage_from_frame_metrics(value, duplicated)

    truncated = metrics([0] * 9)
    with pytest.raises(ActionInventoryError, match="coverage mismatch"):
        gauntlet_coverage_from_frame_metrics(value, truncated)

    poisoned = metrics([0] * 10)
    poisoned["frames"][5]["mad"] = float("nan")
    with pytest.raises(ActionInventoryError, match="finite non-negative"):
        gauntlet_coverage_from_frame_metrics(value, poisoned)


def test_confidence_and_peak_metric_domains_fail_closed():
    value = inventory()
    value["actions"][0]["confidence"] = 1.1
    with pytest.raises(Exception):
        validate_action_inventory(value)

    with pytest.raises(ActionInventoryError, match="finite non-negative"):
        detect_local_peaks([0.0, float("inf"), 0.0])
