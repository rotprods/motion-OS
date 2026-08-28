from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import hashlib
import json


class NextIterationPromptError(ValueError):
    pass


@dataclass(frozen=True)
class ContinuationPacket:
    project_id: str
    previous_session_id: str
    workstream_id: str
    correlation_id: str
    last_main_sha: str
    event_watermark: str
    branch: str | None
    pr: int | None
    head_sha: str | None
    authority_state: str
    completed_work: tuple[str, ...]
    exact_tests: tuple[str, ...]
    gauntlet_findings: tuple[str, ...]
    blockers: tuple[str, ...]
    external_degraded: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    released_scopes: tuple[str, ...]
    next_wave: dict[str, Any]


def _canonical_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def compile_continuation_packet(state: dict[str, Any], next_wave: dict[str, Any]) -> dict[str, Any]:
    required = ["project_id", "session_id", "workstream_id", "correlation_id", "live_main_sha", "event_watermark", "authority_state"]
    missing = [key for key in required if not state.get(key)]
    if missing:
        raise NextIterationPromptError(f"missing continuation fields: {missing}")
    if next_wave.get("decision") not in {"EXECUTE", "BLOCKED"}:
        raise NextIterationPromptError("next_wave must be an authoritative compiler result")

    payload = {
        "schema": "motion-os.next-iteration/v1",
        "project_id": state["project_id"],
        "previous_session_id": state["session_id"],
        "workstream_id": state["workstream_id"],
        "correlation_id": state["correlation_id"],
        "last_main_sha": state["live_main_sha"],
        "event_watermark": state["event_watermark"],
        "branch": state.get("branch"),
        "pr": state.get("pr"),
        "head_sha": state.get("head_sha"),
        "authority_state": state["authority_state"],
        "completed_work": list(state.get("completed_work", [])),
        "exact_tests": list(state.get("exact_tests", [])),
        "gauntlet_findings": list(state.get("gauntlet_findings", [])),
        "blockers": list(state.get("blockers", [])),
        "external_degraded": list(state.get("external_degraded", [])),
        "evidence_refs": list(state.get("evidence_refs", [])),
        "released_scopes": list(state.get("released_scopes", [])),
        "next_wave": next_wave,
        "freshness_contract": {
            "must_recheck_live_main_sha": True,
            "must_recheck_event_watermark": True,
            "must_recheck_active_claims": True,
            "must_recheck_pr_lifecycle": True,
            "invalidate_on_any_material_drift": True,
        },
    }
    payload["packet_sha256"] = _canonical_hash(payload)
    return payload


def render_metaprompt(packet: dict[str, Any]) -> str:
    nw = packet["next_wave"]
    selected = nw.get("selected") or {}
    decision = nw["decision"]
    lines = [
        "/autoprompt",
        "",
        "You are the next autonomous MOTION.OS execution session.",
        "Do not rely on prior chat memory. This continuation packet is an acceleration hint, not authority.",
        "",
        f"PACKET_SHA256: {packet['packet_sha256']}",
        f"PREVIOUS_MAIN_SHA: {packet['last_main_sha']}",
        f"PREVIOUS_EVENT_WATERMARK: {packet['event_watermark']}",
        f"PREVIOUS_AUTHORITY_STATE: {packet['authority_state']}",
        "",
        "MANDATORY BOOTSTRAP:",
        "1. Read live GitHub main/PR/CI state.",
        "2. Read latest Event Fabric #39 watermark and active claims.",
        "3. Read Issue #48 while open plus canonical repo state.",
        "4. Compare live main SHA, watermark, claims and PR lifecycle against this packet.",
        "5. If any material drift exists, INVALIDATE THIS PACKET and recompute the next wave.",
        "6. Create a new unique session_id and emit WORK_STARTED before mutation.",
        "",
        f"COMPILED_DECISION: {decision}",
    ]
    if decision == "EXECUTE":
        lines += [
            f"NEXT_TASK_ID: {selected.get('task_id')}",
            f"NEXT_TITLE: {selected.get('title')}",
            f"NEXT_PRIORITY: {selected.get('priority')}",
            f"TARGET_BRANCH: {selected.get('branch')}",
            "RESOURCE_SCOPE:",
            *[f"- {scope}" for scope in selected.get("resource_scope", [])],
            "LOCAL_VERIFY_PROFILES:",
            *[f"- {profile}" for profile in selected.get("local_profiles", [])],
            "ADVERSARIAL_TESTS:",
            *[f"- {test}" for test in selected.get("adversarial_tests", [])],
            "",
            "EXECUTION LOOP:",
            "OBSERVE → CLAIM → IMPLEMENT → LOCAL TEST → /gauntlet-loop → CODE REVIEW → SECURITY REVIEW → CLEAN RUNNER → CHECKPOINT → RECONCILE → COMPILE NEXT ITERATION.",
            "Use an independent verifier mindset. Maximum 3 materially distinct repair attempts per failing invariant; if stuck, persist BLOCKED instead of cycling.",
        ]
    else:
        lines += [
            f"BLOCK_REASON: {nw.get('reason')}",
            f"NEXT_ACTION: {nw.get('next_action', 'reconstruct live truth and stop if still blocked')}",
        ]
    lines += [
        "",
        "SESSION CLOSURE:",
        "Persist exact tests, findings, evidence, blockers, released scopes and authority state.",
        "Then recompute live truth and overwrite the canonical NEXT_ITERATION_METAPROMPT with a newly sealed packet for the following session.",
    ]
    return "\n".join(lines) + "\n"
