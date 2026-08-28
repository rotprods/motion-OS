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
     GAUNTLET OUTER VERIFICATION LOOP
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

## `/gauntlet-loop` semantics
The canonical MOTION.OS interpretation of `/gauntlet-loop` is an **outer verification loop** around the implementation/tool loop. This follows the same systems pattern documented by Context7 references such as Ralph Loop Agent and Loop Engineering: the implementer performs work, an independent verifier checks explicit completion criteria, and failed verification is returned as targeted feedback for the next repair iteration.

```text
INNER LOOP = implement / tool calls / tests / edits
OUTER LOOP = verify completion / reject / feedback / retry
```

A gauntlet iteration is:

```text
IMPLEMENT
  ↓
VERIFY AGAINST EXPLICIT STOP CONDITIONS
  ├─ PASS → close gauntlet
  └─ FAIL
       ↓
     emit exact failure reasons
       ↓
     classify ROOT CAUSE / INVARIANT / REGRESSION TEST / ADJACENT FAILURE FAMILY
       ↓
     choose a materially different safe repair
       ↓
     IMPLEMENT AGAIN
```

### Required verifier separation
The same generated claim is never accepted as its own proof. Verification must come from tests, measured evidence, independent deterministic checks, clean-runner CI, or a separately scoped verifier/reviewer. `code exists`, a self-authored summary, or a model saying “done” is not completion evidence.

### Mechanical stop conditions
Every wave must declare verifiable stop conditions before implementation. Typical stop conditions include:
- exact tests/gates required to pass;
- zero unresolved P0/P1 findings in the claimed scope;
- target artifact/hash/evidence produced;
- no active conflicting WRITE/EXCLUSIVE_WRITE claims;
- no stale main/context/event watermark;
- authority state at or above the declared target;
- explicit empirical threshold when the task is empirical rather than code-only.

### Attempt budget / stuck detection
The gauntlet must not become an infinite self-repair loop.
- default maximum: 3 materially distinct repair attempts for the same root failure in one wave;
- repeated failure signature or repeated near-identical patch → classify `STUCK_LOOP` and BLOCK/escalate;
- changing tests solely to make a regression disappear is forbidden unless the test itself is proven incorrect;
- if the task requires unavailable external authority, stop as `BLOCKED` or `DEGRADED_EXTERNAL`, never retry forever.

### Kill switch
If a canonical pause/barrier/kill-switch state is active in the Event Fabric or current state, autonomous mutation stops immediately. Read-only reconstruction/reporting may continue.

## Critical anti-cascade rule
A `next-wave` packet is a proposal for the current reconstructed state only. It MUST NOT be blindly chained into the next invocation. Every wake begins with fresh GitHub/event/state reconstruction. If `main`, event watermark, claims, dependencies or evidence changed, the prior packet is invalid.

A session-end `NEXT_ITERATION_METAPROMPT` is therefore **bootstrap acceleration, not authority**. The next session reads it, then MUST reconstruct live truth before executing any material step.

## Session-end metaprompt contract
Every material session should persist a compact next-iteration packet containing:
- north_star / current objective;
- session/workstream/correlation IDs;
- last observed main SHA + event watermark;
- branch/PR/head SHA;
- exact completed work and authority state;
- active blockers/degraded dependencies;
- released and still-owned scopes;
- tests/evidence with exact outcomes;
- unresolved gauntlet findings;
- highest-value candidate next waves;
- recommended next safe action;
- explicit instruction to invalidate this packet if live truth differs.

The packet should let a future agent understand *where to look and what was learned* without needing chat history, but it must never say “skip reconstruction”.

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
- gauntlet attempts + verifier outcomes
- code-review findings
- security findings
- authority state
- blockers/degraded external dependencies
- evidence refs
- `NEXT_ITERATION_METAPROMPT`
- next safe action

Then the next invocation reconstructs state and compiles again.
