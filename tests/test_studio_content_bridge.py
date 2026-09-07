from __future__ import annotations

from copy import deepcopy

import pytest

from src.compilers.remotion import validate_scene_coverage
from src.content.integrity import seal_manifest
from src.content.provenance_chain import attach_provenance_chain, downstream_handoff_record
from src.content.studio_execution_gateway import StudioExecutionRejected
from src.studio.content_bridge import prepare_studio_execution


def _source_pack():
    return {
        "source_ref": "fixture://phase06-studio-bridge",
        "content_fingerprint": "fixture-content-v1",
        "trust_class": "UNTRUSTED_SOURCE_DATA",
        "claims": [],
    }


def _manifest(*, beat_count: int = 4):
    beats = []
    for index in range(beat_count):
        beat_id = f"B{index:02d}_BEAT"
        beats.append(
            {
                "id": beat_id,
                "function": "hook" if index == 0 else "proof",
                "text": f"Beat {index}",
                "target_duration_s": index + 1,
                "edit_cues": ["browser UI"] if index == 1 else [f"cue {index}"],
            }
        )
    return {
        "content_id": "bridge-demo-001",
        "schema_version": "1.0.0",
        "source_refs": ["fixture://phase06-studio-bridge"],
        "claim_notes": [],
        "viral_driver": "PERSONAL_GROWTH",
        "secondary_driver": "MONEY",
        "core_thesis": "A sealed Phase06 package becomes a Studio editing graph without losing beat identity.",
        "hook": "Bridge the package.",
        "script_display_text": "Bridge the package into Studio.",
        "script_tts_text": "Bridge the package into Studio.",
        "semantic_beats": beats,
        "cta": {"text": "Continue", "placement": "END", "target_beat_id": beats[-1]["id"]},
        "moral": "Authority precedes execution.",
        "duration_target_s": 12,
        "avatar": {"provider": "fixture", "profile_id": "fixture-avatar"},
        "render": {
            "provider": "fixture",
            "provider_job_id": "job-bridge-001",
            "status": "completed",
            "asset_ref": "fixture://avatar/job-bridge-001.mp4",
        },
        "downstream_edit_cues": [
            {
                "beat_id": beats[1]["id"],
                "intent": "show the authorized browser surface",
                "suggested_layer": "PRIMARY_UI",
            }
        ],
    }


def _sealed_and_handoff(manifest=None):
    manifest = deepcopy(manifest or _manifest())
    with_provenance = attach_provenance_chain(_source_pack(), manifest)
    sealed = seal_manifest(with_provenance)
    return sealed, downstream_handoff_record(sealed)


def test_phase06_authority_crosses_into_studio_without_losing_semantic_beat_ids():
    sealed, handoff = _sealed_and_handoff()
    bundle = prepare_studio_execution(sealed, handoff, fps=30, width=640, height=360)

    expected_ids = [beat["id"] for beat in sealed["semantic_beats"]]
    graph = bundle["graph"]
    beat_nodes = [node["id"] for node in graph["nodes"] if node["kind"] == "NarrativeBeat"]
    scene_nodes = [node for node in graph["nodes"] if node["kind"] == "Scene"]

    assert bundle["stage"] == "STUDIO_COMPILED"
    assert bundle["execution_started"] is True
    assert bundle["render_started"] is False
    assert bundle["semantic_beat_ids"] == expected_ids
    assert beat_nodes == expected_ids
    assert len(scene_nodes) == len(expected_ids)
    assert [scene["continuity_id"] for scene in scene_nodes] == expected_ids


def test_studio_bridge_preserves_arbitrary_upstream_beat_cardinality_not_three_beat_director_default():
    sealed, handoff = _sealed_and_handoff(_manifest(beat_count=8))
    bundle = prepare_studio_execution(sealed, handoff, fps=30, width=640, height=360)
    assert len(bundle["semantic_beat_ids"]) == 8
    assert len(bundle["runtime_spec"]["scenes"]) == 8
    assert len([n for n in bundle["graph"]["nodes"] if n["kind"] == "NarrativeBeat"]) == 8


def test_studio_bridge_is_gapless_and_runtime_frame_count_matches_authorized_target():
    sealed, handoff = _sealed_and_handoff()
    bundle = prepare_studio_execution(sealed, handoff, fps=30, width=640, height=360)
    runtime = bundle["runtime_spec"]
    assert validate_scene_coverage(runtime) == []
    assert runtime["project"] == {
        "fps": 30,
        "width": 640,
        "height": 360,
        "duration_frames": 360,
    }
    cursor = 0
    for scene in runtime["scenes"]:
        assert scene["from"] == cursor
        assert scene["durationInFrames"] > 0
        cursor += scene["durationInFrames"]
    assert cursor == 360


def test_every_studio_layer_is_bound_to_remotion_before_runtime_preparation():
    sealed, handoff = _sealed_and_handoff()
    bundle = prepare_studio_execution(sealed, handoff, fps=30, width=640, height=360)
    graph_layers = {node["id"] for node in bundle["graph"]["nodes"] if node["kind"] == "Layer"}
    assigned = {item["node_id"] for item in bundle["render_manifest"]["assignments"]}
    assert assigned == graph_layers
    assert {item["renderer"] for item in bundle["render_manifest"]["assignments"]} == {"remotion"}


def test_avatar_render_asset_is_carried_into_studio_graph_and_primary_layers():
    sealed, handoff = _sealed_and_handoff()
    bundle = prepare_studio_execution(sealed, handoff)
    assets = [node for node in bundle["graph"]["nodes"] if node["kind"] == "Asset"]
    assert len(assets) == 1
    assert assets[0]["data"]["source_ref"] == "fixture://avatar/job-bridge-001.mp4"
    primary = [
        node for node in bundle["graph"]["nodes"]
        if node["kind"] == "Layer" and node["data"]["attention_role"] == "primary"
    ]
    assert primary
    assert all(node["data"]["asset_ref"] == "asset:phase06-avatar-master" for node in primary)


def test_execution_bundle_is_deterministic_for_same_authorized_inputs():
    sealed, handoff = _sealed_and_handoff()
    first = prepare_studio_execution(sealed, handoff)
    second = prepare_studio_execution(sealed, handoff)
    for key in (
        "graph_hash",
        "asset_manifest_hash",
        "render_manifest",
        "remotion_spec_hash",
        "runtime_spec_hash",
        "execution_hash",
    ):
        assert first[key] == second[key]


def test_mutated_handoff_is_rejected_before_studio_execution_transition():
    sealed, handoff = _sealed_and_handoff()
    mutated = deepcopy(handoff)
    mutated["semantic_beat_ids"] = list(reversed(mutated["semantic_beat_ids"]))
    with pytest.raises(StudioExecutionRejected):
        prepare_studio_execution(sealed, mutated)


@pytest.mark.parametrize("bad_value", [0, -1, "zero", float("nan"), True])
def test_invalid_phase06_target_duration_fails_closed(bad_value):
    manifest = _manifest()
    manifest["duration_target_s"] = bad_value
    sealed, handoff = _sealed_and_handoff(manifest)
    with pytest.raises(ValueError, match="duration_target_s"):
        prepare_studio_execution(sealed, handoff)


@pytest.mark.parametrize("bad_value", [0, -1, "bad", float("inf"), True])
def test_invalid_beat_target_duration_fails_closed(bad_value):
    manifest = _manifest()
    manifest["semantic_beats"][1]["target_duration_s"] = bad_value
    sealed, handoff = _sealed_and_handoff(manifest)
    with pytest.raises(ValueError, match="target_duration_s"):
        prepare_studio_execution(sealed, handoff)


def test_orphan_downstream_cue_is_rejected_not_silently_dropped():
    manifest = _manifest()
    manifest["downstream_edit_cues"].append(
        {"beat_id": "B99_UNKNOWN", "intent": "orphan", "suggested_layer": "UI"}
    )
    sealed, handoff = _sealed_and_handoff(manifest)
    with pytest.raises(ValueError, match="unknown semantic beats"):
        prepare_studio_execution(sealed, handoff)


def test_duplicate_beat_ids_never_reach_studio_executor():
    manifest = _manifest()
    manifest["semantic_beats"][2]["id"] = manifest["semantic_beats"][1]["id"]
    sealed, handoff = _sealed_and_handoff(manifest)
    with pytest.raises(StudioExecutionRejected, match="unique"):
        prepare_studio_execution(sealed, handoff)


def test_primary_layer_routes_ui_cues_to_primary_ui_and_plain_cues_to_subject():
    sealed, handoff = _sealed_and_handoff()
    bundle = prepare_studio_execution(sealed, handoff)
    primary_by_beat = {}
    for node in bundle["graph"]["nodes"]:
        if node["kind"] == "Layer" and node["data"]["attention_role"] == "primary":
            beat_id = node["continuity_id"].split(":", 1)[0]
            primary_by_beat[beat_id] = node["data"]["layer_class"]
    assert primary_by_beat["B01_BEAT"] == "PRIMARY_UI"
    assert primary_by_beat["B00_BEAT"] == "SUBJECT"


def test_runtime_spec_contains_one_semantic_scene_start_event_per_authorized_beat():
    sealed, handoff = _sealed_and_handoff()
    bundle = prepare_studio_execution(sealed, handoff)
    runtime = bundle["runtime_spec"]
    assert [scene["id"] for scene in runtime["scenes"]] == [
        f"scene:{beat_id}" for beat_id in bundle["semantic_beat_ids"]
    ]
    assert all(len(scene["events"]) == 1 for scene in runtime["scenes"])
