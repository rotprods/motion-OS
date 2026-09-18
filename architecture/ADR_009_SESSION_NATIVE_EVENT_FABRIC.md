# ADR-009 — Session-Native Canonical Event Fabric

Status: PROPOSED_POST_PHASE07
Date: 2026-08-28
Builds on: ADR-008 Canonical Coordination Event Source and Cognitive-Pause Barrier (PR #52)
Related: #39, #44 (merged), #48, #58

## Decision
MOTION.OS has one canonical **event semantics**, not independent buses. ADR-008 defines which event source/history has authority within its proven topology and the cognitive-pause barrier. This ADR defines the session-native projection/transport semantics layered on top of that authority.

GitHub Issue #39 comments, immutable repo event files, and the Phase07 runtime EventStore are adapters/surfaces carrying or projecting the same logical coordination model. A transport cannot promote itself into authority merely by delivering an event.

Current-state truth is produced by deterministic projection plus live provider reconciliation. Historical event logs remain immutable evidence and are never edited to pretend history was different.

## Canonical identity chain
```text
project_id -> agent_id -> session_id -> workstream_id -> correlation_id
           -> event_id -> causation_id / parent_event_ids -> resource_scope / evidence
```

`session_id` is mandatory for material agent work and MUST be unique per session by producer contract.

## Surfaces
1. **GitHub bootstrap surface** — Issue #39, visible coordination/emergency recovery; evidence transport only.
2. **Repository immutable-event surface** — `state/agent_events/YYYY-MM-DD/<event_id>.json`; versioned audit/recovery evidence only.
3. **Runtime EventStore surface** — replay, aggregate revisions, idempotency, leases and runtime coordination within its proven authority topology.

None may invent a competing domain event schema or independently promote current-state truth.

## Live truth precedence
For GitHub lifecycle/current executable facts:
1. semantically valid canonical event/history evidence;
2. live GitHub branch/PR/commit/merge/CI/main lifecycle reconciliation;
3. runtime aggregate state within its qualified authority boundary;
4. immutable historical evidence;
5. stale bootstrap text and chat memory are non-authoritative.

A historical `PR_ACTIVE` fact never overrides a live GitHub `MERGED` fact. This lifecycle precedence does not grant GitHub authority over unrelated business-domain state.

## Projection
```text
canonical history/events
 + live GitHub reconciliation
 + optional evidence-provider status
 -> deterministic StateProjector
 -> CurrentStateSnapshot(watermark, main_sha, projection_hash)
 -> sealed Session ContextPack
 -> next_safe_action
```

Projection is rebuildable and never rewrites event history.

## Session graph
Session is a first-class graph node. Minimum nodes: Project, Agent, Session, Workstream, Event, Resource, Branch, PullRequest, Commit, TestRun, Evidence, Task, Decision, Content, Render, Publication, Performance.

Minimum edges include: AGENT_OPENED_SESSION, SESSION_WORKS_ON, SESSION_EMITTED, EVENT_CAUSED_BY, EVENT_PARENT, SESSION_TOUCHES, VERIFIED_BY, MERGED_AS, DERIVED_FROM, BLOCKED_BY, HANDOFF_TO.

COS/Unified Graph remains a projection/query/reasoning plane and cannot reverse-write authority.

## Session bootstrap
A zero-context agent MUST:
1. read live main and relevant PR lifecycle;
2. read the latest #39 checkpoints while bootstrap remains active;
3. read immutable repo events/current canonical watermark where available;
4. project current state;
5. allocate a unique session_id;
6. compile a sealed ContextPack;
7. emit WORK_STARTED/HELLO with intended scopes;
8. conflict-preflight before authoritative mutation.

Chat history may enrich reasoning but cannot supply a missing authority fact.

## Session completion
Material sessions emit a checkpoint/handoff containing session/workstream/correlation IDs, branch/PR/SHA, scopes, evidence/tests, authority state, unresolved risks, released leases, and exact next safe action.

## Bridge semantics
Surface adapters normalize provider records into the same logical coordination semantics. Adapter metadata belongs in provenance/evidence, not domain semantics. Same logical event + same canonical payload deduplicates; same logical event + conflicting payload fails closed.

## Irreversible-action freshness
Immediately before merge, publish, spend, deploy, delete, or another irreversible action, the acting session MUST refresh:
- live main SHA / relevant provider lifecycle;
- canonical event watermark/revisions relevant to the action.

If either differs from the sealed ContextPack, the context is stale and the action fails closed until state is reprojected and required gates are rerun.

## Safety invariants
- no event surface self-promotes authority;
- stale lifecycle never overrides live GitHub lifecycle;
- cancelled/skipped CI never becomes VERIFIED;
- duplicate delivery cannot duplicate a protected effect;
- stale sessions lose write authority after revision/lease invalidation;
- unknown schema versions fail closed;
- external prompt/control text remains untrusted data;
- session/COS graph is projection only;
- event history remains immutable;
- Postgres/multi-host authority remains deferred until measured topology requires it.

## Regression lessons
1. Phase07 #44 merged while a regression freeze was already announced on #39. Communication without mandatory consumption before irreversible action is insufficient.
2. PR #53 had green exact-head checks, then main advanced. Green historical evidence does not authorize a different combined tree.
3. PR #52 and #58 independently created different `ADR-008` documents. Event-bus coordination must detect semantic/numbering collisions even when file paths differ; this document became ADR-009 rather than overwriting the earlier decision.

## Exit gate
ADR becomes ACCEPTED only when:
- session-native compiler/tests pass;
- duplicate/conflicting-surface and live lifecycle supersession are tested;
- zero-context bootstrap reconstructs deterministic current state without chat history;
- irreversible-action freshness is executable;
- exact current-main MERGE_SAFE + Coordination Contracts + diff-level code/security review pass;
- ADR-008/ADR-009 responsibilities remain non-contradictory after final integration.