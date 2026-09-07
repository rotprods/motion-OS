from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
from typing import Any, Mapping

_HEX40_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _node_data(node: Any) -> Mapping[str, Any]:
    attrs = getattr(node, "attrs", {}) or {}
    data = attrs.get("data", attrs)
    return data if isinstance(data, Mapping) else {}


def _valid_hex(value: object, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _artifact_refs_valid(values: object) -> bool:
    if not isinstance(values, list) or not values:
        return False
    return all(isinstance(item, str) and bool(item.strip()) for item in values)


def _assigned_layer_ids(render_manifest: Mapping[str, Any]) -> set[str]:
    assignments = render_manifest.get("assignments")
    if not isinstance(assignments, list):
        raise ValueError("render_manifest.assignments must be a list")
    assigned: set[str] = set()
    for item in assignments:
        if not isinstance(item, Mapping):
            raise ValueError("render assignment must be an object")
        node_id = item.get("node_id")
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("render assignment node_id must be a non-empty string")
        if node_id in assigned:
            raise ValueError("render assignment node_id must be unique")
        assigned.add(node_id)
    return assigned


def inspect_project(graph: Any, *, render_manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    kinds = Counter(node.kind for node in graph.nodes)
    layers = [node for node in graph.nodes if node.kind == "Layer"]
    layer_ids = {node.id for node in layers}

    provenance_gaps: list[str] = []
    for node in graph.nodes:
        data = _node_data(node)
        attrs = getattr(node, "attrs", {}) or {}
        if (
            node.kind in {"Asset", "Artifact"}
            and not attrs.get("provenance_refs")
            and not data.get("provenance")
        ):
            provenance_gaps.append(node.id)

    render_manifest_present = render_manifest is not None
    if render_manifest is None:
        unresolved = sorted(layer_ids)
    elif not isinstance(render_manifest, Mapping):
        raise ValueError("render_manifest must be an object or null")
    else:
        assigned = _assigned_layer_ids(render_manifest)
        unresolved = sorted(layer_ids - assigned)

    scenes = sorted(
        [node for node in graph.nodes if node.kind == "Scene"],
        key=lambda node: _node_data(node).get("start_ms", 0),
    )
    timeline = []
    for scene in scenes:
        data = _node_data(scene)
        timeline.append(
            {
                "id": scene.id,
                "start_ms": data.get("start_ms"),
                "end_ms": data.get("end_ms"),
            }
        )

    snapshot = {
        "graph_id": getattr(graph, "graph_id", None),
        "project_id": getattr(graph, "project_id", None),
        "graph_revision": getattr(graph, "graph_revision", None),
        "graph_hash": graph.content_hash() if hasattr(graph, "content_hash") else None,
        "node_counts": dict(sorted(kinds.items())),
        "edge_count": len(graph.edges),
        "timeline": timeline,
        "render_manifest_present": render_manifest_present,
        "provenance_gaps": sorted(provenance_gaps),
        "unresolved_layers": unresolved,
    }
    snapshot["snapshot_hash"] = hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return snapshot


def recovery_manifest(
    graph: Any,
    *,
    git_sha: str,
    asset_manifest_hash: str | None,
    render_manifest: dict[str, Any] | None,
    qa_summary: dict[str, Any] | None,
    artifact_refs: list[str] | None = None,
) -> dict[str, Any]:
    snapshot = inspect_project(graph, render_manifest=render_manifest)
    render_manifest_hash = (
        render_manifest.get("manifest_hash")
        if isinstance(render_manifest, Mapping)
        else None
    )
    normalized_artifacts = sorted(artifact_refs or [])
    requirements = {
        "graph_hash_present": _valid_hex(snapshot["graph_hash"], _HEX64_RE),
        "git_sha_valid": _valid_hex(git_sha, _HEX40_RE),
        "asset_manifest_hash_valid": _valid_hex(asset_manifest_hash, _HEX64_RE),
        "render_manifest_present": snapshot["render_manifest_present"],
        "render_manifest_hash_valid": _valid_hex(render_manifest_hash, _HEX64_RE),
        "qa_summary_present": isinstance(qa_summary, Mapping) and bool(qa_summary),
        "artifact_refs_present": _artifact_refs_valid(artifact_refs),
        "no_unresolved_layers": not snapshot["unresolved_layers"],
        "no_provenance_gaps": not snapshot["provenance_gaps"],
    }
    manifest = {
        "git_sha": git_sha,
        "graph_id": snapshot["graph_id"],
        "graph_revision": snapshot["graph_revision"],
        "graph_hash": snapshot["graph_hash"],
        "asset_manifest_hash": asset_manifest_hash,
        "render_manifest_hash": render_manifest_hash,
        "qa_summary": qa_summary or {},
        "artifact_refs": normalized_artifacts,
        "zero_context_requirements": requirements,
        "recovery_ready": all(requirements.values()),
    }
    manifest["manifest_hash"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return manifest
