from __future__ import annotations

from copy import deepcopy
from typing import Any
import hashlib
import json


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def build_provenance_chain(*, source_pack: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    claims = manifest.get("claims", source_pack.get("claims", []))
    beats = manifest.get("semantic_beats", [])
    source_digest = _hash({
        "source_ref": source_pack.get("source_ref"),
        "content_fingerprint": source_pack.get("content_fingerprint"),
        "trust_class": source_pack.get("trust_class"),
    })
    claims_digest = _hash([
        {
            "claim_id": c.get("claim_id"),
            "proposition": c.get("proposition"),
            "source_ref": c.get("source_ref"),
            "evidence_strength": c.get("evidence_strength"),
            "freshness": c.get("freshness"),
        }
        for c in claims
    ])
    beats_digest = _hash([
        {
            "id": b.get("id"),
            "text": b.get("text"),
            "factual": b.get("factual", False),
            "claim_ids": b.get("claim_ids", []),
            "function": b.get("function"),
        }
        for b in beats
    ])
    script_digest = _hash({
        "display": manifest.get("script_display_text"),
        "tts": manifest.get("script_tts_text"),
    })
    avatar_digest = _hash(manifest.get("avatar", {}))
    chain = [source_digest, claims_digest, beats_digest, script_digest, avatar_digest]
    root = "PRV_" + hashlib.sha256("|".join(chain).encode("utf-8")).hexdigest()[:32].upper()
    return {
        "version": 1,
        "root": root,
        "source_digest": source_digest,
        "claims_digest": claims_digest,
        "beats_digest": beats_digest,
        "script_digest": script_digest,
        "avatar_digest": avatar_digest,
    }


def attach_provenance_chain(source_pack: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(manifest)
    out["provenance_chain"] = build_provenance_chain(source_pack=source_pack, manifest=out)
    return out


def verify_provenance_chain(source_pack: dict[str, Any], manifest: dict[str, Any]) -> bool:
    observed = manifest.get("provenance_chain")
    if not isinstance(observed, dict):
        return False
    expected = build_provenance_chain(source_pack=source_pack, manifest=manifest)
    return observed == expected


def downstream_handoff_record(manifest: dict[str, Any]) -> dict[str, Any]:
    integrity = manifest.get("integrity") or {}
    provenance = manifest.get("provenance_chain") or {}
    if not integrity.get("replay_fingerprint") or not provenance.get("root"):
        raise ValueError("sealed manifest and provenance chain required before downstream handoff")
    return {
        "content_id": manifest.get("content_id"),
        "replay_fingerprint": integrity["replay_fingerprint"],
        "provenance_root": provenance["root"],
        "semantic_beat_ids": [b.get("id") for b in manifest.get("semantic_beats", [])],
        "render_job_id": (manifest.get("render") or {}).get("provider_job_id"),
    }
