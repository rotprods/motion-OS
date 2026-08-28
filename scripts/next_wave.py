from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class NextWaveError(ValueError):
    pass


PRIORITY_WEIGHT = {"P0": 1000, "P1": 700, "P2": 400, "P3": 100}


@dataclass(frozen=True)
class Claim:
    scope: str
    mode: str
    owner_session: str


@dataclass(frozen=True)
class Candidate:
    task_id: str
    priority: str
    title: str
    scopes: tuple[str, ...]
    status: str
    dependencies_satisfied: bool
    blocked_external: bool
    irreversible: bool
    metrics: dict[str, float]
    local_profiles: tuple[str, ...]
    adversarial_tests: tuple[str, ...]


def _scope_parts(scope: str) -> tuple[str, str]:
    if ":" not in scope:
        raise NextWaveError(f"invalid resource scope: {scope}")
    kind, value = scope.split(":", 1)
    if not kind or not value:
        raise NextWaveError(f"invalid resource scope: {scope}")
    return kind, value


def scopes_overlap(a: str, b: str) -> bool:
    ka, va = _scope_parts(a)
    kb, vb = _scope_parts(b)
    if ka == kb and va == vb:
        return True
    if {ka, kb} == {"file", "tree"}:
        file_value = va if ka == "file" else vb
        tree_value = va if ka == "tree" else vb
        tree_prefix = tree_value.rstrip("*/")
        return file_value == tree_prefix or file_value.startswith(tree_prefix + "/")
    if ka == kb == "tree":
        pa = va.rstrip("*/")
        pb = vb.rstrip("*/")
        return pa == pb or pa.startswith(pb + "/") or pb.startswith(pa + "/")
    return False


def conflicting_claims(candidate: Candidate, claims: tuple[Claim, ...], session_id: str) -> tuple[Claim, ...]:
    conflicts: list[Claim] = []
    for claim in claims:
        if claim.owner_session == session_id:
            continue
        if claim.mode not in {"WRITE", "EXCLUSIVE_WRITE"}:
            continue
        if any(scopes_overlap(scope, claim.scope) for scope in candidate.scopes):
            conflicts.append(claim)
    return tuple(conflicts)


def _candidate_from_dict(raw: dict[str, Any]) -> Candidate:
    priority = str(raw.get("priority", ""))
    if priority not in PRIORITY_WEIGHT:
        raise NextWaveError(f"unsupported priority: {priority}")
    metrics = {str(k): float(v) for k, v in dict(raw.get("metrics", {})).items()}
    return Candidate(
        task_id=str(raw["task_id"]),
        priority=priority,
        title=str(raw.get("title", raw["task_id"])),
        scopes=tuple(str(v) for v in raw.get("scopes", ())),
        status=str(raw.get("status", "PROPOSED")),
        dependencies_satisfied=bool(raw.get("dependencies_satisfied", False)),
        blocked_external=bool(raw.get("blocked_external", False)),
        irreversible=bool(raw.get("irreversible", False)),
        metrics=metrics,
        local_profiles=tuple(str(v) for v in raw.get("local_profiles", ("quick",))),
        adversarial_tests=tuple(str(v) for v in raw.get("adversarial_tests", ())),
    )


def _score(candidate: Candidate, policy: dict[str, Any], contention_count: int) -> float:
    score = float(PRIORITY_WEIGHT[candidate.priority])
    weights = policy["score_weights"]
    for key, weight in weights.items():
        if key == "scope_contention":
            score += float(weight) * contention_count
        else:
            score += float(weight) * float(candidate.metrics.get(key, 0.0))
    return round(score, 4)


def compile_next_wave(state: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    required = ("live_main_sha", "context_main_sha", "session_id", "workstream_seed", "candidates")
    missing = [key for key in required if key not in state]
    if missing:
        raise NextWaveError(f"missing state fields: {missing}")

    live_sha = str(state["live_main_sha"])
    context_sha = str(state["context_main_sha"])
    if live_sha != context_sha:
        return {
            "schema": "motion-os.next-wave/v1",
            "decision": "BLOCKED",
            "reason": "STALE_CONTEXT_MAIN_SHA",
            "live_main_sha": live_sha,
            "context_main_sha": context_sha,
            "next_action": "reconstruct live truth and compile a fresh ContextPack before any mutation"
        }
    if not bool(state.get("authority_reconstructed", False)):
        return {"schema": "motion-os.next-wave/v1", "decision": "BLOCKED", "reason": "AUTHORITY_NOT_RECONSTRUCTED"}
    if bool(state.get("event_semantic_divergence", False)):
        return {"schema": "motion-os.next-wave/v1", "decision": "BLOCKED", "reason": "EVENT_SEMANTIC_DIVERGENCE"}
    if bool(state.get("hard_security_blocker", False)):
        return {"schema": "motion-os.next-wave/v1", "decision": "BLOCKED", "reason": "HARD_SECURITY_BLOCKER"}

    claims = tuple(Claim(str(c["scope"]), str(c["mode"]), str(c["owner_session"])) for c in state.get("active_claims", ()))
    session_id = str(state["session_id"])
    barrier = bool(state.get("promotion_barrier_active", False))
    evaluated: list[dict[str, Any]] = []

    for raw in state["candidates"]:
        candidate = _candidate_from_dict(raw)
        reasons: list[str] = []
        if candidate.status not in {"PROPOSED", "IMPLEMENTED", "EXECUTED", "BLOCKED"}:
            reasons.append("NON_ACTIONABLE_STATUS")
        if not candidate.dependencies_satisfied:
            reasons.append("DEPENDENCIES_UNSATISFIED")
        if candidate.blocked_external:
            reasons.append("EXTERNAL_BLOCKER")
        if barrier and candidate.irreversible:
            reasons.append("PROMOTION_BARRIER")
        conflicts = conflicting_claims(candidate, claims, session_id)
        if conflicts:
            reasons.append("SCOPE_CONFLICT")
        score = _score(candidate, policy, len(conflicts))
        evaluated.append({
            "candidate": candidate,
            "score": score,
            "eligible": not reasons,
            "reasons": reasons,
            "conflicts": [c.__dict__ for c in conflicts],
        })

    eligible = [item for item in evaluated if item["eligible"]]
    if not eligible:
        blockers = [
            {"task_id": item["candidate"].task_id, "reasons": item["reasons"]}
            for item in sorted(evaluated, key=lambda x: x["candidate"].task_id)
        ]
        return {
            "schema": "motion-os.next-wave/v1",
            "decision": "BLOCKED",
            "reason": "NO_SAFE_HIGH_VALUE_TASK",
            "blockers": blockers,
            "next_action": "reconstruct live state on next tick; do not invent work"
        }

    eligible.sort(key=lambda item: (-item["score"], item["candidate"].task_id))
    chosen = eligible[0]
    candidate: Candidate = chosen["candidate"]
    branch_slug = candidate.task_id.lower().replace("_", "-").replace("/", "-")
    branch = f"autoloop/{state['workstream_seed']}/{branch_slug}"
    return {
        "schema": "motion-os.next-wave/v1",
        "decision": "EXECUTE",
        "selected": {
            "task_id": candidate.task_id,
            "title": candidate.title,
            "priority": candidate.priority,
            "score": chosen["score"],
            "resource_scope": list(candidate.scopes),
            "branch": branch,
            "local_profiles": list(candidate.local_profiles),
            "adversarial_tests": list(candidate.adversarial_tests),
        },
        "execution_protocol": [
            "READ_LATEST_EVENT_WATERMARK",
            "RECONCILE_LIVE_GITHUB",
            "EMIT_WORK_STARTED",
            "CLAIM_SCOPES",
            "IMPLEMENT",
            "LOCAL_TEST",
            "ADVERSARIAL_TEST",
            "CODE_REVIEW",
            "SECURITY_REVIEW",
            "CHECKPOINT",
            "RECONCILE_LIVE_STATE",
            "COMPILE_NEXT_WAVE"
        ],
        "closure_requirements": {
            "emit_handoff": True,
            "release_scopes": True,
            "persist_exact_test_outcomes": True,
            "recompute_next_wave_from_live_truth": True,
            "never_chain_stale_packet": True
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile the highest-value safe next MOTION.OS execution wave")
    parser.add_argument("--state", required=True)
    parser.add_argument("--policy", default="config/autoloop_policy.json")
    parser.add_argument("--out")
    args = parser.parse_args()
    state = json.loads(Path(args.state).read_text(encoding="utf-8"))
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    result = compile_next_wave(state, policy)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["decision"] in {"EXECUTE", "BLOCKED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
