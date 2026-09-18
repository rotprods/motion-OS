from pathlib import Path

from scripts.validate_v2_hypergraph import validate


ROOT = Path(__file__).resolve().parents[1]


def test_v2_hypergraph_schema_and_semantics_are_valid():
    errors = validate(
        ROOT / "schemas" / "v2_hypergraph.schema.json",
        ROOT / "graph" / "v2" / "motion_os_v2_hypergraph.json",
    )
    assert errors == []


def test_v2_validator_uses_real_jsonschema_format_checker():
    source = (ROOT / "scripts" / "validate_v2_hypergraph.py").read_text(encoding="utf-8")
    assert "FormatChecker()" in source
    assert "Draft202012Validator" in source


def test_v2_hypergraph_preserves_unknown_authority_instead_of_self_promoting():
    import json

    graph = json.loads((ROOT / "graph" / "v2" / "motion_os_v2_hypergraph.json").read_text(encoding="utf-8"))
    snapshot = graph["snapshot"]
    assert snapshot["runtime_event_watermark"] is None
    assert snapshot["authority"] == "IMPLEMENTED"
