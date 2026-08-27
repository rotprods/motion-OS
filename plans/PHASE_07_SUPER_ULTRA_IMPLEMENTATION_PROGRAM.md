# MOTION.OS — Phase 07 Super Ultra Implementation Program

Status: CANONICAL EXECUTION PLAN (convergence branch)
Scope: cross-session/cross-agent coordination, COS Graph integration, Phase06 Viral Content Intelligence integration, validation, recovery and authority promotion.

## North Star
A zero-context agent can join MOTION.OS, reconstruct current truth from canonical sources, claim safe non-conflicting work, execute without silent collisions, emit durable causal events/checkpoints, hand off safely, and contribute to one deterministic COS projection. Three or more agents can work concurrently without duplicate architecture, stale writes, or semantic contract corruption.

## Canonical control plane
- GitHub executable truth: `rotprods/motion-OS`
- Canonical bootstrap coordination bus: Issue #39
- Canonical Phase07 epic: Issue #41
- Convergence PR: #44 (`feat/agentic-coordination-kernel`)
- Canonical Drive coordination folder: `MOTION.OS_CANONICAL/11_AGENTIC_COORDINATION`
- Phase06 Content/Viral workstream: PR #37
- Studio Engine foundation: merged PR #38 / main
- Remotion runtime proof: merged PR #42 / main
- COS Graph Engine: external reusable projection/query/reasoning substrate; never coordination source of truth.

## Authority matrix
| Plane | Authority |
|---|---|
| Code/contracts | GitHub/main + merged commits |
| Bootstrap developer coordination | GitHub Issue #39 |
| Artifacts/recovery/evidence | Drive |
| Phase06 render execution | SQLite/WAL single-host authority |
| Phase07 multi-host coordination target | provider-neutral durable transactional store; Postgres is one future backend, not a prerequisite for engineering |
| Graph/query/reasoning | COS rebuildable projection |
| Reference semantics | in-memory/local test backends only |

## Global invariants
1. PR closed != merged != CI green != deployed != verified.
2. Commands and outcomes are distinct events.
3. Protected writes require expected revision + lease/fencing semantics.
4. Stale writers fail closed.
5. Duplicate delivery cannot duplicate authoritative effects.
6. GitHub/Drive/event/kernel/graph authority boundaries are explicit and testable.
7. COS may never mutate canonical coordination state through a backdoor.
8. Context Packs are sealed and invalidated on source/main/contract/projection drift.
9. Semantic resources are first-class (`contract:`, `schema:`, `capability:`), not only files.
10. No workstream may silently overwrite another active semantic contract.
11. Existing Phase06 claim, TTS, spend, render, provenance and replay guarantees cannot regress.
12. Completion is evidence-backed; code existence is not authority.

---

# EXECUTION PROGRAM

## PHASE 0 — Reconciliation Freeze
Goal: eliminate duplicate coordination architectures and establish one canonical plan before further feature growth.

Tasks:
- Build PR #40 vs #44 capability matrix.
- Port unique #40 guarantees into #44: aggregate revisions/heads, idempotency keys, parent event IDs, event watermark, inbox, snapshots, structured provenance, command/outcome separation, unified developer+runtime event model.
- Preserve unique #44 guarantees: alias-safe resource scopes, hierarchical overlap resolver, ContextPack staleness/seal, snapshot bootstrap, outbox dispatch leases, deterministic graph hash, authority matrix, 20D scorecard, adversarial gauntlet.
- Reconcile Issue #39/#43 and Epic #41/#45; retain #39/#41 as canonical after evidence migration.
- Reconcile Drive 09 vs 11; retain `11_AGENTIC_COORDINATION` as canonical.
- Update active topology: #38 and #42 merged capabilities; #37 active; #34/#35 historical/superseded.

Checkpoint CP0:
- one bus, one epic, one Drive folder, one convergence PR, one live topology snapshot.

Definition of Done:
- no duplicated canonical control objects;
- every retained guarantee from #40/#44 mapped to one implementation artifact;
- superseded objects point to canonical replacements;
- snapshot reflects current `main` and current PR states.

Evidence required:
- reconciliation matrix;
- GitHub issue/PR state links;
- current main SHA;
- changed-file/capability comparison.

## PHASE 1 — Canonical Domain Model v1
Goal: freeze identity, event, aggregate, lease, resource and ContextPack semantics.

Tasks:
- Canonical URI model for project/agent/session/workstream/task/decision/artifact/content/render/contract/schema/file/tree.
- `AgentEvent`/`CoordinationEvent` convergence into one envelope.
- Add aggregate revision + expected revision + idempotency key + payload hash + provenance refs + causation + parent events + correlation + workstream.
- Explicit event family registry and command/outcome pairs.
- Version JSON Schemas with migration policy.
- Define compatibility policy: additive/minor/breaking.

Checkpoint CP1:
- all contracts serialize/validate deterministically.

DoD:
- one event schema, one lease schema, one ContextPack schema;
- deterministic canonical JSON/hash tests;
- unknown versions fail closed;
- schema compatibility tests exist.

## PHASE 2 — Resource Ownership + Conflict Engine
Goal: prevent semantic collisions before writes happen.

Tasks:
- Canonical `ResourceScope` resolver.
- Path normalization and repo escape rejection.
- Hierarchical `tree:` ↔ `file:` overlap.
- Exact semantic overlap for `contract:`/`schema:`/`capability:`.
- Dependency expansion one hop through COS/local graph.
- Conflict classifier: NONE / PATH_OVERLAP / SEMANTIC_OVERLAP / DEPENDENCY_RISK / AUTHORITY_CONFLICT.
- Work claim planner that returns SAFE / COORDINATE / BLOCK.

CP2:
- concurrent work intents can be compared deterministically.

DoD:
- false negatives in curated collision suite = 0;
- known unrelated resources proceed without global locking;
- conflict explanation includes exact conflicting resource/dependency.

## PHASE 3 — Lease/Fencing/CAS Semantics
Goal: prove stale-writer safety provider-independently.

Tasks:
- unify reference lease store + aggregate CAS.
- monotonic fencing generations per canonical resource.
- READ/WRITE/EXCLUSIVE_WRITE rules.
- heartbeat, expiry, takeover, release, revoke.
- stale completion rejection after takeover.
- expected state revision on protected mutation.
- adversarial race tests with threads/processes.

CP3:
- one writer wins; stale writer cannot commit.

DoD:
- 1000+ randomized races, zero dual-writer authority;
- takeover increments generation monotonically;
- stale token and stale revision both fail closed.

## PHASE 4 — Event Bus + Event-Sourced State
Goal: make coordination replayable and causally reconstructable.

Tasks:
- event append API with idempotency and aggregate revisions.
- aggregate heads.
- transactional semantic oracle in reference backend.
- durable cursor abstraction.
- command/outcome separation.
- parent/causation/correlation semantics.
- poison/unknown event quarantine policy.

CP4:
- event history reconstructs same aggregate heads and state hash.

DoD:
- duplicate event replay yields same logical result;
- idempotency-key collision with different payload fails;
- invalid revision rejected;
- deterministic replay tests pass.

## PHASE 5 — Outbox / Inbox / Consumer Semantics
Goal: guarantee at-least-once transport without duplicate side effects.

Tasks:
- transactional outbox contract.
- dispatcher claim leases / SKIP LOCKED equivalent in provider adapter.
- inbox/idempotency records.
- monotonic consumer offsets.
- retry/backoff/dead-letter/quarantine.
- crash between effect and ack scenarios.

CP5:
- duplicate/reorder/restart campaign passes in reference integration tests.

DoD:
- duplicate delivery => one logical effect;
- restart resumes from durable cursor;
- reordered events either buffer/resolve or fail explicitly;
- poison event does not block unrelated streams indefinitely.

## PHASE 6 — Zero-Context ContextPack Compiler
Goal: remove chat history as a hidden dependency.

Tasks:
- compile from GitHub state, Drive refs, accepted decisions, leases, blockers, dependencies, graph neighborhood, evidence refs.
- event watermark + projection hash.
- main SHA + source hashes + contract revisions.
- allowed/forbidden write scopes.
- next-safe-actions compiler.
- SHA-256 seal.
- invalidation on main/PR/contract/source/Drive/projection drift.

CP6:
- a fresh session can produce a valid bounded ContextPack from canonical sources.

DoD:
- stale main SHA fails closed;
- mutated source hash invalidates pack;
- changed contract revision invalidates relevant pack;
- no required context field is sourced only from chat memory.

## PHASE 7 — GitHub Lifecycle Bridge
Goal: synchronize executable truth into coordination state.

Tasks:
- ingest PR open/update/close/merge, commits, branch/base SHA, CI conclusions.
- explicitly model `CLOSED_UNMERGED`, `MERGED`, `CI_GREEN`, `CI_FAILED`.
- drift detector for agent registry/snapshot.
- workstream lifecycle transitions.
- semantic changed-file impact hooks.

CP7:
- #34/#35 historical and #38/#42 merged are represented correctly automatically.

DoD:
- no closed PR remains ACTIVE;
- merge is not inferred from close;
- main advancement invalidates stale sessions;
- GitHub bridge replay is idempotent.

## PHASE 8 — Drive Evidence + Recovery Bridge
Goal: make artifacts/recovery durable without making Drive transaction authority.

Tasks:
- canonical Drive folder map.
- content-addressed or revision-pinned artifact refs.
- evidence manifests.
- immutable checkpoint/handoff convention.
- Drive drift checks.
- duplicate folder/control-plane reconciliation.

CP8:
- a cold agent can locate relevant evidence and latest handoff deterministically.

DoD:
- no mutable Drive alias can silently replace referenced evidence;
- missing evidence is surfaced explicitly;
- superseded folders redirect to canonical location.

## PHASE 9 — COS Graph Projection v1
Goal: connect all engineering activity to one deterministic graph.

Tasks:
- pin qualified COS Graph Engine commit/version.
- implement MOTION-owned adapter; COS remains generic.
- node types: Project, Agent, Session, Workstream, Task, Decision, Branch, Commit, PR, Contract, Schema, Artifact, Evidence, Content, Render, TestRun, Metric, Incident.
- edges: OWNS, WORKS_ON, DEPENDS_ON, BLOCKS, TOUCHES, MODIFIES, PRODUCES, CONSUMES, SUPERSEDES, CAUSED_BY, VERIFIED_BY, CONFLICTS_WITH, IMPLEMENTS, DERIVED_FROM.
- source_event_id + temporal validity + projection version/hash.
- rebuild from zero.

CP9:
- identical event history => identical canonical graph hash.

DoD:
- destroy/rebuild produces equivalent graph;
- graph outage does not corrupt coordination authority;
- projection lag is observable;
- no reverse mutation path.

## PHASE 10 — Shared Planning Graph
Goal: make plans/tasks/checkpoints cross-session and queryable.

Tasks:
- Goal → Plan → Phase → Task → Checkpoint → Evidence model.
- task states + dependencies + blockers + owners.
- next-safe-task query.
- plan revision/supersession lineage.
- integrate Epic #41 and repo plan files.

CP10:
- an agent can query “what is the next safe task for my scope?” without reading the whole repo manually.

DoD:
- every active Phase07 task maps to owner/status/dependencies/DoD/evidence;
- impossible dependency cycles fail validation;
- checkpoint completion updates graph deterministically.

## PHASE 11 — Phase06 Viral Content Intelligence Full Integration
Goal: make Viral Engine a native upstream domain of MOTION.OS, not a side document.

Tasks:
- finalize Signal/Opportunity/Goal/Account routing contracts.
- angle + hook + first-frame tournaments.
- dual ViralPotential/StrategicValue scoring.
- proof-first contract.
- visual blueprint + Studio handoff.
- platform-native adapters.
- publication records.
- append-only analytics snapshots.
- experiment engine with one-primary-variable default.
- learning compiler with support/contradiction/sample/baseline/effect/uncertainty.
- COS Content/Hook/Proof/Performance/Experiment graphs.

CP11:
- one source can flow SourcePack → approved script → avatar handoff → Studio handoff → publication record → analytics → learning candidate with one lineage ID.

DoD:
- factual hook without evidence rejected;
- stable beat IDs preserved;
- performance correlation cannot auto-promote to causal rule;
- platform derivatives preserve provenance;
- cold rebuild reproduces approved script package.

## PHASE 12 — Agent SDK + CLI
Goal: make the coordination system easy enough that every agent actually uses it.

Tasks:
- `hello/start`, `context`, `claim`, `heartbeat`, `checkpoint`, `handoff`, `release`, `conflict`, `status`, `next` commands.
- machine-readable JSON output by default; human-readable optional.
- nonzero exit on policy/staleness/conflict failure.
- SDK protocol interfaces independent of backend.
- local/reference backend first.

CP12:
- a fresh agent can follow the lifecycle using only CLI/SDK + canonical sources.

DoD:
- no manual YAML editing required for normal flow;
- CLI errors never return success;
- all commands emit/consume canonical contracts.

## PHASE 13 — Observability + Audit
Goal: make coordination failures diagnosable.

Tasks:
- correlation tracing across session/workstream/event/PR/content/render.
- metrics: active leases, stale rejects, conflict rate, context invalidations, event lag, projection lag, replay failures, duplicate deliveries, outbox depth.
- structured audit log.
- health report.

CP13:
- one correlation ID traces a task from start through code/evidence/graph/handoff.

DoD:
- every protected failure produces explainable evidence;
- no silent telemetry failure changes protected operation outcome.

## PHASE 14 — Security + Trust Boundaries
Goal: default-deny and provenance-safe coordination.

Tasks:
- sensitivity propagation.
- untrusted source isolation.
- secret redaction/no secrets in events.
- capability/scope checks.
- policy negative tests.
- malicious event payload/schema abuse tests.
- prompt-injection-resistant context compilation.

CP14:
- security gauntlet passes locally.

DoD:
- unauthorized scope mutation rejected;
- restricted evidence excluded above sensitivity ceiling;
- unknown policy operators fail closed;
- event payload cannot smuggle secrets into graph/context logs under test policy.

## PHASE 15 — 3-Agent Adversarial Qualification
Goal: use real concurrent agents as the acceptance workload.

Campaign:
- 3 agents start with zero chat context.
- overlapping and non-overlapping tasks mixed.
- one branch closes without merge.
- another merges while contexts are active.
- agent crashes after lease acquisition.
- stale agent resumes.
- duplicate event delivered.
- graph projection destroyed.
- Drive artifact revision changes.
- semantic contract change proposed mid-session.

CP15:
- system coordinates all cases without hidden collision or false completion.

DoD:
- zero stale authoritative writes;
- zero silent semantic overwrites;
- zero false merged/verified states;
- deterministic recovery/handoff.

## PHASE 16 — Replay / Restore / Disaster Recovery
Goal: prove the system survives loss of ephemeral state.

Tasks:
- delete local caches/reference projections.
- recreate state from GitHub + Drive + event history fixtures.
- rebuild COS graph.
- regenerate ContextPack.
- resume exact next safe action.

CP16:
- cold restore is reproducible.

DoD:
- same state hash and graph hash from same history;
- no chat transcript required;
- missing external evidence produces explicit degraded/block state.

## PHASE 17 — CI / Contract Gates
Goal: institutionalize validation.

Tasks:
- schema validation gate.
- coordination unit tests 3.11/3.12.
- CLI smoke tests.
- replay determinism test.
- resource collision suite.
- ContextPack staleness suite.
- graph rebuild hash test.
- integration/adversarial profile separated from cheap PR checks.

CP17:
- every coordination PR receives deterministic gates.

DoD:
- no merge on contract/test failures;
- expensive tests are explicit and reproducible;
- skipped capability tests are reported as skips, never success claims.

## PHASE 18 — Documentation / Operator UX
Goal: make the system operable by humans and agents.

Tasks:
- `coordination/README_FIRST.md` canonical quickstart.
- architecture diagrams.
- authority matrix.
- incident/runbook.
- adding a new agent guide.
- adding a new contract/resource guide.
- backend adapter guide.

CP18:
- zero-context human/agent can understand authority and safe workflow quickly.

DoD:
- docs match code/schema names;
- no duplicated conflicting README authority.

## PHASE 19 — 20D Gauntlet + Gap Closure
Goal: force every critical vertical toward production quality.

Dimensions:
1 identity/contracts
2 event semantics
3 idempotency
4 revisions/CAS
5 leases/fencing
6 conflict engine
7 ContextPack
8 GitHub bridge
9 Drive bridge
10 COS projection
11 planning graph
12 Phase06 content integration
13 SDK/CLI
14 observability
15 security
16 replay/recovery
17 concurrency
18 test/CI quality
19 operability/docs
20 architecture boundaries

Scoring:
- Build 0–10
- Assurance 0–10
- Authority = min(Build, Assurance)

CP19:
- no critical dimension Authority < 9 for promotion candidate.

DoD:
- every score links to evidence;
- unverified dimensions cannot be rounded upward.

## PHASE 20 — Optional Multi-Host Durable Backend Promotion
Goal: only after semantics are proven locally, add a network transactional authority when genuinely required.

Tasks:
- select backend (Postgres/Supabase-class or equivalent) through adapter contract.
- migrations/RLS/service identities if Postgres selected.
- run same conformance suite against network backend.
- multi-host race/crash/restart tests.

CP20:
- backend passes reference-semantic conformance.

DoD:
- backend choice does not change domain contracts;
- no authority promotion without real concurrent-host evidence.

---

# Promotion Ladder
DESIGN_ONLY → LOCAL_REFERENCE_VERIFIED → BOOTSTRAP_COORDINATION → SHADOW_DURABLE → ASSISTED_COORDINATION → ENFORCED_DEVELOPER_LEASES → ENFORCED_RUNTIME_LEASES → MULTI_HOST_AUTHORITY

Promotion rule: move only when evidence for the next rung exists. No automatic promotion because implementation exists.

# Definition of Done — Whole Program
The program is done only when:
1. there is one canonical coordination/control architecture;
2. a zero-context agent reconstructs current truth deterministically;
3. 3+ agents coordinate safely on real repo work;
4. semantic/path conflicts are detected before unsafe write;
5. stale writer/duplicate delivery/replay are safe;
6. GitHub/Drive lifecycle drift is reconciled;
7. COS graph rebuild is deterministic and non-authoritative;
8. Phase06 Viral Content Intelligence participates in the same lineage/graph;
9. disaster recovery does not require chat history;
10. 20D critical Authority scores are >=9 with linked evidence.

# Immediate Execution Order
P0 Reconcile #40/#44 and canonical control objects → P1 contracts → P2 resource/conflict → P3 leases/CAS → P4 event state → P6 ContextPack → P7 GitHub bridge → P9 COS projection → P10 planning graph → P11 Viral integration → P12 SDK → P15 real 3-agent gauntlet → remaining assurance/security/recovery → optional network backend last.
