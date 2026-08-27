from __future__ import annotations

import copy
import tempfile
from pathlib import Path

import pytest

from src.avatar.render_guard import RenderIntent, RenderState
from src.avatar.transactional_store import SQLiteTransactionalRenderStore
from src.content.integrity import seal_manifest
from src.content.provenance_chain import attach_provenance_chain, verify_provenance_chain, downstream_handoff_record


def _intent(intent_id="RND_TEST"):
    return RenderIntent(
        intent_id=intent_id,
        content_id="CNT_1",
        profile_id="heygen_rot_canonical_v1",
        script_hash="abc",
        state=RenderState.AUTHORIZED,
        estimated_credits=9.0,
    )


def test_fencing_token_rejects_stale_writer_after_reacquire():
    with tempfile.TemporaryDirectory() as td:
        store = SQLiteTransactionalRenderStore(Path(td) / "authority.db")
        lease1 = store.acquire_lease("RND_TEST", "worker-a", ttl_s=30)
        store.put_intent(_intent(), lease1)
        store.release_lease(lease1)
        lease2 = store.acquire_lease("RND_TEST", "worker-b", ttl_s=30)
        assert lease2.fencing_token > lease1.fencing_token
        with pytest.raises(RuntimeError):
            store.put_intent(_intent(), lease1)
        running = RenderIntent(**{**_intent().__dict__, "state": RenderState.RUNNING})
        store.put_intent(running, lease2)
        assert store.get_intent("RND_TEST").state == RenderState.RUNNING


def test_live_lease_blocks_other_owner():
    with tempfile.TemporaryDirectory() as td:
        store = SQLiteTransactionalRenderStore(Path(td) / "authority.db")
        store.acquire_lease("RND_TEST", "worker-a", ttl_s=30)
        with pytest.raises(RuntimeError):
            store.acquire_lease("RND_TEST", "worker-b", ttl_s=30)


def test_provenance_chain_breaks_after_semantic_mutation():
    source = {
        "source_ref": "https://example.test/source",
        "content_fingerprint": "sourcehash",
        "trust_class": "UNTRUSTED_SOURCE_DATA",
        "claims": [],
    }
    manifest = {
        "content_id": "CNT_1",
        "schema_version": 2,
        "script_display_text": "Texto base.",
        "script_tts_text": "Texto base.",
        "semantic_beats": [{"id": "B00_HOOK", "function": "hook", "text": "Texto base.", "claim_ids": []}],
        "avatar": {"profile_id": "heygen_rot_canonical_v1"},
        "source_refs": [source["source_ref"]],
    }
    with_chain = attach_provenance_chain(source, manifest)
    assert verify_provenance_chain(source, with_chain)
    mutated = copy.deepcopy(with_chain)
    mutated["semantic_beats"][0]["text"] = "Texto manipulado."
    assert not verify_provenance_chain(source, mutated)


def test_downstream_handoff_requires_seal_and_provenance():
    source = {"source_ref": "s", "content_fingerprint": "h", "trust_class": "UNTRUSTED_SOURCE_DATA", "claims": []}
    manifest = {
        "content_id": "CNT_1", "schema_version": 2, "source_refs": ["s"], "claim_notes": [],
        "viral_driver": "MONEY", "secondary_driver": None, "core_thesis": "x", "hook": "x",
        "script_display_text": "x", "script_tts_text": "x",
        "semantic_beats": [{"id": "B00_HOOK", "function": "hook", "text": "x"}],
        "cta": {"text": "x"}, "moral": "x", "duration_target_s": 35,
        "avatar": {"profile_id": "heygen_rot_canonical_v1"},
    }
    chained = attach_provenance_chain(source, manifest)
    with pytest.raises(ValueError):
        downstream_handoff_record(chained)
    sealed = seal_manifest(chained)
    record = downstream_handoff_record(sealed)
    assert record["provenance_root"].startswith("PRV_")
    assert record["replay_fingerprint"].startswith("MNF_")
