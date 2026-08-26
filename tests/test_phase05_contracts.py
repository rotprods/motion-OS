import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load(name: str):
    return json.loads((SCHEMAS / name).read_text())


def test_editing_graph_contract_accepts_minimal_valid_graph():
    schema = load("editing_graph.schema.json")
    fixture = {
        "schema_version": "1.0.0",
        "graph_id": "graph_demo",
        "project_id": "project_demo",
        "graph_revision": 1,
        "nodes": [
            {
                "id": "brief_01",
                "kind": "Brief",
                "level": "L1_SEMANTIC",
                "authority": "authoritative",
                "provenance_refs": ["user_brief"],
                "data": {"goal": "launch product"},
            },
            {
                "id": "beat_01",
                "kind": "NarrativeBeat",
                "level": "L1_SEMANTIC",
                "authority": "inferred",
                "provenance_refs": ["brief_01"],
                "data": {"intent": "reveal"},
            },
            {
                "id": "scene_01",
                "kind": "Scene",
                "level": "L2_EDITING",
                "authority": "inferred",
                "provenance_refs": ["beat_01"],
                "data": {"start_ms": 0, "end_ms": 1000},
            },
        ],
        "edges": [
            {
                "id": "e1",
                "source": "brief_01",
                "target": "beat_01",
                "relation": "DRIVES",
                "required": True,
                "data": {},
            },
            {
                "id": "e2",
                "source": "beat_01",
                "target": "scene_01",
                "relation": "MATERIALIZES_AS",
                "required": True,
                "data": {},
            },
        ],
    }
    jsonschema.Draft202012Validator(schema).validate(fixture)


def test_skill_contract_requires_explicit_capability_and_fallback_policy():
    schema = load("skill.schema.json")
    fixture = {
        "skill_id": "video_reverse_engineer",
        "version": "1.0.0",
        "description": "Extract measured evidence from a source video.",
        "inputs": [{"name": "source_video", "schema_ref": "artifact://video", "required": True}],
        "outputs": [{"name": "feature_pack", "schema_ref": "schemas/feature_pack.schema.json", "required": True}],
        "requires": ["ffmpeg", "ffprobe"],
        "tools": ["ffmpeg"],
        "providers": [],
        "authority": "measured",
        "deterministic": True,
        "cost_class": "low",
        "latency_class": "seconds",
        "failure_modes": ["ffmpeg_unavailable", "decode_failed"],
        "fallbacks": [],
        "qa": ["feature_pack_schema_valid", "provenance_complete"],
        "graph_effects": {
            "creates_node_kinds": ["Shot", "Artifact"],
            "creates_relations": ["PRODUCED_BY"],
            "may_mutate": [],
        },
    }
    jsonschema.Draft202012Validator(schema).validate(fixture)


def test_provider_asset_contract_keeps_reference_only_asset_noncommercial_by_default():
    schema = load("provider_asset.schema.json")
    fixture = {
        "asset_id": "ref_pin_01",
        "provider": "pinterest",
        "source_ref": "https://example.invalid/reference",
        "asset_type": "reference",
        "sha256": None,
        "policy": {
            "usage_class": "reference_only",
            "license_state": "unknown",
            "license_ref": None,
            "attribution_required": None,
            "notes": "Reference discovery only until rights are verified.",
        },
        "provenance": {
            "discovered_at": "2026-08-26T00:00:00Z",
            "discovery_method": "provider_search",
            "query": "premium motion reference",
            "parent_reference_id": None,
            "downloaded_at": None,
        },
        "technical": {},
        "fitness": {
            "resolution": None,
            "semantic_match": 0.9,
            "style_match": 0.9,
            "technical_fit": 0.0,
            "transparency_quality": None,
            "licensing_confidence": 0.0,
            "aggregate_score": None,
        },
        "status": "approved_reference",
        "rejection_reasons": [],
    }
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(fixture)


def test_provider_asset_rejects_invalid_sha256():
    schema = load("provider_asset.schema.json")
    fixture = {
        "asset_id": "asset_bad_hash",
        "provider": "local",
        "source_ref": "local://asset.png",
        "asset_type": "image",
        "sha256": "not-a-sha",
        "policy": {"usage_class": "owned", "license_state": "owned"},
        "provenance": {"discovered_at": "2026-08-26T00:00:00Z", "discovery_method": "local_import"},
        "fitness": {"semantic_match": 1, "style_match": 1, "technical_fit": 1, "licensing_confidence": 1},
        "status": "approved_asset",
        "rejection_reasons": [],
    }
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    assert any(error.validator == "pattern" for error in validator.iter_errors(fixture))
