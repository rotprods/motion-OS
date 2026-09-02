from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _bounded_paths(values: object, *, limit: int = 128) -> list[str]:
    if not isinstance(values, list):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        path = str(value).strip().replace("\\", "/")
        if not path or path in seen:
            continue
        seen.add(path)
        out.append(path)
        if len(out) >= limit:
            break
    return out


def load_structural_context(root: Path) -> dict[str, dict[str, Any]]:
    """Reuse an existing repository-owned graph as retrieval metadata, never as new authority."""
    graph_path = root.resolve() / "GRAPH" / "graph.json"
    if not graph_path.exists() or graph_path.stat().st_size > 16 * 1024 * 1024:
        return {}
    try:
        parsed = json.loads(graph_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    nodes = parsed.get("nodes") if isinstance(parsed, dict) else None
    if not isinstance(nodes, list):
        return {}

    community_by_path: dict[str, dict[str, Any]] = {}
    communities_path = graph_path.with_name("communities.json")
    if communities_path.exists() and communities_path.stat().st_size <= 16 * 1024 * 1024:
        try:
            communities_doc = json.loads(communities_path.read_text(encoding="utf-8"))
            communities = communities_doc.get("communities") if isinstance(communities_doc, dict) else communities_doc
            if isinstance(communities, list):
                for community in communities:
                    if not isinstance(community, dict):
                        continue
                    summary = {"id": community.get("id"), "label": community.get("label"), "top_dir": community.get("topDir")}
                    for member in _bounded_paths(community.get("members"), limit=10000):
                        community_by_path[member] = summary
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            community_by_path = {}

    context: dict[str, dict[str, Any]] = {}
    for raw in nodes:
        if not isinstance(raw, dict):
            continue
        path = str(raw.get("file") or raw.get("id") or "").strip().replace("\\", "/")
        if not path:
            continue
        deps_raw = raw.get("deps")
        dependents_raw = raw.get("dependents")
        deps = _bounded_paths(deps_raw)
        dependents = _bounded_paths(dependents_raw)
        context[path] = {
            "authority": "repository_graph_projection",
            "source": "GRAPH/graph.json",
            "node_type": raw.get("type"),
            "dependency_count": len(deps_raw) if isinstance(deps_raw, list) else len(deps),
            "dependent_count": len(dependents_raw) if isinstance(dependents_raw, list) else len(dependents),
            "dependencies": deps,
            "dependents": dependents,
        }
        if path in community_by_path:
            context[path]["community"] = community_by_path[path]
    return context
