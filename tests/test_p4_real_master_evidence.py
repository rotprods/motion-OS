from __future__ import annotations

from pathlib import Path
import hashlib
import json


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "p4_rc06_real_master_recovery_2026-08-31.json"
STATE = ROOT / "state" / "p4_real_master_authority.json"


def canonical_sha(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_p4_rc06_recovery_evidence_is_exact_and_self_consistent():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    anchor = evidence["recovery_anchor"]
    result = evidence["recovery_result"]
    materialization = evidence["materialization"]

    assert evidence["status"] == "RECOVERED_EXACT"
    assert evidence["authority"] == "EXACT_IDENTITY_VERIFIED"
    assert result["exact"] is True
    assert result["errors"] == []
    assert anchor["registry_sha256"] == materialization["observed_sha256"] == result["observed_sha256"]
    assert anchor["expected_bytes"] == materialization["observed_bytes"] == result["observed_bytes"]
    assert evidence["gates"]["recoverable_real_master_exact_sha"] is True


def test_p4_recovery_contract_hash_is_deterministically_bound():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    contract = evidence["recovery_contract"]
    payload = {"identity": contract["identity"], "candidate": contract["candidate"]}
    assert canonical_sha(payload) == contract["contract_sha256"]


def test_p4_fails_closed_on_unrecoverable_rc09e_and_missing_provider():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    state = json.loads(STATE.read_text(encoding="utf-8"))

    assert evidence["historical_truth"]["selected_master"] == "RC09E"
    assert evidence["historical_truth"]["selected_master_status"] == "UNRECOVERABLE_EXACT_IDENTITY_UNKNOWN"
    assert evidence["multimodal_authority"]["authority"] == "NONE"
    assert evidence["gates"]["real_full_video_provider_run_bound_to_same_sha"] is False
    assert evidence["gates"]["p4_complete"] is False
    assert state["creative_master_selection"]["recovery_authority"] is False
    assert state["multimodal_provider"]["authoritative"] is False
    assert state["gates"]["project_done"] is False


def test_p3_mirror_is_not_allowed_to_masquerade_as_creative_master():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    mirror = evidence["p3_durable_mirror"]
    assert mirror["contained_master_sha256"] == "2c11f29609a3f093f10f1ac36c1291e4560bad6fe62e7fc2a1a8c468282735e0"
    assert mirror["role"] == "technical_renderer_proof_only_not_creative_canonical_master"
