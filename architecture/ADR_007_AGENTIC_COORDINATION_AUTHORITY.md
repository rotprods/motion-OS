# ADR-007 — Multi-Agent Coordination Authority and COS Projection Boundary

Status: PROPOSED
Date: 2026-08-26

## Context
MOTION.OS has multiple concurrent agents operating across independent PRs. Existing persistence is intentionally split: GitHub software truth, Drive artifact/recovery truth, SQLite operational knowledge, graph causal/execution lineage. Phase06 already proves the need for leases, fencing, idempotency, provider reconciliation and multi-host authority.

Cross-session coordination cannot be safely based on chat history, mutable markdown, process-local memory, WebSocket continuity, SQLite shared-file assumptions or a mutable graph projection.

## Decision
Adopt PostgreSQL/Supabase as durable multi-host coordination/event authority.

Use:
- append-only Event Log as causal history;
- transactional Outbox for atomic state/event publication;
- durable Consumer offsets/Inbox for idempotent at-least-once delivery;
- Resource leases with fencing generations;
- revision CAS for mutable aggregates;
- deterministic ContextPacks for bounded cross-session reconstruction;
- COS Graph Engine as a versioned deterministic projection/query/reasoning substrate rebuilt from authoritative sources.

GitHub Issue #43 is the interim low-frequency Coordination Bus before the DB kernel is deployed.

## Rejected alternatives

### Chat history as shared state
Rejected: session-local, incomplete, non-transactional, cannot fence stale writers.

### Drive docs as event bus
Rejected: valuable for recovery/handoffs but poor event semantics, locking, ordering and idempotent consumption.

### SQLite as multi-host authority
Rejected: correct for current single-host Phase06 transactional authority, but not the target for network concurrent hosts.

### Redis/pub-sub only
Rejected as authority: notification without durable causal truth. May be used later as acceleration only.

### WebSocket/Supabase Realtime as truth
Rejected: disconnect/reconnect cannot be allowed to change correctness. Realtime is wake-up transport; durable rows are truth.

### COS Graph Engine as event/state authority
Rejected: would create a hidden second source of truth and weaken replay/rebuild guarantees. COS remains projection/query/reasoning.

### GitHub Issues as permanent runtime event bus
Rejected for high-frequency runtime communication. Retained only as bootstrap cross-session coordination while W1 is not deployed.

## Consequences
Positive:
- stale writers can be fenced;
- three+ agents can coordinate without same-file locking;
- sessions can reconstruct context deterministically;
- events are replayable;
- graph can answer impact/dependency queries without owning truth;
- failures/disconnects have explicit recovery semantics.

Costs:
- Postgres service must be provisioned and secured;
- event schemas require version governance;
- projection lag must be observed;
- ContextPack invalidation becomes a first-class mechanism;
- agents must follow session/claim/checkpoint discipline.

## Safety / security
- default-deny RLS before authority;
- separate runtime identities;
- no provider credentials in events;
- sensitivity labels propagated into graph/context;
- unknown policy/operators fail closed;
- production authority only after adversarial multi-agent qualification.

## Promotion gate
This ADR does not promote a backend merely because tables/code exist. COORDINATION_AUTHORITY requires executed evidence for concurrency, stale fencing, duplicate delivery, replay, crash takeover, context invalidation and graph rebuild determinism.
