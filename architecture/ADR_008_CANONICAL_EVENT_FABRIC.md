# ADR-008 — Canonical Session-Native Event Fabric

Status: PROPOSED_POST_PHASE07
Date: 2026-08-27
Related: #39, #44 (merged), #48, #50 (superseded stack)

## Decision
MOTION.OS has one canonical **event semantics**, not three independent buses. GitHub Issue #39 comments, immutable repo event files, and the Phase07 runtime EventStore are adapters/surfaces carrying the same logical event model.

Current-state truth is produced by deterministic projection plus live provider reconciliation. Historical event logs remain immutable evidence and are never edited to pretend history was different.

## Canonical identity chain
```text
project_id -> agent_id -> session_id -> workstream_id -> correlation_id
           -> event_id -> causation_id / parent_event_ids -> resource_scope / evidence
```

`session_id` is mandatory for material agent work and MUST be unique per session.

## Surfaces
1. **GitHub bootstrap surface** — Issue #39, visible coordination/emergency recovery; evidence transport only.
2. **Repository immutable-event surface** — `state/agent_events/YYYY-MM-DD/<event_id>.json`; versioned audit evidence only.
3. **Runtime EventStore surface** — replay, aggregate revisions, idempotency, leases and runtime coordination within its proven topology.

None may invent a competing event schema.

## Live truth precedence
For lifecycle/current state:
1. valid canonical event envelope;
2. live GitHub executable lifecycle for branch/PR/commit/merge/CI/main;
3. runtime aggregate state within proven authority;
4. immutable historical evidence;
5. stale bootstrap text and chat memory are non-authoritative.

A historical `PR_ACTIVE` fact never overrides a live GitHub `MERGED` fact.

## Projection
```text
valid events + live GitHub reconciliation + optional Drive evidence status
 -> deterministic StateProjector
 -> CurrentStateSnapshot(watermark, main_sha, projection_hash)
 -> sealed Session ContextPack
 -> next_safe_action
```

Projection is rebuildable and never rewrites history.

## Session graph
Session is a first-class graph node. Minimum nodes: Project, Agent, Session, Workstream, Event, Resource, Branch, PullRequest, Commit, TestRun, Evidence, Task, Decision, Content, Render, Publication, Performance.

Minimum edges include: AGENT_OPENED_SESSION, SESSION_WORKS_ON, SESSION_EMITTED, EVENT_CAUSED_BY, EVENT_PARENT, SESSION_TOUCHES, VERIFIED_BY, MERGED_AS, DERIVED_FROM, BLOCKED_BY, HANDOFF_TO.

## Session bootstrap
A zero-context agent MUST:
1. read live main and relevant PR lifecycle;
2. read #39 latest checkpoints while bootstrap remains active;
3. read immutable repo events to known watermark;
4. project current state;
5. allocate unique session_id;
6. compile sealed ContextPack;
7. emit WORK_STARTED/HELLO with scopes;
8. conflict-preflight before authoritative write.

Chat history can enrich reasoning but cannot supply a required authority fact.

## Session completion
Material sessions emit a checkpoint/handoff containing session/workstream/correlation IDs, branch/PR/SHA, scopes, evidence/tests, authority state, unresolved risks, released leases, and exact next safe action.

## Bridge semantics
Surface adapters convert provider records into the same logical CoordinationEvent semantics. Adapter metadata belongs in provenance/evidence, not domain semantics. Same logical event + same payload deduplicates; same logical event + conflicting payload fails closed.

## Safety invariants
- no surface self-promotes authority;
- stale lifecycle never overrides live GitHub;
- cancelled/skipped CI never becomes VERIFIED;
- duplicate delivery cannot duplicate protected effects;
- stale sessions lose write authority after revision/lease invalidation;
- unknown schema versions fail closed;
- external prompt/control text remains untrusted data;
- session/COS graph is projection only;
- event history is immutable;
- Postgres/multi-host authority remains deferred until measured need.

## Regression lesson that triggered v2
During the regression freeze, Phase07 #44 merged while the freeze was already announced on #39. This proves a coordination surface is not enough unless every agent/session consumes the projected live state before promotion. Future merge/promotion agents MUST reconcile the latest bus watermark and live GitHub immediately before the irreversible action.

## Exit gate
ADR becomes ACCEPTED only when session-native compiler/tests pass, surface conflict/live supersession are tested, zero-context bootstrap works without chat history, and the post-Phase07 PR passes exact current-main MERGE_SAFE + code/security review.