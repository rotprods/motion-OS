# MOTION.OS V2 — Definition of Done Law

Authority: `PROPOSED_V2_CANDIDATE`

`DONE` is an authority state, not a synonym for “code exists”.

## Universal task DoD

A task is DONE only when every applicable condition is satisfied:

- implementation/artifact exists at an exact revision;
- required tests were actually executed;
- required tests passed;
- `NOT_RUN`, `SKIPPED`, `CANCELLED`, `PASS`, `FAIL` remain distinguishable;
- security/trust-boundary implications were reviewed;
- documentation affected by the semantic change was updated or explicitly declared unaffected;
- current state/task/checkpoint projections were updated or explicitly deferred to the canonical owner;
- graph nodes/edges/authority changes were updated when semantics changed;
- relevant decision/incident/regression history was persisted;
- evidence is bound to the exact subject/source/spec/runtime/run/artifact it claims to verify;
- no unresolved P0/P1 was introduced;
- rollback/compensation is known for reversible/irreversible effects;
- session checkpoint/handoff allows zero-context continuation.

If any applicable item is absent: `NOT_DONE`.

## Phase DoD

A phase is DONE when:

1. every required phase task is DONE or explicitly `DEFERRED` with a measured trigger and no dependency from the phase exit;
2. phase-level integration/adversarial tests pass;
3. dependencies and downstream consumers are rechecked after implementation;
4. all new P0/P1 findings are closed or the phase is `BLOCKED`;
5. phase outputs/evidence/checkpoint are durable;
6. next phase entry criteria are objectively true.

A phase may be `IMPLEMENTED` without being DONE.

## Program DoD

The V2 program is DONE only at CP14 when:

- canonical architecture is coherent and unique;
- current truth is reconciled and machine/human projections agree;
- authority hierarchy is explicit and enforced;
- Event Fabric/session/claim semantics are promoted and recoverable;
- critical renderer paths are physical and evidence/provenance bound;
- temporal/full-video critic is authoritative on a real recoverable master;
- creative/product empirical thresholds are met;
- exact primitive/benchmark evidence supports all aggregate metrics;
- security/recovery/concurrency/death drills pass;
- GitHub main governance is actually active;
- P0=0 and P1=0;
- migration leaves no competing V1/V2 current authority;
- exact release and rollback artifacts are recoverable;
- final combined-head/main verification passes;
- `main.verified` and release evidence are persisted.

## Domain-specific additions

### Architecture / contract
- alternatives/tradeoffs/reconsideration trigger recorded;
- consumers and migration impact mapped;
- no duplicate authority introduced;
- schema/version compatibility addressed.

### Code
- compile/type/static checks applicable to language pass;
- unit/property/integration tests cover success and error paths;
- failure modes do not silently widen authority;
- dead/duplicate path considered for deletion.

### Event/state
- idempotency/replay behavior defined;
- stale/out-of-order/duplicate/concurrent behavior tested;
- revision/watermark invalidation explicit;
- historical truth preserved.

### Agent/session
- globally unique session identity;
- semantic/path scopes declared;
- current ContextPack and watermark recorded;
- claims/leases released or transferred;
- handoff names exact next safe action.

### Renderer/media
- source/spec/runtime/run/artifact identity bound;
- frame count/fps/time base measured;
- audio/alpha/color contracts applicable to the artifact verified;
- physical runtime evidence available;
- artifact hash persisted.

### Temporal critic / repair
- evidence samples are media-bound and clock-valid;
- defect intervals contain their supporting evidence;
- provider/result identity matches evidence identity;
- repair targets refer to actual mutable targets, not causal defect nodes;
- semantic/creative score cannot be inferred from mechanical smoke.

### Benchmark / empirical
- exact suite/entity IDs exist;
- every counted success maps to evidence;
- aggregate metrics are recomputable from ledger;
- unseen/generalization coverage is explicit;
- correlation and causation states remain distinct.

### Security
- input is classified by trust boundary;
- exploit/failure-family tests exist for relevant high-risk paths;
- secret/PII persistence reviewed;
- dependency/supply-chain evidence current;
- residual risk has owner, trigger and resolution path.

### Recovery
- reconstruction source set documented;
- graph/read-model deletion recovery proven;
- missing external evidence degrades explicitly;
- recovered state reproduces important blockers/owners/next safe action;
- no chat/local cache is required as unique authority.

## Evidence freshness law

A DONE claim is invalidated for promotion if:

- main advances and the candidate was not combined-head revalidated;
- event watermark advances in a way that changes claimed scopes/authority;
- artifact/media/source/spec identity changes;
- required provider/runtime/dependency identity changes;
- a regression/security finding invalidates a protected invariant.

Historical DONE remains historical evidence; it does not automatically authorize a new revision.