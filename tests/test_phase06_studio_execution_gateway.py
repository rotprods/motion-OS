from __future__ import annotations

from copy import deepcopy

import pytest

from src.content.integrity import seal_manifest
from src.content.provenance_chain import attach_provenance_chain, downstream_handoff_record
from src.content.studio_execution_gateway import (
    StudioExecutionRejected,
    authorize_studio_execution,
    execute_verified_studio_handoff,
)


def _sealed_manifest() -> tuple[dict, dict]:
    source = {
        "source_ref": "fixture:studio-gateway",
        "content_fingerprint": "SRC_TEST",
        "trust_class": "trusted_fixture",
        "claims": [],
    }
    manifest = {
        "content_id": "CONTENT_STUDIO_GATE",
        "schema_version": 2,
        "source_refs": ["fixture:studio-gateway"],
        "claim_notes": [],
        "claims": [],
        "viral_driver": "UTILITY",
        "secondary_driver": None,
        "core_thesis": "authority before execution",
        "hook": "gate before render",
        "script_display_text": "authority before execution",
        "script_tts_text": "authority before execution",
        "semantic_beats": [
            {"id": "B00_HOOK", "text": "authority", "factual": False, "claim_ids": [], "function": "hook"},
            {"id": "B01_PROOF", "text": "execution", "factual": False, "claim_ids": [], "function": "proof"},
        ],
        "cta": {"text": "continue"},
        "moral": "fail closed",
        "duration_target_s": 35,
        "avatar": {"profile_id": "p"},
        "render": {"provider_job_id": "job_123"},
    }
    with_provenance = attach_provenance_chain(source, manifest)
    sealed = seal_manifest(with_provenance)
    return sealed, downstream_handoff_record(sealed)


def test_valid_handoff_authorizes_studio_context():
    sealed, handoff = _sealed_manifest()
    ctx = authorize_studio_execution(sealed, handoff)
    assert ctx.content_id == "CONTENT_STUDIO_GATE"
    assert ctx.provenance_root.startswith("PRV_")
    assert ctx.replay_fingerprint.startswith("MNF_")
    assert ctx.semantic_beat_ids == ("B00_HOOK", "B01_PROOF")
    assert ctx.render_job_id == "job_123"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provenance_root", "PRV_MUTATED"),
        ("replay_fingerprint", "MNF_MUTATED"),
        ("semantic_beat_ids", ["B00_HOOK", "B99_MUTATED"]),
        ("content_id", "OTHER_CONTENT"),
        ("render_job_id", "other_job"),
    ],
)
def test_handoff_mutation_rejects_before_executor(field, value):
    sealed, handoff = _sealed_manifest()
    mutated = deepcopy(handoff)
    mutated[field] = value
    calls: list[str] = []

    def executor(_ctx):
        calls.append("called")
        return "UNREACHABLE"

    with pytest.raises(StudioExecutionRejected):
        execute_verified_studio_handoff(sealed, mutated, executor)
    assert calls == []


def test_manifest_mutation_rejects_before_executor():
    sealed, handoff = _sealed_manifest()
    mutated = deepcopy(sealed)
    mutated["semantic_beats"][0]["id"] = "B99_TAMPERED"
    calls: list[str] = []

    with pytest.raises(StudioExecutionRejected):
        execute_verified_studio_handoff(mutated, handoff, lambda _ctx: calls.append("called"))
    assert calls == []


def test_duplicate_manifest_beat_identity_is_fail_closed():
    sealed, handoff = _sealed_manifest()
    mutated = deepcopy(sealed)
    mutated["semantic_beats"][1]["id"] = "B00_HOOK"
    # Integrity is now invalid as well, which must reject before identity can be consumed.
    with pytest.raises(StudioExecutionRejected):
        authorize_studio_execution(mutated, handoff)
