# ADR-007 — Multi-Agent Coordination Authority and COS Projection Boundary

Status: ACCEPTED — LOCAL/REFERENCE; MULTI-HOST BACKEND DEFERRED
Date: 2026-08-26
Last reconciled: 2026-08-27

## Context
MOTION.OS operates multiple concurrent agents and workstreams. Persistence is intentionally split: GitHub is executable truth; Drive is artifact/evidence/recovery truth when available; Phase06 SQLite/WAL is transactional single-host render authority; the Phase07 coordination kernel provides locally qualified event/revision/lease/context semantics; COS is a derived graph projection.

Cross-session coordination cannot safely depend on chat history, mutable markdown alone, process-local memory, WebSocket continuity, SQLite shared-file assumptions across hosts, or a mutable graph projection.

## Decision
Adopt the Phase07 coordination contracts as the canonical **local/reference coordination model** now:
- append-only event semantics and aggregate revisions;
- idempotent command/outcome and inbox processing;
- resource claims, leases, fencing and CAS semantics;
- deterministic ContextPacks and recovery bundles;
- explicit policy/trust boundaries;
- deterministic COS projection/query/reasoning with no reverse write authority;
- GitHub Issue #39 plus immutable repository agent events as the current low-frequency cross-session coordination/control trail.

A durable network transactional backend such as PostgreSQL/Supabase is an **optional P20 promotion**, required only when MOTION.OS needs simultaneous independent-host write authority. No backend is promoted merely because SQL/schema/adapter code exists.

If P20 is activated, the durable backend must provide:
- append-only Event Log as causal history;
- transactional Outbox for atomic state/event publication;
- durable Consumer offsets/Inbox for idempotent at-least-once delivery;
- resource leases with fencing generations;
- revision CAS for mutable aggregates;
- least-privilege service identities and default-deny authorization;
- replay/recovery evidence across real independent processes/hosts.

## Authority boundaries
- **GitHub/main** — executable software/config truth and merge lifecycle.
- **MERGE_SAFE** — clean-runner merge authority for repository promotion.
- **Issue #39 + immutable agent events** — bootstrap/low-frequency coordination and audit trail; not high-frequency runtime truth.
- **Phase06 SQLite/WAL** — transactional single-host render execution authority only.
- **Phase07 reference stores** — local/reference semantics and qualification only.
- **Drive** — artifact/evidence/recovery plane when provider access is healthy; provider failure is explicit, never synthesized.
- **COS Graph Engine** — rebuildable projection/query/reasoning plane only; never authoritative writeback.
- **PostgreSQL/Supabase or equivalent** — optional future multi-host authority only after P20 qualification.

## Rejected authority shortcuts
### Chat history as shared state
Rejected: session-local, incomplete, non-transactional and unable to fence stale writers.

### Drive documents as event bus
Rejected: valuable for evidence/recovery but unsuitable for ordering, locking and high-frequency idempotent consumption.

### SQLite as multi-host authority
Rejected: valid for current Phase06 single-host transactions, not a network coordination authority.

### Redis/pub-sub or WebSocket/Realtime as truth
Rejected as authority: notification continuity must not determine correctness. They may accelerate wake-up/delivery around durable state.

### COS as event/state authority
Rejected: would create a hidden second source of truth and break deterministic rebuild guarantees.

### GitHub Issues as permanent high-frequency runtime bus
Rejected. Issue #39 is retained for human/agent checkpoints and bootstrap coordination only.

## Consequences
Positive:
- local agents can reason about collisions, stale writers, context drift and replay with one canonical contract;
- Phase06 authority remains isolated and cannot be silently replaced;
- merge-safe repository promotion and Phase07 coordination semantics compose rather than compete;
- COS can answer dependency/impact/lineage queries without owning truth;
- moving to real multi-host authority later has an explicit qualification boundary.

Costs / remaining gaps:
- Drive live evidence bridge depends on provider availability;
- independent-host transactional authority is intentionally not claimed;
- a future P20 deployment requires service identities, RLS/policy, outbox/inbox durability and real failure-injection tests.

## Safety / security
- default deny for unknown capabilities/operations/resources/sensitivity;
- no provider credentials in events/context packs;
- untrusted external context remains data and is redacted/flagged before use;
- stale revisions/fencing tokens fail closed;
- COS cannot authorize writes;
- multi-host authority requires real network/process evidence, not local simulations.

## Promotion gate
`LOCAL_REFERENCE_VERIFIED` and `ASSISTED_COORDINATION` may be supported by current local/reference evidence. `MULTI_HOST_AUTHORITY` remains disabled until D06 and the distributed variants of durability, fencing, CAS, recovery, security and delivery score >=9 with machine-verifiable independent-host evidence.
