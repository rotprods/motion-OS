# PHASE 08 — CANONICAL EVENT-SOURCE RECONCILIATION + COGNITIVE PAUSE

Status: MASTER IMPLEMENTATION PLAN
Baseline: `main@080dfd5c16bc06100edd716eadc770530dc47af2`
Depends on: Phase05 Studio Engine, Phase06 Content/Avatar + render authority, Phase07 coordination kernel.
North Star: every agent can pause, synchronize, reason and resume from one coherent authority model without chat-dependent truth, stale projections or overlapping silent writes.

## Definition of “canonical Event Bus”

Precise wording:
- **Event Store/history** = canonical coordination state-transition source for coordination aggregates, limited to its qualified authority.
- **Event Bus/realtime/Issue #39** = delivery/bootstrap surfaces.
- **Read models** = rebuildable projections.
- **COS** = rebuildable graph projection.

Do not promote an in-memory reference store into multi-host authority.

---

# Program score gates

A phase is complete only with executed evidence.

| Gate | Target |
|---|---:|
| Projection consistency | 100% generated/read-model hashes match |
| Event replay determinism | 100% |
| Scheduler causal correctness | 100% regression suite |
| Multi-render global timeline integrity | 100% reference fixtures |
| Skill failure observability | 100% terminal paths recorded |
| QA history immutability | 100% distinct run identity |
| Coordination local contention | >=9.5/10 |
| Multi-host authority | remains DISABLED until independent-host campaign >=9.0 |
| Drive coordination evidence | no false authority; provider evidence required |
| Product truth reconciliation | zero conflicting P0/master/runtime read models |

---

# 17 implementation phases / ordered PR train

## P08.0 — Cognitive Freeze & Historical Regression
**Goal:** no work begins from obsolete Phase05 topology.

Deliverables:
- historical lineage map: RC→P01→P07;
- current main/PR/issue topology;
- stale-state inventory;
- code/test gap matrix;
- active CLAIM on Issue #39.

Checkpoint C08.0:
- baseline SHA pinned;
- Phase07 active owners/scopes inspected;
- audit published before shared-contract mutation.

PR08-01: `audit: cognitive pause regression + authority ADR + target graph`

## P08.1 — Canonical Authority Decision
**Goal:** formally eliminate ambiguity between rich CoordinationEvent and lifecycle-file events.

Changes:
- accept ADR-008 after tests;
- document aggregate owners;
- define repository lifecycle projection adapter;
- mark Issue #39 transport/bootstrap, not store authority;
- deprecate obsolete Issue #43 references.

Checkpoint C08.1:
- every coordination/read-model document names one authority owner per aggregate.

PR08-02: `docs(coordination): canonical event-store authority and lifecycle adapter contract`

## P08.2 — State Projection Compiler
**Goal:** eliminate manual state split-brain.

Implement `src/coordination/projections/` and `scripts/reconcile_state.py`.

Inputs:
- GitHub lifecycle snapshot;
- coordination event watermark/snapshot;
- Phase06 render-state evidence;
- artifact/recovery references;
- product promotion decisions.

Outputs:
- `STATE.md`;
- `state/project_state.json`;
- `coordination/ACTIVE_AGENTS.yaml`;
- `coordination/README_FIRST.md` dynamic sections;
- machine-readable `state/projection_manifest.json`.

Every projection records:
- source watermark;
- main SHA;
- aggregate revisions;
- projection schema version;
- content hash.

Checkpoint C08.2:
- rebuild twice → byte-identical projections;
- current committed state reconciles RC/runtime/topology correctly.

PR08-03: `feat(coordination): deterministic canonical state projections`

## P08.3 — Projection Drift Gate
**Goal:** stale state can never merge silently.

Implement:
- `scripts/reconcile_state.py --check`;
- MERGE_SAFE subgate;
- negative test that mutates projected output and expects failure;
- topology resolution test for bus/PR/active agent refs.

Checkpoint C08.3:
- manual drift of any generated read model blocks merge.

PR08-04: `ci(coordination): fail merge-safe on projection drift`

## P08.4 — Event Representation Unification
**Goal:** one logical event model.

Design:
- canonical `CoordinationEvent` command/outcome lifecycle;
- adapter/export to `state/agent_events` for Git-audit evidence;
- deterministic mapping for `work.started/checkpoint/completed/blocked`, PR lifecycle and main verification;
- correlation/causation/idempotency retained;
- file export cannot mutate aggregate state.

Migration:
- existing files remain immutable historical evidence;
- adapter v2 writes canonical event hash + source event ID/watermark.

Checkpoint C08.4:
- one canonical event produces deterministic audit projection;
- duplicate export is idempotent;
- audit file cannot be replayed as a conflicting command without validation.

PR08-05: `feat(coordination): unify lifecycle events behind CoordinationEvent adapter`

## P08.5 — Cognitive Pause Barrier
**Goal:** synchronize all agents before high-blast-radius changes.

Semantics:
- `COGNITIVE_PAUSE_REQUESTED`;
- determine conflicting active write claims;
- agents reach recoverable CHECKPOINT;
- `COGNITIVE_PAUSE_ACKNOWLEDGED`;
- expired/stale leases fenced;
- projections/revisions reconciled;
- `COGNITIVE_PAUSE_RELEASED` with new watermark + ContextPack revision.

No chat message counts as ACK.

Checkpoint C08.5:
- simulated 3-agent contract collision cannot mutate protected contract until barrier release.

PR08-06: `feat(coordination): cognitive pause barrier and context invalidation`

## P08.6 — Scheduler Causal Bugfix
**Goal:** remove filtered-dependency deadlocks.

Fix:
- distinguish executable dependencies from immutable/input dependency closure;
- cache keys include non-executable upstream state;
- scheduler jobs reference only scheduled dependencies or explicit pre-satisfied inputs.

Tests:
- Skill depends on Asset;
- Skill depends on Provider + StyleSignature;
- mixed executable/non-executable chain;
- invalidation still correct.

Checkpoint C08.6:
- no `ready()` deadlock from filtered graph nodes.

PR08-07: `fix(graph): executable dependency closure without scheduler deadlock`

## P08.7 — Multi-render Global Timeline Fix
**Goal:** make renderer assembly correct for real subclips.

Implement:
- graph/z-order explicit in RenderArtifact;
- trim + `setpts=PTS-STARTPTS+start/TB`;
- alpha format handling;
- color-space normalization policy;
- audio graph/master mux;
- base interval validation;
- overlap and gap policy;
- provenance enforced when plan says required.

Tests:
- overlay artifact starts at 1.5s but source duration is 0.5s;
- lexical renderer order cannot override z-order;
- alpha overlay;
- audio duration/tail;
- exact frame count and fps.

Checkpoint C08.7:
- real FFmpeg fixture equals expected frame-level timeline.

PR08-08: `fix(render): global-time z-ordered multi-render assembly`

## P08.8 — Skill Runtime Failure Semantics
**Goal:** no executor crash disappears.

Implement:
- catch/record executor errors;
- `FAILED` vs `BLOCKED`;
- retryability classification;
- error fingerprint/hash, bounded safe message;
- ToolCall/Run event emitted before optional re-raise;
- invocation idempotency key.

Checkpoint C08.8:
- every terminal executor path produces trace/evidence.

PR08-09: `fix(skills): durable failure traces and idempotent invocations`

## P08.9 — QA / Repair Graph Integrity
**Goal:** immutable evaluation history and correct mutation semantics.

Fix:
- QAResult/Defect IDs include run/correlation fingerprint;
- repeated run preserves history;
- explicit finding fingerprint for optional dedupe;
- RepairCandidate `ADDRESSES` defect and `MUTATES` target/subgraph;
- root-cause relation explicit;
- impact traversal tests.

Checkpoint C08.9:
- two QA runs coexist;
- repair graph query resolves defect→candidate→actual mutated target.

PR08-10: `fix(qa): immutable run-scoped findings and target-bound repairs`

## P08.10 — Event Integrity & Replay Root
**Goal:** snapshot proves exact history, not only aggregate heads.

Implement:
- event stream rolling hash / Merkle-compatible root;
- snapshot includes stream root;
- timestamp RFC3339 validation;
- occurred_at <= recorded_at policy with clock-skew envelope where relevant;
- parent/causation validation modes;
- replay verifies event root + aggregate heads + projections.

Checkpoint C08.10:
- historical event tamper invalidates snapshot/replay proof.

PR08-11: `feat(coordination): cryptographically bind snapshots to event history`

## P08.11 — Local Durable Outbox/Inbox Reference
**Goal:** close semantic gap between state mutation and publication without fake distributed transactions.

Implement first against local durable test backend:
- authoritative transaction writes state + outbox;
- dispatcher publishes at-least-once;
- inbox dedupes logical effect;
- poison event quarantine;
- crash after transaction/before publish;
- crash after publish/before ack.

Checkpoint C08.11:
- restart campaign converges with zero lost logical effects.

PR08-12: `feat(coordination): durable outbox/inbox crash-recovery qualification`

## P08.12 — Multi-agent Cognitive Gauntlet
**Goal:** prove synchronization properties adversarially.

Campaigns:
- 3 agents same contract;
- 10 agents mixed scopes;
- 50 simulated agents read/write contention;
- stale ContextPack;
- expired lease takeover;
- duplicate event delivery;
- reordered delivery;
- crash during pause;
- GitHub main moves during session.

Invariants:
- one authority mutation per protected revision;
- no lost accepted event;
- stale writer fails closed;
- projection rebuild deterministic;
- pause cannot release with unresolved conflicting writer.

Checkpoint C08.12:
- local/reference coordination >=9.5 across invariants.

PR08-13: `test(coordination): cognitive-pause and contention gauntlet`

## P08.13 — Drive Evidence Bridge Requalification
**Goal:** raise D17 without turning Drive into coordination authority.

Implement/verify:
- retry/backoff/provider errors;
- immutable artifact ID + hash + revision evidence;
- recovery attestation references event watermark/main SHA;
- provider unavailable → DEGRADED, never success.

Checkpoint C08.13:
- live provider campaign if connector healthy; otherwise remains explicitly open.

PR08-14: `feat(evidence): Drive bridge qualification and degradation semantics`

## P08.14 — GitHub Promotion Enforcement
**Goal:** policy cannot be bypassed accidentally.

Target:
- protect/ruleset `main`;
- require MERGE_SAFE + Coordination Contracts;
- forbid force pushes/deletions;
- review/direct-push detector if settings path unavailable.

Checkpoint C08.14:
- direct unverified mutation is prevented or detected/blocking by independent enforcement.

PR08-15: `ops: enforce merge-safe promotion on main`

## P08.15 — Product Truth Reconciliation
**Goal:** coordination work does not leave creative/product truth stale.

Reconcile:
- Remotion = runtime verified;
- HyperFrames = current runtime status;
- temporal critic = current status;
- working master / candidate truth (RC06 vs RC09E);
- Phase05/06/07 status;
- benchmark/primitives counts from actual evidence.

Checkpoint C08.15:
- all projected state surfaces agree byte/logically on active P0 and current master.

PR08-16: `state: reconcile canonical product/runtime truth from authority planes`

## P08.16 — Zero-chat Recovery + Return to Product
**Goal:** prove a fresh agent can resume exclusively from canonical state.

Recovery exercise:
1. read main + sealed ContextPack;
2. replay coordination event history;
3. rebuild state projections + COS;
4. verify hashes;
5. identify active P0 and exact next task;
6. verify no chat context is required.

Then release cognitive pause and return priority to:
- HyperFrames physical runtime;
- authoritative temporal multimodal critic;
- Apple-level complex benchmark;
- creative convergence >=9.

Checkpoint C08.16:
- zero-chat recovery PASS and `COGNITIVE_PAUSE_RELEASED` emitted.

PR08-17: `release(coordination): seal Phase08 recovery and release product workstreams`

---

# PR dependency train

`01 → 02 → 03 → 04 → 05 → 06`

Then bugfix lanes may proceed with declared non-overlapping scopes:
- Graph lane: `07`
- Renderer lane: `08`
- Skill/QA lane: `09 → 10`
- Event integrity lane: `11 → 12 → 13`

Converge:
`14 → 15 → 16 → 17`

Every PR:
- starts with coordination CLAIM;
- records expected main SHA + event watermark + ContextPack revision;
- runs local relevant profile;
- runs MERGE_SAFE/Coordination Contracts before promotion;
- publishes CHECKPOINT/HANDOFF;
- cannot silently edit another active write scope.

---

# Plan-level Definition of Done

Phase08 is complete only when:
- one event-store coordination model is canonical;
- simple lifecycle JSON is projection/evidence, not peer authority;
- zero read-model drift;
- scheduler mixed-dependency bug fixed;
- multi-render region timing/z-order correct;
- skill failures observable;
- QA history immutable/run-scoped;
- repair relations target actual mutated subgraphs;
- event snapshots bind exact history;
- outbox/inbox crash campaign passes;
- cognitive pause contention gauntlet passes;
- main promotion enforcement exists or an explicit fail-closed substitute exists;
- product P0/master state reconciled;
- zero-chat recovery passes;
- no claim of multi-host or live Drive authority without executed evidence.

## Optional P20 — true distributed coordination authority

Only trigger if multiple independent execution hosts become an operational requirement. Candidate: PostgreSQL/Supabase transactional event store with durable offsets, leases/fencing and outbox. Required before promotion:
- independent processes/hosts;
- network faults/reordering;
- isolation/fencing proof;
- crash/restart;
- no lost accepted writes;
- D06 >=9.0.

Until then, do not spend complexity budget on distributed infrastructure.
