from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

CURRENT_SCHEMA_VERSION = 2
Migration = Callable[[dict[str, Any]], dict[str, Any]]


def _v1_to_v2(document: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(document)
    out["schema_version"] = 2
    out.setdefault("claim_lineage", [])
    out.setdefault("integrity", None)
    out.setdefault("replica_metadata", {})
    render = out.setdefault("render", {})
    render.setdefault("render_intent_id", None)
    render.setdefault("retry_count", 0)
    render.setdefault("reconciliation_required", False)
    return out


MIGRATIONS: dict[int, Migration] = {1: _v1_to_v2}


def detect_schema_version(document: dict[str, Any]) -> int:
    raw = document.get("schema_version", 1)
    try:
        version = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid schema_version") from exc
    if version < 1:
        raise ValueError("schema_version must be >= 1")
    return version


def migrate(document: dict[str, Any], *, target_version: int = CURRENT_SCHEMA_VERSION) -> dict[str, Any]:
    current = detect_schema_version(document)
    if current > target_version:
        raise ValueError(f"document schema v{current} is newer than supported v{target_version}")
    out = deepcopy(document)
    while current < target_version:
        migration = MIGRATIONS.get(current)
        if migration is None:
            raise ValueError(f"no migration registered from schema v{current}")
        out = migration(out)
        next_version = detect_schema_version(out)
        if next_version <= current:
            raise RuntimeError("migration did not advance schema version")
        current = next_version
    return out


def assert_current_schema(document: dict[str, Any]) -> None:
    version = detect_schema_version(document)
    if version != CURRENT_SCHEMA_VERSION:
        raise ValueError(f"schema v{version} requires migration to v{CURRENT_SCHEMA_VERSION}")
