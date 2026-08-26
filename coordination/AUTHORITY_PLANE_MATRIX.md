# MOTION.OS Authority Plane Matrix

Status: CANONICAL BOUNDARY PROPOSAL
Date: 2026-08-26

This document prevents a dangerous ambiguity: `Postgres multi-host coordination authority` does NOT mean `migrate Phase06 render authority from SQLite to Postgres`.

## Authority planes

| Plane | Scope | Current/Target authority | Why |
|---|---|---|---|
| Software | source, schemas, code, plans, executable lineage | GitHub | canonical executable truth |
| Heavy artifacts/recovery | video, images, reports, handoffs, persistent recovery | Drive | durable artifact truth, not transactional bus |
| Phase06 Render Execution | paid render intent, provider job reconciliation, single-host transactional render state | SQLite/WAL `TRANSACTIONAL_SINGLE_HOST_AUTHORITY` on PR #37 | already hardened for one execution host; Postgres migration is explicitly deferred by Phase06 design |
| Phase07 Agent Coordination | concurrent agents/sessions, resource claims, leases, decisions, checkpoints, cross-session context, event log | PostgreSQL/Supabase target | network/multi-host concurrency requires shared transactional authority |
| Coordination wake-up | low-latency notification | Supabase Realtime / PostgreSQL NOTIFY optional | transport only; durable rows remain truth |
| Graph reasoning | dependency/impact/causal/agent/task/content projections | COS Graph Engine | rebuildable deterministic projection/query/reasoning; never transactional source of truth |
| Local test semantics | deterministic contract/adversarial tests | in-memory reference backends | never multi-host authority |
| Bootstrap coordination | human/agent low-frequency messages during W0/W1 | GitHub Issue #43 | temporary bridge only |

## Non-goals of Phase07

Phase07 MUST NOT:
- replace `src/avatar/transactional_store.py` on PR #37 merely because a Postgres coordination DB exists;
- move provider render state into the coordination event log without a separate measured architecture decision;
- weaken Phase06 reconciliation/idempotency/fencing semantics;
- require paid render workers to use a network DB if one host remains the measured topology;
- create a second canonical render-intent state machine.

## Allowed integration

Phase06 may emit coordination events such as:
- `render.intent_authorized`
- `render.provider_acknowledged`
- `render.reconcile_required`
- `render.completed`
- `handoff.sealed`

These events are projections/notifications of Phase06 state transitions. The Phase06 render store remains authoritative for the render aggregate until a future ADR explicitly changes that ownership.

The coordination kernel may use these events to:
- update task/session context;
- wake downstream Studio agents;
- update causal graphs;
- invalidate ContextPacks;
- track evidence/checkpoints.

It MUST NOT accept an event as permission to mutate Phase06 render state outside its authority path.

## Future migration rule

If production topology later needs multiple concurrent render-authority hosts, create a dedicated ADR and evidence campaign. Required trigger/evidence examples:
- multiple independent execution hosts are operationally necessary;
- SQLite file locality becomes a measured bottleneck or availability risk;
- provider reconciliation must be shared across hosts;
- failover RTO/RPO cannot be met by current single-host recovery.

Only then evaluate Postgres for Phase06 render authority. Do not preemptively migrate because Phase07 already uses Postgres.

## Cross-plane transaction rule

There is no fake distributed transaction across GitHub, Drive, Phase06 SQLite and Phase07 Postgres.

Instead use:
- local authoritative transaction;
- immutable outcome event;
- idempotent projection/replication;
- compensation/reconciliation where cross-store side effects fail;
- explicit state such as `PENDING_REPLICA`, `RECONCILE_REQUIRED`, `DEGRADED`, never silent success.

## Canonical principle

> One aggregate has one authority owner at a time. Other planes receive events, evidence references or deterministic projections; they do not silently become co-authorities.
