# ADR-008 — Canonical Session-Native Event Fabric

Status: PROPOSED_FOR_PHASE07
Date: 2026-08-27
Related: #39, #44, #48

## Decision
MOTION.OS has one canonical **event semantics**, not three independent buses. GitHub Issue #39 comments, immutable repo event files, and the Phase07 runtime EventStore are adapters/surfaces carrying the same logical event model.

Current-state truth is produced by deterministic projection plus live provider reconciliation. Historical event logs remain immutable evidence and are never edited to pretend history was different.

## Canonical identity chain

```text
project_id
  -> agent_id
    -> session_id
      -> workstream_id
        -> correlation_id
          -> event_id
            -> causation_id / parent_event_ids
              -> resource_scope / lease / evidence
```

`session_id` is mandatory for material agent work. A new session must never reuse a previous session identifier.

## Surfaces

### 1. GitHub bootstrap surface
Purpose: human/agent-visible coordination and emergency recovery.
Authority: evidence transport only.
Canonical object: Issue #39 until Phase07 bootstrap is retired.

### 2. Repository immutable-event surface
Purpose: versioned audit/recovery evidence associated with executable truth.
Path: `state/agent_events/YYYY-MM-DD/<event_id>.json`.
Authority: evidence transport only.

### 3. Runtime EventStore surface
Purpose: replay, aggregate revisions, idempotency, leases, consumer semantics and current runtime coordination.
Authority: runtime coordination within the backend's proven topology only.

None of the surfaces may invent a competing event schema.

## Live truth precedence
When projecting lifecycle/current state:

1. cryptographically/semantically valid event envelope;
2. live GitHub executable state for branch/PR/commit/merge/CI lifecycle;
3. runtime aggregate state where the backend has authority;
4. immutable historical evidence;
5. stale bootstrap text and chat memory are non-authoritative.

A historical event saying `PR_ACTIVE` does not override a later live GitHub `MERGED` state.

## Projection rule

```text
all valid events
    + live GitHub reconciliation
    + optional Drive evidence status
       -> deterministic StateProjector
       -> CurrentStateSnapshot(watermark, main_sha, projection_hash)
       -> sealed SessionContextPack
       -> next_safe_action
```

Projection is rebuildable. It must not mutate event history.

## Session graph
Every session is a first-class graph node.

Minimum nodes:
- Project
- Agent
- Session
- Workstream
- Correlation
- Event
- Resource
- Branch
- PullRequest
- Commit
- TestRun
- Evidence
- Task
- Decision
- Content
- Render
- Publication
- Performance

Minimum relationships:
- AGENT_OPENED_SESSION
- SESSION_WORKS_ON
- SESSION_EMITTED
- EVENT_CAUSED_BY
- EVENT_PARENT
- SESSION_CLAIMS
- SESSION_TOUCHES
- SESSION_PRODUCED
- VERIFIED_BY
- MERGED_AS
- DERIVED_FROM
- BLOCKED_BY
- HANDOFF_TO

## Session bootstrap contract
A zero-context agent MUST:
1. read live `main` and relevant PR lifecycle;
2. read canonical Bus #39 latest checkpoints while bootstrap remains active;
3. read immutable repo events to the current known watermark;
4. project current state;
5. allocate a unique `session_id`;
6. compile a sealed ContextPack;
7. emit `WORK_STARTED`/`HELLO` with intended resource scopes;
8. run conflict preflight before authoritative write.

Chat history may enrich reasoning but cannot supply a missing authority fact.

## Session completion contract
Before ending material work the agent MUST emit a checkpoint/handoff containing:
- session_id
- workstream_id
- correlation_id
- branch/PR/current SHA
- exact resource scopes touched
- evidence/tests
- authority state: PROPOSED / IMPLEMENTED / EXECUTED / VERIFIED
- unresolved risks/blockers
- released leases
- exact next safe action

## Bridge semantics
Adapters convert surface-specific records into `CoordinationEvent`-compatible facts. Adapter metadata belongs in provenance/evidence, not in domain semantics.

The same logical event delivered by two surfaces MUST deduplicate by canonical logical identity/idempotency key. A conflicting duplicate with different payload MUST fail closed.

## Safety invariants
1. no event surface can self-promote its own authority;
2. no stale lifecycle event overrides live GitHub state;
3. cancelled/skipped CI never becomes VERIFIED;
4. duplicate delivery never duplicates a protected effect;
5. a stale session may analyze but cannot write after revision/lease invalidation;
6. unknown schema versions fail closed;
7. prompt-injection text from external sources remains untrusted data;
8. session graph/COS projections are read/query planes, never reverse write authority;
9. event history remains immutable;
10. Postgres/multi-host authority remains deferred until measured topology requires it.

## Migration
Phase07 will provide adapters/projectors so existing #39 records and repo events remain useful evidence. They are not rewritten into fake canonical history. New agents should emit the canonical fields immediately.

## Exit gate
ADR becomes ACCEPTED only when:
- session-native compiler/tests pass;
- duplicate/conflicting-surface events are tested;
- live GitHub supersession is tested;
- zero-context session bootstrap works without chat history;
- #39, repo events and runtime EventStore are documented as adapters to one semantic event model;
- Phase07 exact combined-head gates pass.