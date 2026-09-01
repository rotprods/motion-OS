# ADR-008 — Canonical Coordination Event Source and Cognitive-Pause Barrier

Status: PROPOSED FOR RECONCILIATION
Date: 2026-08-27
Baseline: `main@080dfd5c16bc06100edd716eadc770530dc47af2`

## Decision

For coordination aggregates, MOTION.OS SHALL treat the rich Phase07 `CoordinationEvent` + authoritative EventStore implementation as the canonical event-sourced state-transition history **within the authority level actually qualified by that implementation**.

The word “Event Bus” is reserved for transport/delivery. A bus, realtime websocket, GitHub Issue or notification channel MUST NOT become truth merely by delivering an event.

## Current authority boundary

- `InMemoryReferenceEventStore` and `InMemoryReferenceBus`: semantic/reference test oracle only.
- Repository immutable lifecycle JSON (`state/agent_events/`): audit/read projection and repository lifecycle evidence; not a competing coordination aggregate store.
- GitHub Issue #39: bootstrap shared coordination surface; not final transactional authority.
- PostgreSQL/Supabase or equivalent: optional future multi-host coordination authority only after independent-host qualification.
- Phase06 SQLite/WAL: remains authoritative for its single-host render aggregates.
- COS: deterministic projection/query/reasoning; no writeback authority.

## Consequences

1. `STATE.md`, `state/project_state.json`, `coordination/ACTIVE_AGENTS.yaml`, operator dashboards and handoff summaries become generated/verified projections with source watermark/hash.
2. `scripts/agent_event.py` must evolve into an adapter/exporter around canonical event semantics or explicitly remain repository-lifecycle evidence; it cannot silently define a second coordination state machine.
3. Every agent ContextPack records canonical event watermark, relevant aggregate revisions and projection hashes.
4. A stale projection is a failed gate, not harmless documentation drift.
5. State mutation and event publication converge on transactional-outbox semantics in any durable authority implementation.
6. Consumers use durable offsets/idempotent effects and can rebuild projections from event history.

## Cognitive Pause barrier

A cognitive pause is required before changing high-blast-radius shared contracts.

Proposed lifecycle:
- `COGNITIVE_PAUSE_REQUESTED`
- active conflicting agents checkpoint and acknowledge (`COGNITIVE_PAUSE_ACKNOWLEDGED`)
- stale writers are released/fenced according to lease rules
- canonical event/history/lifecycle authorities are reconciled
- projections are rebuilt
- decisions/migrations are recorded
- `COGNITIVE_PAUSE_RELEASED` publishes new watermark + ContextPack revision

No agent may treat chat acknowledgement as the barrier state.

## Non-goals

- no second event bus;
- no automatic Phase06 SQLite→Postgres migration;
- no distributed transaction across GitHub/Drive/render-store/coordination-store;
- no false multi-host claim from in-memory tests;
- no COS write authority.

## Promotion gate

This ADR can become ACCEPTED only after Phase08 verifies:
- one canonical event mapping;
- zero projection drift on clean main;
- replay produces identical read-model hashes;
- lifecycle adapter has deterministic idempotency;
- cognitive-pause collision campaign passes;
- authority labels remain honest when durable backend is absent.
