#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "v2_hypergraph.schema.json"
DEFAULT_GRAPH = ROOT / "graph" / "v2" / "motion_os_v2_hypergraph.json"

UNCERTAINTY_TYPES = {"Unknown", "Risk", "ArchitectureDefect", "Blocker", "DeferredDecision"}
REQUIRED_COS = {f"L{i}" for i in range(17)}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def validate(schema_path: Path = DEFAULT_SCHEMA, graph_path: Path = DEFAULT_GRAPH) -> list[str]:
    schema = _load(schema_path)
    graph = _load(graph_path)
    errors: list[str] = []

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(validator.iter_errors(graph), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(x) for x in error.absolute_path) or "<root>"
        errors.append(f"schema:{where}: {error.message}")

    nodes = graph.get("nodes", [])
    edges = graph.get("hyperedges", [])
    node_ids = [node.get("id") for node in nodes]
    edge_ids = [edge.get("id") for edge in edges]

    if len(node_ids) != len(set(node_ids)):
        errors.append("semantic:nodes: duplicate node id")
    if len(edge_ids) != len(set(edge_ids)):
        errors.append("semantic:hyperedges: duplicate hyperedge id")

    known_nodes = set(node_ids)
    for edge in edges:
        for role, refs in edge.get("participants", {}).items():
            for ref in refs:
                if ref not in known_nodes:
                    errors.append(f"semantic:{edge.get('id')}:{role}: dangling node reference {ref}")

    for node in nodes:
        start = _parse_dt(node.get("valid_from"))
        end = _parse_dt(node.get("valid_to"))
        if start and end and end < start:
            errors.append(f"semantic:{node.get('id')}: valid_to precedes valid_from")
        if node.get("type") in UNCERTAINTY_TYPES:
            if not node.get("owner"):
                errors.append(f"semantic:{node.get('id')}: uncertainty/risk node requires owner")
            attrs = node.get("attributes", {})
            if not attrs.get("resolution_path"):
                errors.append(f"semantic:{node.get('id')}: uncertainty/risk node requires attributes.resolution_path")

    for edge in edges:
        start = _parse_dt(edge.get("valid_from"))
        end = _parse_dt(edge.get("valid_to"))
        if start and end and end < start:
            errors.append(f"semantic:{edge.get('id')}: valid_to precedes valid_from")

    dimension_prefixes = {key.split("_", 1)[0] for key in graph.get("cos_dimensions", {})}
    missing = sorted(REQUIRED_COS - dimension_prefixes)
    if missing:
        errors.append(f"semantic:cos_dimensions: missing required dimensions {missing}")

    snapshot = graph.get("snapshot", {})
    if snapshot.get("runtime_event_watermark") is None and snapshot.get("authority") in {"VERIFIED", "EMPIRICALLY_QUALIFIED"}:
        errors.append("authority:snapshot: cannot be VERIFIED without a runtime event watermark while Event Fabric v3 is unpromoted")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MOTION.OS V2 temporal hypergraph")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    args = parser.parse_args()
    errors = validate(args.schema, args.graph)
    if errors:
        for item in errors:
            print(item)
        return 1
    print(f"V2 hypergraph valid: {args.graph}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
