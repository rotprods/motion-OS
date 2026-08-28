from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class NextWaveError(ValueError):
    pass


PRIORITY_WEIGHT = {"P0": 1000, "P1": 700, "P2": 400, "P3": 100}
ALLOWED_STATUSES = {"PROPOSED", "IMPLEMENTED", "EXECUTED", "VERIFIED"}
ALLOWED_CLAIM_MODES = {"READ", "WRITE", "EXCLUSIVE_WRITE"}
SEMANTIC_SCOPE_KINDS = {
    "contract", "schema", "phase", "capability", "evidence", "resource", "plan",
    "issue", "pr", "artifact", "task", "architecture", "adr", "root-cause", "authority",
}
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
SAFE_BRANCH_COMPONENT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")


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


def _strict_bool(raw: Any, field: str) -> bool:
    if type(raw) is not bool:
        raise NextWaveError(f"{field} must be a JSON boolean")
    return raw


def _finite_number(raw: Any, field: str) -> float:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise NextWaveError(f"{field} must be numeric")
    value = float(raw)
    if not math.isfinite(value):
        raise NextWaveError(f"{field} must be finite")
    return value


def _require_sha1(raw: Any, field: str) -> str:
    value = str(raw)
    if not SHA1_RE.fullmatch(value):
        raise NextWaveError(f"{field} must be a lowercase 40-char git SHA")
    return value


def _require_sha256(raw: Any, field: str) -> str:
    value = str(raw)
    if not SHA256_RE.fullmatch(value):
        raise NextWaveError(f"{field} must be a lowercase sha256")
    return value


def _require_nonempty_id(raw: Any, field: str) -> str:
    value = str(raw).strip()
    if not value or not SAFE_ID_RE.fullmatch(value):
        raise NextWaveError(f"{field} is missing or unsafe")
    return value


def _scope_parts(scope: str) -> tuple[str, str]:
    if ":" not in scope:
        raise NextWaveError(f"invalid resource scope: {scope}")
    kind, value = scope.split(":", 1)
    kind = kind.strip().lower()
    value = value.strip()
    if not kind or not value:
        raise NextWaveError(f"invalid resource scope: {scope}")
    if kind in {"file", "tree"}:
        normalized = value.replace("\\", "/").lstrip("/")
        if kind == "tree":
            normalized = normalized.removesuffix("/**").removesuffix("/*").rstrip("/")
        if not normalized or normalized == ".." or normalized.startswith("../") or "/../" in normalized:
            raise NextWaveError(f"unsafe repository scope: {scope}")
        return kind, normalized
    if kind not in SEMANTIC_SCOPE_KINDS:
        raise NextWaveError(f"unsupported resource scope kind: {kind}")
    if not re.fullmatch(r"[A-Za-z0-9._/@+-]+", value):
        raise NextWaveError(f"unsafe semantic resource scope: {scope}")
    return kind, value


def scopes_overlap(a: str, b: str) -> bool:
    ka, va = _scope_parts(a)
    kb, vb = _scope_parts(b)
    if ka == kb and va == vb:
        return True
    if {ka, kb} == {"file", "tree"}:
        file_value = va if ka == "file" else vb
        tree_value = va if ka == "tree" else vb
        return file_value == tree_value or file_value.startswith(tree_value + "/")
    if ka == kb == "tree":
        return va == vb or va.startswith(vb + "/") or vb.startswith(va + "/")
    return False


def _claim_from_dict(raw: dict[str, Any]) -> Claim:
    scope = str(raw.get("scope", ""))
    _scope_parts(scope)
    mode = str(raw.get("mode", ""))
    if mode not in ALLOWED_CLAIM_MODES:
        raise NextWaveError(f"unsupported claim mode: {mode}")
    owner_session = _require_nonempty_id(raw.get("owner_session"), "owner_session")
    return Claim(scope=scope, mode=mode, owner_session=owner_session)


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


def _candidate_from_dict(raw: dict[str, Any], policy: dict[str, Any]) -> Candidate:
    task_id = _require_nonempty_id(raw.get("task_id"), "task_id")
    priority = str(raw.get("priority", ""))
    if priority not in PRIORITY_WEIGHT:
        raise NextWaveError(f"unsupported priority: {priority}")
    status = str(raw.get("status", "PROPOSED"))
    if status not in ALLOWED_STATUSES:
        raise NextWaveError(f"non-actionable or unsupported candidate status: {status}")

    scopes = tuple(str(v) for v in raw.get("scopes", ()))
    if not scopes:
        raise NextWaveError("candidate must declare at least one resource scope")
    for scope in scopes:
        _scope_parts(scope)

    metrics_raw = raw.get("metrics", {})
    if not isinstance(metrics_raw, dict):
        raise NextWaveError("metrics must be an object")
    metrics = {str(k): _finite_number(v, f"metrics.{k}") for k, v in metrics_raw.items()}

    allowed_profiles = set(policy.get("local_first_profiles", ()))
    local_profiles = tuple(str(v) for v in raw.get("local_profiles", ("quick",)))
    if not local_profiles or any(profile not in allowed_profiles for profile in local_profiles):
        raise NextWaveError("candidate contains unsupported local verification profile")

    adversarial_tests = tuple(str(v).strip() for v in raw.get("adversarial_tests", ()))
    if any(not value for value in adversarial_tests):
        raise NextWaveError("adversarial test names must be non-empty")

    return Candidate(
        task_id=task_id,
        priority=priority,
        title=str(raw.get("title", task_id)).strip() or task_id,
        scopes=scopes,
        status=status,
        dependencies_satisfied=_strict_bool(raw.get("dependencies_satisfied", False), "dependencies_satisfied"),
        blocked_external=_strict_bool(raw.get("blocked_external", False), "blocked_external"),
        irreversible=_strict_bool(raw.get("irreversible", False), "irreversible"),
        metrics=metrics,
        local_profiles=local_profiles,
        adversarial_tests=adversarial_tests,
    )


def _validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema") != "motion-os.autoloop-policy/v1":
        raise NextWaveError("unsupported autoloop policy schema")
    weights = policy.get("score_weights")
    if not isinstance(weights, dict) or not weights:
        raise NextWaveError("score_weights must be a non-empty object")
    for key, value in weights.items():
        _finite_number(value, f"score_weights.{key}")


def _score(candidate: Candidate, policy: dict[str, Any], contention_count: int) -> float:
    score = float(PRIORITY_WEIGHT[candidate.priority])
    for key, weight in policy["score_weights"].items():
        if key == "scope_contention":
            score += float(weight) * contention_count
        else:
            score += float(weight) * float(candidate.metrics.get(key, 0.0))
    if not math.isfinite(score):
        raise NextWaveError("candidate score became non-finite")
    return round(score, 4)


def _safe_branch_slug(task_id: str) -> str:
    slug = task_id.lower().replace("/", "-").replace("_", "-")
    slug = re.sub(r"[^a-z0-9._-]+", "-", slug).strip(".-")
    slug = re.sub(r"-{2,}", "-", slug)[:80].rstrip(".-")
    if not slug or not SAFE_BRANCH_COMPONENT_RE.fullmatch(slug):
        raise NextWaveError("task_id cannot be converted to a safe branch component")
    return slug


def _blocked(reason: str, **extra: Any) -> dict[str, Any]:
    result = {"schema": "motion-os.next-wave/v1", "decision": "BLOCKED", "reason": reason}
    result.update(extra)
    return result


def compile_next_wave(state: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    _validate_policy(policy)
    required = (
        "live_main_sha", "context_main_sha", "live_event_watermark", "context_event_watermark",
        "session_id", "workstream_seed", "candidates", "context_projection_hash",
        "event_fabric_snapshot_hash", "canonical_event_fabric_ready",
    )
    missing = [key for key in required if key not in state]
    if missing:
        raise NextWaveError(f"missing state fields: {missing}")

    live_sha = _require_sha1(state["live_main_sha"], "live_main_sha")
    context_sha = _require_sha1(state["context_main_sha"], "context_main_sha")
    context_projection_hash = _require_sha256(state["context_projection_hash"], "context_projection_hash")
    event_fabric_snapshot_hash = _require_sha256(state["event_fabric_snapshot_hash"], "event_fabric_snapshot_hash")
    session_id = _require_nonempty_id(state["session_id"], "session_id")
    workstream_seed = _require_nonempty_id(state["workstream_seed"], "workstream_seed")

    live_watermark = state["live_event_watermark"]
    context_watermark = state["context_event_watermark"]
    if isinstance(live_watermark, bool) or not isinstance(live_watermark, int) or live_watermark < 0:
        raise NextWaveError("live_event_watermark must be a non-negative integer")
    if isinstance(context_watermark, bool) or not isinstance(context_watermark, int) or context_watermark < 0:
        raise NextWaveError("context_event_watermark must be a non-negative integer")

    if live_sha != context_sha:
        return _blocked(
            "STALE_CONTEXT_MAIN_SHA",
            live_main_sha=live_sha,
            context_main_sha=context_sha,
            next_action="reconstruct live truth and compile a fresh ContextPack before any mutation",
        )
    if live_watermark != context_watermark:
        return _blocked(
            "STALE_CONTEXT_EVENT_WATERMARK",
            live_event_watermark=live_watermark,
            context_event_watermark=context_watermark,
            next_action="reconstruct canonical Event Fabric snapshot before any mutation",
        )

    if not _strict_bool(state["canonical_event_fabric_ready"], "canonical_event_fabric_ready"):
        return _blocked("CANONICAL_EVENT_FABRIC_NOT_READY")
    if state.get("event_fabric_contract_version") != "motion-os.event-fabric/v3":
        return _blocked("EVENT_FABRIC_CONTRACT_UNQUALIFIED")

    authority_reconstructed = _strict_bool(state.get("authority_reconstructed", False), "authority_reconstructed")
    event_semantic_divergence = _strict_bool(state.get("event_semantic_divergence", False), "event_semantic_divergence")
    hard_security_blocker = _strict_bool(state.get("hard_security_blocker", False), "hard_security_blocker")
    barrier = _strict_bool(state.get("promotion_barrier_active", False), "promotion_barrier_active")

    if not authority_reconstructed:
        return _blocked("AUTHORITY_NOT_RECONSTRUCTED")
    if event_semantic_divergence:
        return _blocked("EVENT_SEMANTIC_DIVERGENCE")
    if hard_security_blocker:
        return _blocked("HARD_SECURITY_BLOCKER")

    claims_raw = state.get("active_claims", ())
    if not isinstance(claims_raw, (list, tuple)):
        raise NextWaveError("active_claims must be an array")
    claims = tuple(_claim_from_dict(c) for c in claims_raw)

    candidates_raw = state["candidates"]
    if not isinstance(candidates_raw, list):
        raise NextWaveError("candidates must be an array")
    evaluated: list[dict[str, Any]] = []
    for raw in candidates_raw:
        if not isinstance(raw, dict):
            raise NextWaveError("candidate entries must be objects")
        candidate = _candidate_from_dict(raw, policy)
        reasons: list[str] = []
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
        return _blocked(
            "NO_SAFE_HIGH_VALUE_TASK",
            blockers=blockers,
            next_action="reconstruct live state on next tick; do not invent work",
        )

    eligible.sort(key=lambda item: (-item["score"], item["candidate"].task_id))
    chosen = eligible[0]
    candidate: Candidate = chosen["candidate"]
    branch = f"autoloop/{_safe_branch_slug(workstream_seed)}/{_safe_branch_slug(candidate.task_id)}"
    return {
        "schema": "motion-os.next-wave/v1",
        "decision": "EXECUTE",
        "authority_binding": {
            "main_sha": live_sha,
            "event_watermark": live_watermark,
            "context_projection_hash": context_projection_hash,
            "event_fabric_snapshot_hash": event_fabric_snapshot_hash,
            "event_fabric_contract_version": "motion-os.event-fabric/v3",
        },
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
            "VERIFY_AUTHORITY_BINDING",
            "EMIT_WORK_STARTED",
            "CLAIM_SCOPES",
            "IMPLEMENT",
            "LOCAL_TEST",
            "ADVERSARIAL_TEST",
            "CODE_REVIEW",
            "SECURITY_REVIEW",
            "CHECKPOINT",
            "RECONCILE_LIVE_STATE",
            "COMPILE_NEXT_WAVE",
        ],
        "closure_requirements": {
            "emit_handoff": True,
            "release_scopes": True,
            "persist_exact_test_outcomes": True,
            "recompute_next_wave_from_live_truth": True,
            "never_chain_stale_packet": True,
        },
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
