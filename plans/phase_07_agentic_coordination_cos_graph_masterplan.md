# Phase 07 — Agentic Coordination + COS Graph Integration Masterplan

Status: PROPOSED / CONTROL-PLANE IMPLEMENTATION
Date: 2026-08-26
Owner: MOTION.OS
North Star: three or more concurrent agents can work cross-session on MOTION.OS without silent collisions, stale context, duplicated work, false completion or causal ambiguity.

## 0. Why this phase exists

MOTION.OS already has strong local persistence and execution primitives:
- GitHub = software truth
- Drive = artifacts/progress/recovery truth
- SQLite = structured single-host operational knowledge
- Graph = execution/causal lineage
- Phase 06 introduces leases, fencing, render intent idempotency, replay fingerprints, provenance roots and a move toward network transactional authority.

The remaining coordination gap is multi-agent/multi-session shared truth. Three agents are currently active on distinct but interacting lines:
- PR #34: Remotion production-runtime proof
- PR #35: physical analysis + Studio Engine
- PR #37: Content Intelligence + Avatar Factory + distributed authority

These branches can currently diverge without a single durable coordination plane. A chat-local plan or mutable markdown checklist is insufficient.

## 1. Architectural decision

Do NOT embed content-specific behavior into COS Graph Engine.
Do NOT make the graph the transactional source of truth.
Do NOT use SQLite as multi-host authority.

Use a four-plane architecture:

1. GitHub — executable truth
2. Postgres/Supabase — durable coordination/event/state truth
3. Drive — heavy artifact/evidence/recovery truth
4. COS Graph Engine — deterministic derived projection for traversal, GraphRAG, dependency analysis, impact analysis, context compilation and causal reasoning

The graph MUST be rebuildable from durable events + authoritative state.

## 2. Coordination kernel

### 2.1 Durable Event Log
Append-only event stream. Every material operation emits an event.

Required event envelope:
- event_id UUID
- schema_version
- event_type
- aggregate_type
- aggregate_id
- project_id
- run_id
- session_id
- agent_id
- causation_id
- correlation_id
- expected_revision
- occurred_at
- recorded_at
- payload
- evidence_refs
- git_sha / branch / pr_number where applicable
- provenance_hash
- sensitivity

Core event families:
- agent.registered
- agent.heartbeat
- agent.session_started
- agent.session_ended
- work.claim_requested
- work.claim_acquired
- work.claim_rejected
- work.claim_released
- work.claim_expired
- task.started
- task.blocked
- task.completed
- task.failed
- decision.proposed
- decision.accepted
- decision.rejected
- file.intent_declared
- file.changed
- contract.changed
- schema.changed
- graph.projection_requested
- graph.projection_completed
- context.pack_compiled
- context.pack_rejected
- artifact.created
- artifact.promoted
- pr.opened
- pr.updated
- pr.ready
- pr.merged
- conflict.detected
- conflict.resolved
- checkpoint.created
- recovery.started
- recovery.completed

### 2.2 Transactional Outbox
Any authoritative state mutation and its event are committed in one DB transaction.
A dispatcher publishes outbox records to subscribers/realtime channels.
No dual-write DB→bus race is allowed.

### 2.3 Inbox / Consumer offsets
Every consumer records event IDs / stream offsets already processed.
Processing must be idempotent.
At-least-once delivery is acceptable; duplicate side effects are not.

### 2.4 Leases + fencing
Work claims use leases, not informal ownership.
Lease includes:
- lease_id
- resource_uri
- scope
- agent_id
- generation/fencing_token
- acquired_at
- expires_at
- heartbeat_at
- expected_revision

A stale agent may still run locally but MUST be rejected when attempting an authoritative write with an old fencing token.

### 2.5 Optimistic concurrency / CAS
Mutable authoritative aggregates expose revision numbers.
Writes provide expected_revision.
Mismatch = conflict, never silent overwrite.

## 3. Agent identity model

Canonical URI form:
`motion://agent/{agent_id}`
`motion://session/{session_id}`
`motion://task/{task_id}`
`motion://artifact/{artifact_id}`
`motion://repo/rotprods/motion-OS/pr/{number}`
`motion://file/{repo-relative-path}`

Agent record:
- agent_id
- runtime: chatgpt|codex|claude|gemini|human|other
- capability_set
- session_id
- branch
- active_pr
- claimed_scopes
- last_heartbeat
- status
- context_pack_hash
- authority_level

Display names are metadata only, never identity.

## 4. Anti-collision protocol

Before editing:
1. reconstruct canonical context
2. register session
3. inspect active leases + changed-file intents + PR overlap
4. declare work intent
5. acquire scope lease
6. compile a bounded ContextPack
7. only then mutate files/state

Resource scopes may be:
- file exact: `file:src/content/content_factory.py`
- subtree: `tree:src/content/**`
- contract: `contract:avatar-handoff-v2`
- schema: `schema:avatar_content_manifest`
- phase: `phase:06/content-intelligence`
- semantic resource: `resource:studio-entry-contract`

Lease granularity should be the smallest safe scope. Avoid repository-wide locks.

If two agents need the same resource:
- read/read is allowed
- read/write is allowed with revision awareness
- write/write requires explicit conflict resolution or scope decomposition

## 5. Shared ContextPack

Every agent session receives a deterministic, bounded context compiled from authoritative sources.

ContextPack must contain:
- North Star + current release gates
- current main SHA
- active PRs and their relationship to current task
- active agents + leases
- task dependency neighborhood
- decisions affecting scope
- contracts/schemas affecting scope
- relevant evidence and artifact lineage
- unresolved conflicts
- last checkpoints
- exact allowed write scope
- exact forbidden write scope
- expected revisions
- stale-after timestamp
- projection_version + projection_hash
- source refs + SHA-256 pack seal

A ContextPack with stale graph version/hash or stale source revisions MUST fail closed for authoritative writes.

## 6. COS Graph projection

COS is the query/reasoning plane, not the event authority.

Node classes:
Project, Goal, Phase, Task, Agent, Session, Branch, Commit, PullRequest, File, Contract, Schema, Decision, Claim, Artifact, Evidence, Run, Renderer, Provider, Benchmark, Metric, Risk, Incident, Checkpoint, Event.

Core edges:
AGENT --OWNS_LEASE--> RESOURCE
AGENT --EXECUTES--> TASK
SESSION --RUN_BY--> AGENT
TASK --DEPENDS_ON--> TASK
TASK --TOUCHES--> FILE
TASK --CHANGES--> CONTRACT
PR --IMPLEMENTS--> TASK
PR --TOUCHES--> FILE
PR --DEPENDS_ON--> PR
COMMIT --BELONGS_TO--> PR
DECISION --GOVERNS--> CONTRACT
ARTIFACT --DERIVED_FROM--> ARTIFACT
ARTIFACT --PRODUCED_BY--> RUN
EVIDENCE --SUPPORTS--> CLAIM
CONFLICT --BETWEEN--> RESOURCE
EVENT --CAUSED_BY--> EVENT
CHECKPOINT --SUMMARIZES--> SESSION

Projection requirements:
- deterministic IDs
- versioned projection
- forward + reverse indexes
- temporal validity
- provenance
- sensitivity/project filtering
- rebuild from event log
- snapshot hash
- no mutation back into source truth through graph APIs

## 7. Coordination views

Materialized/read models:
- active_agent_view
- active_lease_view
- task_status_view
- pr_dependency_view
- file_collision_view
- contract_impact_view
- unresolved_conflict_view
- session_resume_view
- latest_checkpoint_view
- projection_health_view

## 8. Immediate GitHub Coordination Bus

Until Postgres event authority is deployed, GitHub Issue `MOTION.OS Agent Coordination Bus` acts as an interim durable human/agent-readable channel.

Agents publish structured comments for:
- HELLO
- CLAIM
- HEARTBEAT
- BLOCKED
- DECISION
- RELEASE
- CHECKPOINT

This is not the final runtime bus and is not suitable for high-frequency telemetry. It is a zero-infrastructure bootstrap for cross-session coordination.

## 9. Supabase/Postgres target

Recommended: dedicated MOTION.OS coordination database/project rather than reusing unrelated production databases.

Tables:
- coordination_events
- coordination_outbox
- coordination_consumers
- agent_sessions
- agent_heartbeats
- resource_leases
- work_items
- work_dependencies
- decisions
- conflicts
- checkpoints
- context_packs
- graph_projection_versions

Security:
- RLS/default deny
- service identities per runtime
- no provider secrets in events
- sensitivity labels
- immutable append-only event rows
- audit trigger / hash chain optional hardening

## 10. Runtime communication

Postgres NOTIFY/Realtime is wake-up transport only; the durable table is authority.
Consumers always recover from durable offsets after disconnect.
No correctness guarantee depends on websocket continuity.

## 11. Cross-agent merge discipline

- one guarantee / coherent semantic unit per PR
- PR declares touched contracts and scopes
- no agent may overwrite another active lease silently
- before rebase/merge, run graph impact query
- merge emits durable event
- all affected ContextPacks become stale after contract/schema/main revision changes
- stale sessions must refresh before further authoritative writes

## 12. Relationship to active PRs

PR #34 Remotion:
- owns renderer/runtime qualification
- may emit renderer.capability_verified and artifact evidence
- must not redefine Content→Studio handoff without coordination

PR #35 Studio Engine:
- owns physical analysis and downstream editing execution
- consumes sealed Phase06 handoff
- should expose one explicit Studio entry contract

PR #37 Content/Avatar:
- owns upstream content/avatar and render authority
- already has lease/fencing/idempotency primitives
- Phase07 should reuse those semantics rather than introduce a competing state machine

## 13. Implementation waves

### W0 — Coordination constitution
- protocol + registry + schemas + masterplan
- GitHub interim bus
- active PR topology
- no runtime behavior changes

### W1 — Postgres durable event kernel
- migrations
- append API
- transactional outbox
- consumer offsets/inbox
- tests for duplicate/reorder/restart

### W2 — Agent registry + leases
- registration/heartbeat
- resource claims
- fencing
- CAS
- crash expiry/takeover tests

### W3 — Context compiler
- deterministic ContextPack
- dependency neighborhood
- policy filter
- hash seal
- stale pack rejection

### W4 — COS adapter/projection
- canonical entity mapping
- event→projection compiler
- snapshot/hash/rebuild
- graph queries
- projection lag telemetry

### W5 — GitHub adapter
- ingest PR/commit/file events
- map to graph
- PR scope declaration
- collision detection
- merge invalidation

### W6 — Drive/artifact adapter
- artifact registry linkage
- evidence refs only, no heavy media in graph
- artifact lineage + recovery refs

### W7 — Agent SDK / CLI
Commands:
`motion-agent start`
`motion-agent status`
`motion-agent claim`
`motion-agent heartbeat`
`motion-agent context`
`motion-agent checkpoint`
`motion-agent release`
`motion-agent conflicts`

### W8 — Multi-agent adversarial qualification
Test at least:
- 3 agents same repo, disjoint files
- 2 agents same file
- stale fencing writer
- crashed owner takeover
- duplicate event delivery
- event reorder
- event bus disconnect/recovery
- stale ContextPack
- graph projection lag
- GitHub merge while stale agent active
- Drive artifact missing
- schema breaking change
- partial transaction / dispatcher crash

### W9 — Operator dashboard
- live agents
- active leases
- tasks/PRs
- conflicts
- causal graph
- projection lag
- stale sessions
- handoff completeness

### W10 — Authority promotion
Only after evidence:
DESIGN_ONLY → SHADOW → ASSISTED → COORDINATION_AUTHORITY

## 14. SLOs / gates

Targets after production qualification:
- event append p95 < 150ms
- claim/lease decision p95 < 250ms
- graph projection lag p95 < 2s
- zero silent write/write collisions
- zero stale fenced writes accepted
- replay yields same authoritative read models
- graph rebuild hash deterministic
- session resume reconstructs required context without chat history
- 100% completed work linked to evidence/checkpoint

## 15. Non-negotiable invariants

1. Graph is rebuildable projection.
2. Events are append-only.
3. State+event changes use transaction/outbox.
4. Unknown policy fails closed.
5. Duplicate delivery cannot duplicate side effects.
6. Stale fencing tokens cannot mutate authority.
7. Completion requires evidence.
8. Context is versioned and can become stale.
9. Agent identity is canonical and session-specific.
10. GitHub/Drive/DB/Graph ownership is explicit.
11. No autonomous merge/publish/spend authority is introduced by this phase.
12. Existing Phase06 semantics are reused, not forked.

## 16. Definition of Done

Phase07 is VERIFIED only when three independent agents can start from zero chat context, reconstruct a shared state, claim non-conflicting scopes, detect overlapping work before write, exchange durable events, survive one agent crash, resume from checkpoints, rebuild the same COS graph from the event log, and produce evidence that no stale/duplicate operation became authoritative.
