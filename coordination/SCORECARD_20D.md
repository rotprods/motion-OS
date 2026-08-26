# MOTION.OS Agentic Coordination — 20D Scorecard

Scoring model:
- Build = design/implementation/static-review maturity
- Assurance = executed evidence maturity
- Authority = min(Build, Assurance)

A dimension is never promoted by file count or architectural sophistication alone.

Snapshot: 2026-08-26, Phase07 W0/W1 pre-deployment.

| # | Dimension | Build | Assurance | Authority | Current evidence / gap |
|---|---|---:|---:|---:|---|
| D01 | Truth ownership | 9.0 | 6.0 | 6.0 | Git/Drive/SQLite/Postgres/COS boundary explicit; no live DB proof yet |
| D02 | Canonical identity | 8.0 | 4.0 | 4.0 | URI model/spec exists; active agents still bootstrap `runtime: unknown` |
| D03 | Event durability | 7.5 | 1.0 | 1.0 | append-only schema + SQL function exist; not deployed |
| D04 | Event idempotency | 8.5 | 5.0 | 5.0 | reference bus tests pass on prior CI; Postgres duplicate proof pending |
| D05 | Ordering / causality | 7.5 | 3.0 | 3.0 | event envelope + causal/correlation IDs + ordered cursor designed; DB replay pending |
| D06 | Multi-host concurrency | 7.0 | 0.5 | 0.5 | DB functions designed; no live concurrent-host test |
| D07 | Leases / fencing | 9.0 | 5.0 | 5.0 | reference semantics tested; atomic Postgres functions not executed |
| D08 | CAS / stale writer control | 8.5 | 5.0 | 5.0 | reference CAS tested; integration with authoritative aggregates pending |
| D09 | Recovery / replay | 7.0 | 2.0 | 2.0 | deterministic event/projector model exists; crash/replay campaign pending |
| D10 | Cross-session ContextPack | 9.0 | 5.0 | 5.0 | deterministic seal + stale invalidation tests; live compiler inputs pending |
| D11 | Graph correctness / rebuild | 8.5 | 5.0 | 5.0 | deterministic local projector tests; concrete COS shadow adapter pending |
| D12 | Provenance / evidence | 8.5 | 5.0 | 5.0 | event SHA-256, evidence refs, projection hash; end-to-end proof pending |
| D13 | Security / policy | 7.0 | 1.5 | 1.5 | default-deny RLS intent; no policies/service identities/live advisor run |
| D14 | Isolation / sensitivity | 7.0 | 2.0 | 2.0 | sensitivity envelope + COS contract; enforcement pending |
| D15 | Outbox / delivery recovery | 8.5 | 1.0 | 1.0 | multi-dispatcher leased outbox SQL designed; not executed |
| D16 | GitHub integration | 8.0 | 7.0 | 7.0 | Issue #43 bus + PR #34/#35/#37 links live; automatic ingestion pending |
| D17 | Drive integration | 7.5 | 6.0 | 6.0 | persistent `09_AGENTIC_COORDINATION` live; automated drift/recovery pending |
| D18 | Contract governance | 9.0 | 6.0 | 6.0 | conflict matrix + contract claim protocol materialized; enforcement pending |
| D19 | Testing / adversarial qualification | 7.5 | 5.0 | 5.0 | Python 3.11/3.12 previous head green; DB/concurrency/failure injection pending |
| D20 | Operator DX / observability | 5.5 | 2.0 | 2.0 | README_FIRST + bus + docs; CLI/dashboard/SLO telemetry pending |

Approximate current means:
- Build: 7.9/10
- Assurance: 3.6/10
- Authority: 3.6/10

## Promotion rule
No `COORDINATION_AUTHORITY` until all critical dimensions D03–D15 and D19 are >=9.0 Authority with machine-verifiable evidence.

## Critical path to 9+
1. Dedicated Postgres environment + RLS/service identities.
2. Real transaction/idempotency/outbox tests.
3. 3-host contention + lease takeover + stale writer tests.
4. Durable consumer restart/replay tests.
5. Concrete COS shadow adapter + deterministic rebuild/equivalence proof.
6. ContextPack compilation from live GitHub/Drive/DB graph and stale invalidation after merge.
7. Security advisor + negative authorization tests.
8. Failure injection: dispatcher crash, DB reconnect, duplicate publish, delayed/reordered delivery, COS outage, Drive missing artifact.
9. Zero-context recovery drill with a fresh agent.
10. Operator observability and explicit SLO evidence.
