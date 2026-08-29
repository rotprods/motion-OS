# MOTION.OS V2 — Definition of Done Law

Authority: `IMPLEMENTED_PENDING_REVIEW`

`DONE` is an authority state, not “code exists”.

## Universal task DoD

A task is DONE only when every applicable condition is satisfied:

- implementation/artifact exists at an exact revision;
- required tests were actually executed and passed;
- `NOT_RUN`, `SKIPPED`, `CANCELLED`, `PASS`, `FAIL` remain distinguishable;
- security/trust-boundary implications were reviewed;
- affected documentation/state/graph/decision history was updated or explicitly delegated to the canonical owner;
- evidence is bound to the exact subject/source/spec/runtime/provider/run/artifact it verifies;
- no unresolved P0/P1 was introduced;
- rollback/compensation is understood where applicable;
- durable checkpoint/handoff allows zero-context continuation.

If any applicable item is absent: `NOT_DONE`.

## Phase DoD

A phase is DONE when every required task is DONE or explicitly DEFERRED with measured trigger, phase integration/adversarial tests pass, downstream consumers are rechecked, all new P0/P1 findings are closed or the phase is BLOCKED, outputs/evidence/checkpoint are durable, and next-phase entry criteria are objectively true.

## Program DoD

The V2 program is DONE only at CP14 when:

- one coherent canonical architecture remains;
- current truth is reconciled and machine/human projections agree;
- Event Fabric/session/claim semantics are promoted and recoverable;
- critical renderer paths are physical and provenance-bound;
- full-video temporal critic is authoritative on a real recoverable master;
- empirical creative/product thresholds are met;
- primitive/benchmark aggregates are recomputable from exact evidence;
- security/recovery/concurrency/death drills pass;
- GitHub main governance is actually active;
- P0=0 and P1=0;
- no V1/V2 competing authority remains;
- release and rollback artifacts are recoverable;
- final combined-head/main verification passes and `main.verified` is persisted.

## Domain-specific DoD

### Architecture / contract
Alternatives/tradeoffs/reconsideration trigger recorded; consumers/migration mapped; no duplicate authority; schema/version compatibility addressed.

### Code
Compile/type/static checks applicable to the language pass; unit/property/integration tests cover success/error paths; failures cannot silently widen authority; dead/duplicate path considered for deletion.

### Event/state
Idempotency/replay behavior defined; stale/out-of-order/duplicate/concurrent cases tested; revision/watermark invalidation explicit; historical truth preserved.

### Agent/session
Globally unique session identity; semantic/path scopes declared; current ContextPack/watermark recorded; claims/leases released or transferred; handoff names exact next safe action.

### Renderer/media
Source/spec/runtime/run/artifact identity bound; frame count/fps/time base measured; applicable audio/alpha/color contracts verified; physical evidence and artifact hash persisted.

### Temporal critic / repair
Samples are media-bound and clock-valid; defect intervals contain supporting evidence; provider/result identity matches evidence identity; repair targets are actual mutable targets; mechanical smoke cannot grant semantic/creative authority.

### Benchmark / empirical
Exact suite/entity IDs exist; every counted success maps to evidence; aggregates are recomputable; unseen/generalization coverage explicit; correlation and causation remain distinct.

### Security
Input trust boundary classified; high-risk exploit/failure-family tests exist; secret/PII persistence reviewed; dependency/supply-chain evidence current; residual risk has owner/trigger/resolution.

### Recovery
Reconstruction source set documented; graph/read-model deletion recovery proven; missing external evidence degrades explicitly; recovered state reproduces important blockers/owners/next action; no chat/local cache is unique authority.

## Evidence freshness law

A DONE claim loses promotion authority when main advances without combined-head revalidation, event watermark changes relevant authority/scopes, subject/source/spec/artifact identity changes, required runtime/provider/dependency identity changes, or a new regression/security finding invalidates its invariant.

Historical DONE remains historical evidence; it does not automatically authorize a new revision.