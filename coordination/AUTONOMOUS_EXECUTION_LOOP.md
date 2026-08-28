# MOTION.OS — Autonomous Execution Loop v1

## Purpose
Remove the human reload bottleneck without removing authority boundaries. Every material wave must end by making the next wave executable from persisted state alone.

## External clock vs internal truth
The loop has two layers:

1. **External clock** — a recurring agent invocation periodically re-enters the repository.
2. **Repo-native metaprogram** — live truth reconstruction + deterministic next-wave compilation decides whether to EXECUTE or BLOCK.

The external clock is never authority. GitHub live lifecycle, canonical event semantics, repo state, evidence and deterministic projections remain authority.

## Canonical loop

```text
WAKE
  ↓
RECONSTRUCT LIVE TRUTH
  ↓
CREATE UNIQUE SESSION
  ↓
READ EVENT WATERMARK + ACTIVE CLAIMS
  ↓
INVALIDATE STALE CONTEXT
  ↓
BUILD CANDIDATE TASK SET
  ↓
NEXT-WAVE COMPILER
  ├─ BLOCKED → persist blocker + stop this tick
  └─ EXECUTE
       ↓
     WORK_STARTED
       ↓
     CLAIM SCOPES
       ↓
     IMPLEMENT
       ↓
     LOCAL TEST
       ↓
     ADVERSARIAL TEST
       ↓
     CODE REVIEW
       ↓
     SECURITY REVIEW
       ↓
     CLEAN-RUNNER EVIDENCE WHEN WARRANTED
       ↓
     CHECKPOINT / HANDOFF / RELEASE SCOPES
       ↓
     RECONSTRUCT LIVE TRUTH AGAIN
       ↓
     COMPILE NEXT WAVE
```

## Critical anti-cascade rule
A `next-wave` packet is a proposal for the current reconstructed state only. It MUST NOT be blindly chained into the next invocation. Every wake begins with fresh GitHub/event/state reconstruction. If `main`, event watermark, claims, dependencies or evidence changed, the prior packet is invalid.

## Candidate generation
Candidates should come from current unresolved P0/P1/P2 work, escaped bugs, broken E2E paths, Issue #48 while open, current TASKS/state, PR review findings, CI failures and empirical qualification gaps.

Candidates MUST declare:
- task_id
- priority
- title
- scopes
- status
- dependencies_satisfied
- blocked_external
- irreversible
- north-star/risk metrics
- local verification profiles
- adversarial tests

## Selection
`scripts/next_wave.py` deterministically selects the highest-value eligible candidate using `config/autoloop_policy.json`.

Hard exclusions precede scoring:
- stale ContextPack/main SHA
- authority reconstruction failure
- event-semantic divergence
- hard security blocker
- unresolved WRITE/EXCLUSIVE_WRITE overlap
- unsatisfied dependencies
- external blocker
- irreversible action under an active promotion barrier

If nothing is safe, output `BLOCKED`. Never invent low-value work just to keep the loop busy.

## Human role
The human is removed from routine continuation, not from governance. Human input is only required when a genuine authority boundary demands it: credentials, irreversible external spend, legal/brand decision, inaccessible artifact, unavailable provider, or explicit barrier release.

## Infrastructure rule
The loop itself does not justify Postgres/Redis/Kafka/Kubernetes. The repository/event fabric remains sufficient until measured multi-host contention or other documented promotion trigger appears.

## Definition of Done for each wave
A wave is closed only when persisted state includes:
- unique session/workstream/correlation IDs
- live/base/main SHA
- branch/PR/head SHA when applicable
- scopes touched and released
- exact test outcomes
- code-review findings
- security findings
- authority state
- blockers/degraded external dependencies
- evidence refs
- next safe action

Then the next invocation reconstructs state and compiles again.
