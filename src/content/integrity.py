from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable
import hashlib
import json


DEFAULT_SEALED_FIELDS = (
    "content_id",
    "schema_version",
    "source_refs",
    "claim_notes",
    "viral_driver",
    "secondary_driver",
    "core_thesis",
    "hook",
    "script_display_text",
    "script_tts_text",
    "semantic_beats",
    "cta",
    "moral",
    "duration_target_s",
    "avatar",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def manifest_projection(manifest: dict[str, Any], fields: Iterable[str] = DEFAULT_SEALED_FIELDS) -> dict[str, Any]:
    return {field: deepcopy(manifest.get(field)) for field in fields}


def replay_fingerprint(manifest: dict[str, Any], *, fields: Iterable[str] = DEFAULT_SEALED_FIELDS) -> str:
    return "MNF_" + sha256_json(manifest_projection(manifest, fields))[:24].upper()


def seal_manifest(manifest: dict[str, Any], *, fields: Iterable[str] = DEFAULT_SEALED_FIELDS) -> dict[str, Any]:
    out = deepcopy(manifest)
    selected = tuple(fields)
    projection = manifest_projection(out, selected)
    out["integrity"] = {
        "algorithm": "sha256",
        "sealed_fields": list(selected),
        "payload_hash": sha256_json(projection),
        "replay_fingerprint": replay_fingerprint(out, fields=selected),
    }
    return out


def verify_manifest(manifest: dict[str, Any]) -> bool:
    integrity = manifest.get("integrity") or {}
    if integrity.get("algorithm") != "sha256":
        return False
    fields = integrity.get("sealed_fields")
    expected = integrity.get("payload_hash")
    fingerprint = integrity.get("replay_fingerprint")
    if not isinstance(fields, list) or not expected or not fingerprint:
        return False
    projection = manifest_projection(manifest, fields)
    return sha256_json(projection) == expected and replay_fingerprint(manifest, fields=fields) == fingerprint


def assert_manifest_integrity(manifest: dict[str, Any]) -> None:
    if not verify_manifest(manifest):
        raise ValueError("manifest integrity verification failed")
