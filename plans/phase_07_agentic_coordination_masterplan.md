# Phase 07 — Agentic Coordination + COS Graph Integration Masterplan

Status: PROPOSED
Depends on: current `main`, PR #34, PR #35, PR #37 contract reconciliation
Bootstrap bus: issue #39

## North Star
Any new agent with zero chat context can join MOTION.OS, reconstruct current truth, claim non-conflicting work, execute with causal/provenance guarantees, hand off safely, and contribute to a shared graph without corrupting another workstream.

## Success criteria
- 3+ concurrent developer agents can operate without silent semantic overlap.
- 10+ runtime agents can exchange events with durable offsets/idempotency.
- stale writer after lease takeover is deterministically rejected.
- crash after external provider acceptance cannot duplicate spend.
- every material decision/task/artifact is causally linked.
- event log -> state -> COS graph rebuild is deterministic.
- a cold session restores from canonical surfaces without chat memory.
- cross-session Context Pack has exact event watermark + projection hash.
- zero P0 cross-workstream collisions in qualification gauntlet.

## Wave 0 — Bootstrap coordination now
Deliverables:
- GitHub issue #39 as append-only coordination bus.
- comments linked from active PRs #34/#35/#37.
- mandatory event envelope + resource-scope protocol.
- `coordination/agent_registry.json`.
- AGENTS.md coordination rules.

Gate W0: all active workstreams have explicit authority boundaries and a shared handoff path.

## Wave 1 — Canonical model and contracts
Build:
- AgentEvent v1 schema.
- AgentLease v1 schema.
- ContextPack v1 schema.
- Workstream/Task/Decision identity contracts.
- event-type catalog and compatibility rules.
- canonical URI identity library.

Tests:
- schema positive/negative fixtures;
- duplicate idempotency key rejection;
- invalid causal references;
- sensitivity/provenance validation.

Gate W1: contracts frozen v1; additive evolution only without schema-version bump.

## Wave 2 — Durable Event Kernel
Target: Postgres/Supabase-class transactional store. Do NOT reuse unrelated existing Supabase projects.

Tables:
- agent_events
- aggregates
- workstreams
- tasks
- decisions
- agent_sessions
- resource_leases
- consumer_offsets
- outbox
- inbox
- state_snapshots
- graph_projection_checkpoints

Guarantees:
- append-only event rows;
- UNIQUE(project_id, idempotency_key);
- aggregate revision CAS;
- commands and outcomes separate;
- DB-generated recorded_at;
- payload SHA-256;
- serializable or explicit row-lock transaction for lease changes;
- RLS/capability-aware access when external clients connect.

Gate W2: two independent clients race for same resource; exactly one active generation wins and loser is rejected.

## Wave 3 — Lease/Fencing Kernel
Implement acquire/heartbeat/release/takeover/check-write-authority.

Lease semantics:
- generation is monotonically increasing;
- owner/session/branch/workstream recorded;
- takeover allowed only after expiry or explicit release;
- protected write provides generation + expected aggregate revision;
- stale generation never mutates canonical state;
- external side effects require reconciliation before retry after ambiguity.

Adversarial cases:
- clock skew;
- worker pause > TTL;
- double heartbeat;
- concurrent takeover;
- lease expires during provider call;
- stale completion arrives after takeover.

Gate W3: no stale completion can overwrite newer state.

## Wave 4 — Outbox / Inbox + consumer runtime
Implement reliable event fan-out.

Consumers:
- COSGraphProjector
- ContextIndexer
- DriveEvidenceIndexer
- GitHubStateObserver
- RuntimeOrchestrator
- ObservabilityCollector
- Notification/ConflictDetector

Rules:
- at-least-once delivery accepted;
- inbox makes handlers idempotent;
- offsets/watermarks durable;
- poison event quarantined, never silently skipped;
- dead-letter includes error + schema + event ID;
- consumer lag observable.

Gate W4: duplicate event delivery produces one logical effect.

## Wave 5 — COS Graph Adapter
Create a MOTION.OS-owned adapter package around generic COS primitives.

Responsibilities:
- map canonical MOTION identities -> COS nodes/edges;
- preserve event provenance and temporal validity;
- version every projection;
- compute projection hash;
- support full rebuild and incremental projection;
- expose dependency/conflict/impact/lineage queries;
- never allow graph mutation to bypass canonical event/state APIs.

Initial projections:
1. DevelopmentGraph — agents/sessions/branches/PRs/tasks/decisions.
2. ProductionGraph — content/beats/assets/renders/timeline/QA.
3. KnowledgeGraph — sources/claims/evidence/rules/hypotheses.
4. PerformanceGraph — publications/metrics/experiments/learning.
5. ResilienceGraph — failures/retries/recoveries/incidents.

Gate W5: destroy graph, replay event log, equivalent graph hash/invariants.

## Wave 6 — Context Pack Compiler
Inputs:
- requested task/scope;
- agent capabilities;
- latest event watermark;
- accepted decisions;
- current workstream/lease graph;
- Git/PR state;
- Drive evidence;
- graph neighborhood.

Output is bounded, permission-filtered, deterministic for same inputs and sealed SHA-256.

Compiler prioritization:
P0 current goal/release blockers/authority rules;
P1 direct dependencies/active conflicts/contracts;
P2 recent decisions/evidence;
P3 historical context only if retrieval score passes threshold.

Gate W6: new agent correctly explains current owners, blockers and next safe action without chat transcript.

## Wave 7 — GitHub Bridge
Observe repository facts as events:
- branch/commit/PR lifecycle;
- CI results;
- merge state;
- review state.

Important: observation events do not invent deployment or verification. `PR_CLOSED`, `PR_MERGED`, `CI_GREEN`, `DEPLOYED`, `VERIFIED` remain distinct.

Bootstrap issue #39 remains readable history but becomes a bridge input; database event kernel becomes authority for coordination after promotion.

Gate W7: branch/PR state can be reconstructed and reconciled against GitHub with explicit drift report.

## Wave 8 — Drive Evidence Bridge
Use immutable/revision-pinned Drive references.

Events reference:
- drive_file_id
- revision_id where supported
- content SHA/hash if exported
- artifact class
- sensitivity
- producer event

No large media in Git. Drive never silently overwrites canonical evidence; replacements supersede prior artifacts.

Gate W8: every promoted master can trace Git SHA -> run manifest -> source evidence -> Drive artifact revisions.

## Wave 9 — Runtime orchestration convergence
Converge current bespoke authority primitives from Phase06 into shared kernels where semantics match.

Do not break working render safety. Migration order:
1. wrap existing RenderStateStore behind shared authority interfaces;
2. prove parity;
3. migrate lease/event primitives;
4. retain provider reconciliation semantics;
5. remove duplicates only after equivalence tests.

Integrate Studio Engine handoff:
- stable beat IDs;
- provenance root;
- manifest/replay fingerprint;
- expected handoff revision;
- downstream acceptance/rejection outcome event.

Gate W9: Phase06 -> Studio -> renderer chain is one causal trace.

## Wave 10 — Conflict and impact engine
Before work starts, query:
- path overlap;
- semantic resource overlap;
- schema/API dependency overlap;
- active lease;
- expected branch base drift;
- touching PRs;
- decision conflicts.

Output:
SAFE | COORDINATION_REQUIRED | BLOCKED | REBASE_REQUIRED | HUMAN_DECISION_REQUIRED.

Gate W10: seeded conflicts across three workstreams are detected before writes.

## Wave 11 — Observability
Metrics:
- events/sec
- append latency
- consumer lag
- active leases
- stale write rejections
- conflicts detected/prevented
- context pack compile latency/size
- graph projection lag
- replay duration
- snapshot age
- duplicate deliveries suppressed
- unresolved blockers

Trace IDs use correlation_id across content -> avatar -> edit -> render -> publish/metric loops.

Gate W11: a failed workflow can be traced end-to-end from one correlation ID.

## Wave 12 — Security / adversarial qualification
Threats:
- forged agent identity;
- prompt injection becoming privileged event;
- lease theft;
- replay attack;
- event tampering;
- poisoned Drive artifact;
- graph query leaks sensitivity;
- duplicate provider spend;
- stale branch making incompatible schema change;
- malicious/buggy consumer advancing offset without effect.

Controls:
- actor authentication/capabilities;
- policy engine fail-closed;
- hashes and immutable events;
- RLS/permissions;
- fencing;
- quarantine/dead-letter;
- provenance/evidence gates;
- explicit authority state transitions.

Gate W12: red-team suite with no P0/P1.

## Wave 13 — Recovery + zero-context drill
Scenarios:
- delete local SQLite;
- cold checkout;
- restart runtime workers;
- rebuild COS projections;
- restore Context Packs;
- resume abandoned work after lease expiry;
- recover from partial external provider acceptance;
- compare Drive/Git/event-kernel digests.

Gate W13: another agent resumes exact next action without original conversation.

## Wave 14 — Promotion
Promotion states:
BOOTSTRAP_GITHUB_BUS
-> SHADOW_EVENT_KERNEL
-> ASSISTED_COORDINATION
-> ENFORCED_DEVELOPER_LEASES
-> ENFORCED_RUNTIME_LEASES
-> RUNTIME_AUTHORITY.

Promotion requires evidence, not code volume.

## Integration with Viral Content Engine
The existing Phase06 Content Intelligence is expanded, not replaced:
Signal -> SourcePack/Claims -> ICP/Angle -> Hooks -> Beat Graph -> Script/TTS -> Avatar -> Studio Handoff -> Master -> Publication -> Metrics -> Experiment -> Learned Insight.

Every object receives canonical identity, revision, provenance and event lineage. Performance observations remain hypotheses until controlled/repeated evidence and explicit rule promotion.

## PR strategy
Small guarantee-oriented PRs after this architecture PR:
- P07.1 contracts/schemas
- P07.2 event store
- P07.3 lease/fencing
- P07.4 outbox/inbox
- P07.5 COS adapter
- P07.6 context compiler
- P07.7 GitHub/Drive bridges
- P07.8 Phase06 migration
- P07.9 conflict engine
- P07.10 qualification

Each PR owns one primary guarantee and must include deterministic tests + adversarial negatives.
