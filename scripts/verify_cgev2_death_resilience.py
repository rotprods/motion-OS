from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "state/cgev2/death_resilience_contextpack_2026-09-01.json"
GRAPH = ROOT / "graph/cgev2/death_resilience_graph_2026-09-01.json"
HANDOFF = ROOT / "coordination/cgev2/CGEV2_DEATH_RESILIENCE_HANDOFF_2026-09-01.md"
NEXT = ROOT / "coordination/cgev2/NEXT_ITERATION_METAPROMPT_2026-09-01.md"
CONTINUITY = ROOT / "PROJECT_CONTINUITY_MASTER.md"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
PROJECT_DONE_TRUE = re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:status\s*:\s*)?PROJECT_DONE\s*=\s*true\s*$")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint(ctx: dict) -> str:
    anchors = ctx["live_truth_anchor"]
    by_id = {item["id"]: item for item in ctx["active_programs"]}
    values = [
        anchors["main_sha"],
        str(anchors["event_bus"]["latest_comment_id_at_capture"]),
        anchors["promotion_barrier"]["state"],
        by_id["P3"]["head"],
        by_id["P3_FRAME"]["head"],
        by_id["P4"]["head"],
        by_id["P7"]["head"],
        by_id["T08"]["head"],
    ]
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()


def validate_packet(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    required = [CONTEXT, GRAPH, HANDOFF, NEXT, CONTINUITY]
    for path in required:
        if not path.exists():
            errors.append(f"missing:{path.relative_to(ROOT)}")
    if errors:
        return errors

    ctx = _load(CONTEXT)
    graph = _load(GRAPH)

    if ctx.get("snapshot_authority") != "NON_AUTHORITATIVE_DERIVED_RECOVERY_SNAPSHOT":
        errors.append("snapshot_authority_must_be_derived")
    if ctx.get("refresh_before_mutation") is not True:
        errors.append("refresh_before_mutation_must_be_true")
    if ctx.get("project", {}).get("project_done") is not False:
        errors.append("snapshot_must_not_claim_project_done")
    if ctx.get("project", {}).get("release_status") != "BLOCKED":
        errors.append("snapshot_release_must_remain_blocked")

    anchors = ctx.get("live_truth_anchor", {})
    if not SHA40.fullmatch(str(anchors.get("main_sha", ""))):
        errors.append("invalid_main_sha")
    if anchors.get("main_protected") is not False:
        errors.append("capture_must_record_unprotected_main")
    barrier = anchors.get("promotion_barrier", {})
    if barrier.get("state") != "OPEN" or barrier.get("release_event_observed") is not False:
        errors.append("barrier_capture_must_fail_closed")

    expected = ctx.get("snapshot_fingerprint_sha256", "")
    if not SHA64.fullmatch(expected) or _fingerprint(ctx) != expected:
        errors.append("snapshot_fingerprint_mismatch")

    programs = ctx.get("active_programs", [])
    ids = [p.get("id") for p in programs]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_active_program_id")
    for program in programs:
        if not SHA40.fullmatch(str(program.get("head", ""))):
            errors.append(f"invalid_program_head:{program.get('id')}")

    blockers = ctx.get("external_blockers", [])
    if not blockers:
        errors.append("external_blockers_missing")
    for blocker in blockers:
        if blocker.get("state") != "BLOCKED_EXTERNAL":
            errors.append(f"external_blocker_not_blocked:{blocker.get('id')}")
        if not blocker.get("owner_type") or not blocker.get("resolution_trigger"):
            errors.append(f"external_blocker_missing_resolution:{blocker.get('id')}")

    path = ctx.get("critical_path", [])
    orders = [item.get("order") for item in path]
    if orders != list(range(1, len(path) + 1)):
        errors.append("critical_path_order_invalid")

    recovery = ctx.get("zero_context_recovery", {})
    if recovery.get("entry_rule") != "DO_NOT_START_BY_TRUSTING_THIS_SNAPSHOT":
        errors.append("recovery_entry_must_reject_snapshot_authority")
    if len(recovery.get("steps", [])) < 10:
        errors.append("recovery_steps_incomplete")
    required_invalidation = {"main_sha changed", "Issue39 watermark changed", "Issue48/barrier state changed"}
    if not required_invalidation.issubset(set(recovery.get("staleness_invalidation", []))):
        errors.append("staleness_invalidation_incomplete")

    own = set(ctx.get("own_write_scopes", []))
    foreign = set(ctx.get("foreign_owned_paths", []))
    if own & foreign:
        errors.append("write_scope_collision_with_foreign_owner")

    if graph.get("graph_authority") != "DERIVED_PROJECTION_NO_REVERSE_WRITES":
        errors.append("graph_must_be_derived")
    nodes = graph.get("nodes", [])
    node_ids = [n.get("id") for n in nodes]
    if len(node_ids) != len(set(node_ids)):
        errors.append("duplicate_graph_node")
    known = set(node_ids)
    for edge in graph.get("edges", []):
        if edge.get("source") not in known or edge.get("target") not in known:
            errors.append(f"dangling_edge:{edge}")

    continuity = CONTINUITY.read_text(encoding="utf-8")
    if "VERIFY LIVE TRUTH BEFORE EXECUTION" not in continuity:
        errors.append("continuity_pointer_missing_live_truth_gate")
    # Mentioning the forbidden state in explanatory prose is allowed; only an
    # affirmative standalone PROJECT_DONE=true status line is a false authority claim.
    if PROJECT_DONE_TRUE.search(continuity):
        errors.append("continuity_pointer_must_not_claim_done")
    if re.search(r"current main[^\n]*[0-9a-f]{40}", continuity, flags=re.I):
        errors.append("continuity_pointer_must_not_pin_volatile_main")

    next_text = NEXT.read_text(encoding="utf-8")
    if "/CGEV2" not in next_text or "/PROJECT-COMPLETION-ENGINE" not in next_text:
        errors.append("successor_protocol_sequence_missing")
    if "VERIFY LIVE TRUTH BEFORE EXECUTION" not in next_text:
        errors.append("successor_missing_live_truth_gate")

    return errors


def main() -> int:
    errors = validate_packet()
    payload = {"schema": "motion-os.cgev2-death-resilience-verifier/v1", "status": "PASS" if not errors else "FAIL", "errors": errors}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
