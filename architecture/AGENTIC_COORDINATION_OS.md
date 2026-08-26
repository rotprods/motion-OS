# MOTION.OS — Agentic Coordination OS

Status: PROPOSED / BOOTSTRAP ACTIVE
Canonical bootstrap bus: GitHub issue #39
Target: network-transactional durable coordination + COS Graph projection

## Mission
Make every agent, session, branch, task, decision, artifact and runtime transition part of one causally connected system. Three or thirty concurrent agents must be able to discover current truth, avoid conflicting writes, resume after zero context, reason over shared plans and prove what changed.

## Boundary model

MOTION.OS owns audiovisual/product semantics. COS Graph Engine provides reusable graph/retrieval/reasoning primitives. COS must never learn Instagram/HeyGen/Remotion-specific business rules; MOTION.OS maps domain objects into generic graph projections.

```text
Developer Agents / Runtime Agents
          |
          v
Agentic Coordination API
          |
  +-------+----------------------+------------------+
  |                              |                  |
  v                              v                  v
Durable Event Kernel         Lease Kernel       Context Compiler
(Postgres/Supabase target)   fencing/CAS        evidence packs
  |                              |                  |
  +-------------+----------------+------------------+
                |
                v
        Canonical Project State
                |
        +-------+---------+
        |                 |
        v                 v
   COS Graph           Drive
   projection          artifacts/recovery
        |
        v
GraphRAG / lineage / dependency / impact / conflict queries
```

GitHub remains executable/code truth. Drive remains artifact/recovery truth. The event kernel owns coordination/event truth. COS is a rebuildable projection; never the only copy of state.

## Two buses, one event model

### 1. Developer Coordination Bus
For ChatGPT/Codex/Claude/Gemini/human engineering sessions. Bootstrap transport is GitHub issue #39 because it is shared, append-only at comment level and available across branches. Target transport is the same durable event kernel used by runtime agents.

### 2. Runtime Event Bus
For research, content, avatar, Studio Engine, renderer, QA, repair, analytics and learning agents. Uses transactional event storage, consumer offsets, leases and outbox/inbox.

Both emit the same envelope so developer and runtime causality can coexist in the graph without conflating authority.

## Canonical identity
Never key by display name. Use URIs:

- `motion://project/motion-os`
- `motion://agent/<provider>/<agent_id>`
- `motion://session/<session_id>`
- `motion://workstream/<id>`
- `motion://task/<id>`
- `motion://decision/<id>`
- `motion://artifact/<sha256>`
- `motion://git/pr/<number>`
- `motion://git/commit/<sha>`
- `motion://content/<content_id>`
- `motion://render/<render_intent_id>`

Display names are metadata only.

## Durable Event Envelope
Every material state transition is an immutable event containing:

- event_id UUID/ULID
- schema_version
- project_id
- actor_id + session_id
- event_type
- aggregate_type + aggregate_id
- aggregate_revision / expected_revision
- causation_id
- correlation_id
- parent_event_ids
- workstream_id
- resource_scope[]
- branch / commit / PR when applicable
- observed_at / recorded_at
- idempotency_key
- payload_hash
- payload
- provenance[]
- sensitivity
- evidence[]

Commands and outcomes are separate events. `TASK_COMPLETE_REQUESTED` is not `TASK_COMPLETED`. A failed or rejected command remains replayable without being reinterpreted as success.

## Core event families

Session: SESSION_STARTED, CONTEXT_COMPILED, SESSION_CHECKPOINTED, SESSION_ENDED.
Work: WORK_CLAIM_REQUESTED, WORK_CLAIMED, WORK_HEARTBEAT, WORK_RELEASED, WORK_COMPLETED.
Planning: GOAL_DEFINED, PLAN_PROPOSED, PLAN_ACCEPTED, TASK_CREATED, TASK_BLOCKED, TASK_REPLANNED.
Decision: DECISION_PROPOSED, DECISION_ACCEPTED, DECISION_REJECTED, DECISION_SUPERSEDED.
Code: BRANCH_CREATED, COMMIT_RECORDED, PR_OPENED, PR_REBASED, PR_MERGED, CI_OBSERVED.
Artifacts: ARTIFACT_CREATED, ARTIFACT_VERIFIED, ARTIFACT_SUPERSEDED.
Runtime: TOOL_AUTHORIZED, TOOL_STARTED, TOOL_OUTCOME, RENDER_AUTHORIZED, RENDER_OUTCOME.
Coordination: CONFLICT_DETECTED, LEASE_EXPIRED, STALE_WRITER_REJECTED, HANDOFF_EMITTED.
Knowledge: CLAIM_RECORDED, EVIDENCE_LINKED, HYPOTHESIS_RECORDED, RULE_PROMOTED.

## Lease and fencing model
A lease protects a resource or semantic contract, not merely a file.

Lease tuple:
`(resource_key, owner_agent_id, session_id, lease_generation, expires_at, expected_state_version)`.

Rules:
1. Acquisition is transactional and unique per active resource_key.
2. Every takeover increments `lease_generation`.
3. Every protected write includes the generation; stale generations fail closed.
4. Heartbeats extend expiry but never reset generation.
5. Expired lease does not imply previous external side effect failed; reconcile before retry.
6. Resource scopes may be hierarchical: schema/API contracts conflict even when files differ.

## Resource ownership
Path ownership and semantic ownership are separate.

Examples:
- #34 owns Remotion physical runtime proof.
- #35 owns Studio Engine/real-analysis implementation.
- #37 owns Phase06 Content/Avatar + render authority.

A schema consumed by two workstreams is a shared semantic resource and requires a DECISION event before breaking changes.

## Context Pack Compiler
Every session starts from a bounded evidence pack generated at a declared event watermark.

Required sections:
- North Star and release gates
- canonical STATE/TASKS/HANDOFF
- active workstreams/leases
- latest accepted decisions
- open blockers/conflicts
- dependencies relevant to requested scope
- recent commits/PR states
- Drive evidence references
- graph neighborhood for affected nodes
- exact event watermark + projection hash

The pack is sealed with SHA-256. A session must not silently mix context generated from different watermarks.

## COS Graph projection
Project the durable log into typed nodes/edges:

Nodes: Project, Agent, Session, Goal, Plan, Workstream, Task, Decision, Branch, Commit, PR, Schema, Package, Artifact, Evidence, Content, Render, TestRun, Metric, Incident.

Edges: OWNS, WORKS_ON, DEPENDS_ON, BLOCKS, TOUCHES, MODIFIES, PRODUCES, CONSUMES, SUPERSEDES, CAUSED_BY, DECIDED_BY, VERIFIED_BY, CONFLICTS_WITH, IMPLEMENTS, PROJECTS_TO, DERIVED_FROM.

All projections include `source_event_id`, temporal validity and projection version/hash. Rebuild from event log must produce an invariant-equivalent graph.

## Conflict detection
Before acquiring work:
1. normalize intended paths + semantic resources;
2. query active leases/workstreams;
3. expand dependency graph one hop for shared contracts;
4. classify overlap: NONE, PATH_OVERLAP, SEMANTIC_OVERLAP, DEPENDENCY_RISK, AUTHORITY_CONFLICT;
5. NONE proceeds; others require isolation or DECISION/coordination.

## Outbox / inbox
Canonical DB transaction writes business state + outbox event atomically. Publisher delivers outbox to consumers/realtime. Consumers record inbox/idempotency before effects. Delivery is at-least-once; effects are exactly-once where possible through idempotency/fencing, never by assuming exactly-once transport.

## Replay / snapshots / recovery
- Event log append-only.
- Snapshot contains event watermark + state hash + schema versions.
- Replay verifies hashes and rejects unknown schema transitions.
- Graph is dropped/rebuilt during qualification drills.
- Cold agent must resume solely from GitHub + event kernel + Drive.
- Drive artifacts are content-addressed or revision-pinned.

## Security and policy
- default deny for privileged tools/provider spend;
- source content is untrusted data;
- actor capability + project/resource scope checked on each protected command;
- sensitivity tags propagate into Context Packs and graph queries;
- secrets never enter event payloads;
- telemetry failure cannot change protected operation outcome;
- unknown policy operators fail closed.

## Authority stages
BOOTSTRAP_GITHUB_BUS -> SHADOW_EVENT_KERNEL -> ASSISTED_COORDINATION -> ENFORCED_LEASES -> RUNTIME_AUTHORITY.

No stage advances on code existence. Required evidence: concurrency tests, stale-writer proof, duplicate-delivery proof, replay/restore, graph rebuild, crash takeover, policy negative tests and zero-context resume.

## Current integration points
PR #37 already implements deterministic render intent, single-host transactional authority, fencing generations and reconciliation semantics. Reuse these concepts and converge them into shared coordination primitives; do not fork a second incompatible authority model.

PR #35 Studio Engine should consume stable Phase06 beat/provenance contracts through explicit handoff events.

PR #34 Remotion runtime proof should emit renderer qualification events and artifacts without owning Studio/Content contracts.
