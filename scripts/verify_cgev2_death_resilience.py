from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

RELATIVE_PATHS = {
    "context": "state/cgev2/death_resilience_contextpack_2026-09-01.json",
    "graph": "graph/cgev2/death_resilience_graph_2026-09-01.json",
    "handoff": "coordination/cgev2/CGEV2_DEATH_RESILIENCE_HANDOFF_2026-09-01.md",
    "next": "coordination/cgev2/NEXT_ITERATION_METAPROMPT_2026-09-01.md",
    "continuity": "PROJECT_CONTINUITY_MASTER.md",
    "drive_mirror": "state/cgev2/death_resilience_drive_mirror_2026-09-01.json",
    "manifest": "state/cgev2/death_resilience_packet_manifest_2026-09-02.json",
    "verifier": "scripts/verify_cgev2_death_resilience.py",
}

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
PROJECT_DONE_TRUE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:status\s*:\s*)?PROJECT_DONE\s*=\s*true\s*$"
)

EXPECTED_PROTOCOL = {
    "universal_registry": {
        "repository": "rotprods/rot.knowledge",
        "path": "_hub/command-registry/registry.json",
        "exact_sha": "a44cf558585fb04c139d3058c6be7fb044021256",
    },
    "cgev2": {
        "command_id": "CMD-CGEV2",
        "canonical_name": "/CGEV2",
        "version": "2.0.0",
        "repository": "rotprods/fiscal-ai",
        "path": "commands/CGEV2.md",
        "exact_sha": "d0d1804bda26bfc1f2273df168724ca7087a785c",
    },
    "pce": {
        "command_id": "CMD-PCE",
        "canonical_name": "/PROJECT-COMPLETION-ENGINE",
        "repository": "rotprods/motion-OS",
        "path": "coordination/PROJECT_COMPLETION_ENGINE.md",
        "exact_sha": "f139c8202ffb34c67a269437947a2b8ef92564e5",
        "pr": 94,
        "issue": 93,
    },
}
EXPECTED_COMPOSITION = "COMP-CGEV2-PCE"
EXPECTED_RESOLUTION_FAILURE = "COMMAND_AUTHORITY_BLOCKED"
REQUIRED_PROGRAM_IDS = {"PCE", "V2", "P3", "P3_FRAME", "P4", "P7", "P7_SSRF", "T08"}
LIVE_TRUTH_SCHEMA = "motion-os.cgev2-live-truth-probe/v1"


def _paths(root: Path) -> dict[str, Path]:
    root = Path(root).resolve()
    return {name: root / rel for name, rel in RELATIVE_PATHS.items()}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _authority_anchor_payload(ctx: dict[str, Any]) -> dict[str, Any]:
    anchors = ctx["live_truth_anchor"]
    programs = sorted(ctx["active_programs"], key=lambda item: item["id"])
    return {
        "main_sha": anchors["main_sha"],
        "main_protected": anchors["main_protected"],
        "event_bus": {
            "issue": anchors["event_bus"]["issue"],
            "latest_comment_id_at_capture": anchors["event_bus"][
                "latest_comment_id_at_capture"
            ],
        },
        "promotion_barrier": {
            "issue": anchors["promotion_barrier"]["issue"],
            "state": anchors["promotion_barrier"]["state"],
            "release_event_observed": anchors["promotion_barrier"][
                "release_event_observed"
            ],
        },
        "active_program_heads": {
            item["id"]: {"pr": item.get("pr"), "head": item["head"]}
            for item in programs
        },
    }


def authority_anchor_fingerprint(ctx: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json_bytes(_authority_anchor_payload(ctx))).hexdigest()


def make_live_truth_probe(ctx: dict[str, Any]) -> dict[str, Any]:
    anchors = ctx["live_truth_anchor"]
    return {
        "schema": LIVE_TRUTH_SCHEMA,
        "main_sha": anchors["main_sha"],
        "main_protected": anchors["main_protected"],
        "event_bus_latest_comment_id": anchors["event_bus"][
            "latest_comment_id_at_capture"
        ],
        "promotion_barrier_state": anchors["promotion_barrier"]["state"],
        "promotion_release_event_observed": anchors["promotion_barrier"][
            "release_event_observed"
        ],
        "program_heads": {
            item["id"]: item["head"] for item in ctx["active_programs"]
        },
    }


def validate_live_truth(ctx: dict[str, Any], live: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if live.get("schema") != LIVE_TRUTH_SCHEMA:
        errors.append("live_truth_schema_invalid")
        return errors

    expected = make_live_truth_probe(ctx)
    scalar_fields = (
        "main_sha",
        "main_protected",
        "event_bus_latest_comment_id",
        "promotion_barrier_state",
        "promotion_release_event_observed",
    )
    for field in scalar_fields:
        if live.get(field) != expected[field]:
            errors.append(f"stale:{field}")

    heads = live.get("program_heads")
    if not isinstance(heads, dict):
        errors.append("live_truth_program_heads_missing")
        return errors

    for program_id, expected_head in expected["program_heads"].items():
        if program_id not in heads:
            errors.append(f"live_truth_program_head_missing:{program_id}")
        elif heads[program_id] != expected_head:
            errors.append(f"stale:program_head:{program_id}")

    return errors


def _validate_protocol(ctx: dict[str, Any], errors: list[str]) -> None:
    protocol = ctx.get("protocol_resolution", {})
    for section, expected_fields in EXPECTED_PROTOCOL.items():
        actual = protocol.get(section)
        if not isinstance(actual, dict):
            errors.append(f"protocol_section_missing:{section}")
            continue
        for field, expected in expected_fields.items():
            if actual.get(field) != expected:
                errors.append(f"protocol_mismatch:{section}.{field}")

    if protocol.get("composition") != EXPECTED_COMPOSITION:
        errors.append("protocol_composition_mismatch")
    if protocol.get("resolution_failure_state") != EXPECTED_RESOLUTION_FAILURE:
        errors.append("protocol_failure_state_mismatch")


def _validate_packet_manifest(root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    if manifest.get("schema") != "motion-os.cgev2-death-resilience-packet-manifest/v1":
        errors.append("packet_manifest_schema_invalid")
        return
    if manifest.get("digest_mode") != "git_blob_sha1+sha256_manifest":
        errors.append("packet_manifest_digest_mode_invalid")

    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        errors.append("packet_manifest_files_missing")
        return

    actual_files: dict[str, str] = {}
    for rel, expected_sha in sorted(files.items()):
        path = root / rel
        if not path.exists():
            errors.append(f"packet_manifest_missing_file:{rel}")
            continue
        actual_sha = _git_blob_sha1(path)
        actual_files[rel] = actual_sha
        if actual_sha != expected_sha:
            errors.append(f"packet_manifest_blob_mismatch:{rel}")

    expected_fingerprint = manifest.get("files_fingerprint_sha256", "")
    actual_fingerprint = hashlib.sha256(_canonical_json_bytes(files)).hexdigest()
    if not SHA64.fullmatch(str(expected_fingerprint)) or actual_fingerprint != expected_fingerprint:
        errors.append("packet_manifest_fingerprint_mismatch")


def validate_packet(
    root: Path = ROOT,
    *,
    live_truth: dict[str, Any] | None = None,
    require_live: bool = False,
) -> list[str]:
    root = Path(root).resolve()
    paths = _paths(root)
    errors: list[str] = []

    for name, path in paths.items():
        if not path.exists():
            errors.append(f"missing:{RELATIVE_PATHS[name]}")
    if errors:
        return errors

    ctx = _load(paths["context"])
    graph = _load(paths["graph"])
    drive = _load(paths["drive_mirror"])
    manifest = _load(paths["manifest"])

    if ctx.get("schema") != "motion-os.cgev2-death-resilience-contextpack/v3":
        errors.append("context_schema_invalid")
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
    event_bus = anchors.get("event_bus", {})
    if event_bus.get("issue") != 39 or not isinstance(
        event_bus.get("latest_comment_id_at_capture"), int
    ):
        errors.append("event_bus_anchor_invalid")
    barrier = anchors.get("promotion_barrier", {})
    if (
        barrier.get("issue") != 48
        or barrier.get("state") != "OPEN"
        or barrier.get("release_event_observed") is not False
    ):
        errors.append("barrier_capture_must_fail_closed")

    expected_fingerprint = ctx.get("authority_anchor_fingerprint_sha256", "")
    actual_fingerprint = authority_anchor_fingerprint(ctx)
    if (
        not SHA64.fullmatch(str(expected_fingerprint))
        or actual_fingerprint != expected_fingerprint
    ):
        errors.append("authority_anchor_fingerprint_mismatch")
    if "snapshot_fingerprint_sha256" in ctx:
        errors.append("legacy_snapshot_fingerprint_name_forbidden")

    _validate_protocol(ctx, errors)

    programs = ctx.get("active_programs", [])
    ids = [p.get("id") for p in programs]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_active_program_id")
    if not REQUIRED_PROGRAM_IDS.issubset(set(ids)):
        missing = sorted(REQUIRED_PROGRAM_IDS - set(ids))
        errors.append(f"active_programs_missing:{','.join(missing)}")
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

    critical_path = ctx.get("critical_path", [])
    orders = [item.get("order") for item in critical_path]
    if orders != list(range(1, len(critical_path) + 1)):
        errors.append("critical_path_order_invalid")

    recovery = ctx.get("zero_context_recovery", {})
    if recovery.get("entry_rule") != "DO_NOT_START_BY_TRUSTING_THIS_SNAPSHOT":
        errors.append("recovery_entry_must_reject_snapshot_authority")
    if len(recovery.get("steps", [])) < 10:
        errors.append("recovery_steps_incomplete")
    required_invalidation = {
        "main_sha changed",
        "Issue39 watermark changed",
        "Issue48/barrier state changed",
        "owned PR head changed",
    }
    if not required_invalidation.issubset(
        set(recovery.get("staleness_invalidation", []))
    ):
        errors.append("staleness_invalidation_incomplete")

    probe_contract = ctx.get("live_truth_probe", {})
    if (
        probe_contract.get("schema") != LIVE_TRUTH_SCHEMA
        or probe_contract.get("required_before_mutation") is not True
    ):
        errors.append("live_truth_probe_contract_invalid")

    own = set(ctx.get("own_write_scopes", []))
    foreign = set(ctx.get("foreign_owned_paths", []))
    if own & foreign:
        errors.append("write_scope_collision_with_foreign_owner")

    if graph.get("schema") != "motion-os.cgev2-death-resilience-graph/v2":
        errors.append("graph_schema_invalid")
    if graph.get("graph_authority") != "DERIVED_PROJECTION_NO_REVERSE_WRITES":
        errors.append("graph_must_be_derived")
    nodes = graph.get("nodes", [])
    node_ids = [node.get("id") for node in nodes]
    if len(node_ids) != len(set(node_ids)):
        errors.append("duplicate_graph_node")
    known = set(node_ids)
    required_graph_nodes = {
        "gate:p4-real-provider",
        "scope:t08-reverse-engineering",
        "scope:p7-security",
        "pr:122",
    }
    if not required_graph_nodes.issubset(known):
        errors.append("graph_explicit_gate_or_scope_missing")
    for edge in graph.get("edges", []):
        source = edge.get("source")
        target = edge.get("target")
        edge_type = edge.get("type")
        if source not in known or target not in known:
            errors.append(f"dangling_edge:{edge}")
        if edge_type == "OWNS_SEMANTIC_SCOPE" and target == "project:motion-os":
            errors.append("graph_ownership_must_target_explicit_scope")
        if str(source).startswith("block:") and str(target).startswith("pr:"):
            errors.append("graph_external_blocker_must_target_gate_not_pr")

    if not any(
        e.get("source") == "block:provider"
        and e.get("type") == "BLOCKS"
        and e.get("target") == "gate:p4-real-provider"
        for e in graph.get("edges", [])
    ):
        errors.append("graph_provider_gate_binding_missing")

    if drive.get("authority") != "DURABLE_RECOVERY_MIRROR_NOT_PROJECT_TRUTH":
        errors.append("drive_mirror_authority_invalid")
    if drive.get("project_done") is not False:
        errors.append("drive_mirror_must_not_claim_done")
    drive_meta = drive.get("google_drive", {})
    if drive_meta.get("upload_status") != "SUCCEEDED":
        errors.append("drive_mirror_upload_not_succeeded")
    if not str(drive_meta.get("destination_path", "")).startswith(
        "/Google Drive/00_AGENT_HANDOFF/"
    ):
        errors.append("drive_mirror_not_in_canonical_handoff_folder")
    if drive_meta.get("directory_id") != (
        "external-gdrive:folder:1EeF_juiXk8rmMrUHhN0HBPy1m2NhDOyb"
    ):
        errors.append("drive_mirror_directory_id_mismatch")
    if not SHA64.fullmatch(str(drive_meta.get("content_sha256", ""))):
        errors.append("drive_mirror_content_sha256_missing")
    if not isinstance(drive_meta.get("content_bytes"), int) or drive_meta.get(
        "content_bytes", 0
    ) <= 0:
        errors.append("drive_mirror_content_size_missing")
    if drive.get("source_authority_anchor_fingerprint_sha256") != expected_fingerprint:
        errors.append("drive_mirror_anchor_binding_mismatch")

    _validate_packet_manifest(root, manifest, errors)

    continuity = paths["continuity"].read_text(encoding="utf-8")
    if "VERIFY LIVE TRUTH BEFORE EXECUTION" not in continuity:
        errors.append("continuity_pointer_missing_live_truth_gate")
    if PROJECT_DONE_TRUE.search(continuity):
        errors.append("continuity_pointer_must_not_claim_done")
    if re.search(r"current main[^\n]*[0-9a-f]{40}", continuity, flags=re.I):
        errors.append("continuity_pointer_must_not_pin_volatile_main")

    next_text = paths["next"].read_text(encoding="utf-8")
    if "/CGEV2" not in next_text or "/PROJECT-COMPLETION-ENGINE" not in next_text:
        errors.append("successor_protocol_sequence_missing")
    if "VERIFY LIVE TRUTH BEFORE EXECUTION" not in next_text:
        errors.append("successor_missing_live_truth_gate")
    if "--require-live" not in next_text or LIVE_TRUTH_SCHEMA not in next_text:
        errors.append("successor_missing_executable_staleness_gate")

    if live_truth is not None:
        errors.extend(validate_live_truth(ctx, live_truth))
    elif require_live:
        errors.append("live_truth_required_before_mutation")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the non-authoritative CGEV2 death-resilience packet."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--live-truth", type=Path)
    parser.add_argument("--require-live", action="store_true")
    args = parser.parse_args()

    live_truth = _load(args.live_truth) if args.live_truth else None
    errors = validate_packet(
        args.root, live_truth=live_truth, require_live=args.require_live
    )
    payload = {
        "schema": "motion-os.cgev2-death-resilience-verifier/v2",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
