from __future__ import annotations

import json
from pathlib import Path
import shutil

from scripts.verify_cgev2_death_resilience import (
    RELATIVE_PATHS,
    make_live_truth_probe,
    validate_live_truth,
    validate_packet,
)


ROOT = Path(__file__).resolve().parents[1]


def _copy_packet(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for rel in RELATIVE_PATHS.values():
        src = ROOT / rel
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return root


def _load(root: Path, key: str) -> dict:
    return json.loads((root / RELATIVE_PATHS[key]).read_text(encoding="utf-8"))


def _write(root: Path, key: str, value: dict) -> None:
    (root / RELATIVE_PATHS[key]).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def test_cgev2_packet_static_contract_passes() -> None:
    assert validate_packet() == []


def test_validate_packet_honors_supplied_root(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    assert validate_packet(root) == []


def test_missing_file_in_isolated_root_fails_closed(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    (root / RELATIVE_PATHS["graph"]).unlink()
    assert f"missing:{RELATIVE_PATHS['graph']}" in validate_packet(root)


def test_context_false_release_claim_is_rejected(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    ctx = _load(root, "context")
    ctx["project"]["release_status"] = "READY"
    _write(root, "context", ctx)
    errors = validate_packet(root)
    assert "snapshot_release_must_remain_blocked" in errors
    assert f"packet_manifest_blob_mismatch:{RELATIVE_PATHS['context']}" in errors


def test_packet_manifest_detects_successor_doc_mutation(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    path = root / RELATIVE_PATHS["next"]
    path.write_text(path.read_text(encoding="utf-8") + "\nTAMPER\n", encoding="utf-8")
    errors = validate_packet(root)
    assert f"packet_manifest_blob_mismatch:{RELATIVE_PATHS['next']}" in errors


def test_protocol_exact_sha_and_identity_are_executable_invariants(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    ctx = _load(root, "context")
    ctx["protocol_resolution"]["cgev2"]["exact_sha"] = "0" * 40
    _write(root, "context", ctx)
    errors = validate_packet(root)
    assert "protocol_mismatch:cgev2.exact_sha" in errors


def test_active_p7_ssrf_stack_is_required(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    ctx = _load(root, "context")
    ctx["active_programs"] = [
        item for item in ctx["active_programs"] if item["id"] != "P7_SSRF"
    ]
    _write(root, "context", ctx)
    errors = validate_packet(root)
    assert "active_programs_missing:P7_SSRF" in errors
    assert "authority_anchor_fingerprint_mismatch" in errors


def test_missing_external_blocker_fails_closed(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    ctx = _load(root, "context")
    ctx["external_blockers"] = []
    _write(root, "context", ctx)
    assert "external_blockers_missing" in validate_packet(root)


def test_duplicate_active_program_id_fails_closed(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    ctx = _load(root, "context")
    ctx["active_programs"].append(dict(ctx["active_programs"][0]))
    _write(root, "context", ctx)
    assert "duplicate_active_program_id" in validate_packet(root)


def test_malformed_main_sha_fails_closed(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    ctx = _load(root, "context")
    ctx["live_truth_anchor"]["main_sha"] = "not-a-sha"
    _write(root, "context", ctx)
    assert "invalid_main_sha" in validate_packet(root)


def test_false_project_done_fails_closed(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    ctx = _load(root, "context")
    ctx["project"]["project_done"] = True
    _write(root, "context", ctx)
    assert "snapshot_must_not_claim_project_done" in validate_packet(root)


def test_self_promoted_snapshot_authority_fails_closed(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    ctx = _load(root, "context")
    ctx["snapshot_authority"] = "CANONICAL_PROJECT_TRUTH"
    _write(root, "context", ctx)
    assert "snapshot_authority_must_be_derived" in validate_packet(root)


def test_missing_next_safe_action_fails_closed(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    ctx = _load(root, "context")
    ctx["next_safe_frontier"] = []
    _write(root, "context", ctx)
    assert "next_safe_frontier_missing" in validate_packet(root)


def test_graph_ownership_must_target_explicit_scope(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    graph = _load(root, "graph")
    for edge in graph["edges"]:
        if edge.get("source") == "pr:126" and edge.get("type") == "OWNS_SEMANTIC_SCOPE":
            edge["target"] = "project:motion-os"
            break
    _write(root, "graph", graph)
    errors = validate_packet(root)
    assert "graph_ownership_must_target_explicit_scope" in errors


def test_external_blocker_must_target_authority_gate_not_pr(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    graph = _load(root, "graph")
    graph["edges"].append(
        {"source": "block:provider", "type": "BLOCKS", "target": "pr:119"}
    )
    _write(root, "graph", graph)
    errors = validate_packet(root)
    assert "graph_external_blocker_must_target_gate_not_pr" in errors


def test_drive_mirror_must_live_in_canonical_handoff_folder(tmp_path: Path) -> None:
    root = _copy_packet(tmp_path)
    drive = _load(root, "drive_mirror")
    drive["google_drive"]["destination_path"] = (
        "/Google Drive/08_INFRA_BACKUPS_EXPORTS/handoff.md"
    )
    _write(root, "drive_mirror", drive)
    errors = validate_packet(root)
    assert "drive_mirror_not_in_canonical_handoff_folder" in errors


def test_live_truth_probe_accepts_exact_snapshot() -> None:
    ctx = json.loads((ROOT / RELATIVE_PATHS["context"]).read_text(encoding="utf-8"))
    live = make_live_truth_probe(ctx)
    assert validate_live_truth(ctx, live) == []
    assert validate_packet(live_truth=live, require_live=True) == []


def test_live_truth_main_drift_invalidates_before_mutation() -> None:
    ctx = json.loads((ROOT / RELATIVE_PATHS["context"]).read_text(encoding="utf-8"))
    live = make_live_truth_probe(ctx)
    live["main_sha"] = "0" * 40
    assert "stale:main_sha" in validate_live_truth(ctx, live)


def test_live_truth_event_watermark_drift_invalidates_before_mutation() -> None:
    ctx = json.loads((ROOT / RELATIVE_PATHS["context"]).read_text(encoding="utf-8"))
    live = make_live_truth_probe(ctx)
    live["event_bus_latest_comment_id"] += 1
    assert "stale:event_bus_latest_comment_id" in validate_live_truth(ctx, live)


def test_live_truth_barrier_drift_invalidates_before_mutation() -> None:
    ctx = json.loads((ROOT / RELATIVE_PATHS["context"]).read_text(encoding="utf-8"))
    live = make_live_truth_probe(ctx)
    live["promotion_barrier_state"] = "CLOSED"
    assert "stale:promotion_barrier_state" in validate_live_truth(ctx, live)


def test_live_truth_program_head_drift_invalidates_before_mutation() -> None:
    ctx = json.loads((ROOT / RELATIVE_PATHS["context"]).read_text(encoding="utf-8"))
    live = make_live_truth_probe(ctx)
    live["program_heads"]["P7_SSRF"] = "f" * 40
    assert "stale:program_head:P7_SSRF" in validate_live_truth(ctx, live)


def test_missing_live_truth_is_a_fail_closed_mutation_gate() -> None:
    assert "live_truth_required_before_mutation" in validate_packet(require_live=True)
