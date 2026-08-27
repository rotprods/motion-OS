# MOTION.OS Agentic Coordination — 20D Scorecard

Scoring model:
- **Build** = design/implementation/static-review maturity.
- **Assurance** = executed evidence maturity.
- **Authority** = `min(Build, Assurance)`.

A dimension is never promoted by file count or architectural sophistication alone. Scores below describe the **local/reference + shadow coordination system** unless explicitly marked multi-host. They do not imply distributed transactional authority.

Snapshot: 2026-08-27 — verified through PR #44 head `bc0439326612cad8ff461e9030978296293433f9`.

Evidence gates on this wave:
- CI Python 3.11/3.12: SUCCESS
- physical analysis-runtime: SUCCESS
- Coordination Contracts Python 3.11/3.12: SUCCESS
- Security Baseline: SUCCESS
- Repo Health: SUCCESS
- Runtime Smoke: SUCCESS
- Remotion Runtime: SUCCESS
- predecessor PR #40: CLOSED_UNMERGED / SUPERSEDED

| # | Dimension | Build | Assurance | Authority | Current evidence / remaining gap |
|---|---|---:|---:|---:|---|
| D01 | Truth ownership | 9.5 | 9.0 | 9.0 | Git/Drive/Phase06 SQLite/coordination/COS boundaries explicit and exercised; multi-host authority intentionally deferred |
| D02 | Canonical identity | 9.2 | 8.5 | 8.5 | canonical motion:// identities in events/context/planning/tests; live provider agent registration still incomplete |
| D03 | Event state semantics | 9.2 | 8.7 | 8.7 | EventStore revisions, heads, idempotency, watermark and snapshots pass reference qualification; durable network store is P20 |
| D04 | Event idempotency | 9.4 | 9.0 | 9.0 | duplicate event/idempotency-key conflict and inbox effect dedupe tested |
| D05 | Ordering / causality | 9.1 | 8.8 | 8.8 | aggregate revisions, causation, parent events, correlation and replay-order rejection tested |
| D06 | Multi-host concurrency | 7.5 | 1.0 | 1.0 | deliberately not claimed; SQL candidate exists but no network contention authority campaign |
| D07 | Leases / fencing | 9.5 | 9.0 | 9.0 | READ/WRITE/EXCLUSIVE semantics, 500 takeovers, 100 live competitors and stale-generation rejection qualified locally |
| D08 | CAS / stale writer control | 9.4 | 9.0 | 9.0 | stale expected revisions and stale fencing generations fail closed in reference campaign |
| D09 | Recovery / replay | 9.0 | 8.4 | 8.4 | cold events→state→graph→COS bundle hash equivalence tested; full GitHub+Drive cold-agent drill pending |
| D10 | Cross-session ContextPack | 9.5 | 8.8 | 8.8 | deterministic seal, semantic ordering, lifecycle/main/source/projection invalidation and live-context CLI tested |
| D11 | Graph correctness / rebuild | 9.3 | 8.7 | 8.7 | deterministic projector + pinned COS shadow bundle/hash; actual COS backend load/query equivalence pending |
| D12 | Provenance / evidence | 9.2 | 8.2 | 8.2 | structured provenance, payload/event hashes and revision-pinned EvidenceManifest tested; live Drive revision ingestion pending |
| D13 | Security / policy | 8.9 | 8.2 | 8.2 | Security Baseline green + default-deny capability/resource/sensitivity negative tests; service identity enforcement pending |
| D14 | Isolation / sensitivity | 8.8 | 8.0 | 8.0 | sensitivity ceilings/default deny tested; context redaction/prompt-injection campaign still pending |
| D15 | Outbox / delivery recovery | 9.0 | 7.8 | 7.8 | duplicate effect, unknown-event quarantine and retry-after-handler-repair tested; durable dispatcher crash/restart pending |
| D16 | GitHub integration | 9.3 | 8.7 | 8.7 | canonical Bus #39, Epic #41, PR lifecycle states/revision hash and live reconciliation tested; direct ingestion daemon pending |
| D17 | Drive integration | 8.2 | 5.8 | 5.8 | canonical Drive11 + revision-pinned provider-neutral evidence contract; live checkpoint write hit connector 404 and requires retry |
| D18 | Contract governance | 9.5 | 8.8 | 8.8 | #40/#44 real duplicate-architecture incident reconciled, canonical controls consolidated, semantic conflict engine tested |
| D19 | Testing / adversarial qualification | 9.4 | 9.0 | 9.0 | dedicated Coordination Contracts gate, 3-agent crash/takeover test, 500 takeover + 100 contention campaign, full CI green |
| D20 | Operator DX / observability | 8.5 | 7.6 | 7.6 | README/protocol/CLI/SDK/health metrics exist; status console and tracing exporter pending |

Approximate means:
- **Build:** 9.0/10
- **Assurance:** 7.9/10
- **Authority:** 7.9/10

The low D06 score is intentional: it prevents local/reference evidence from being misrepresented as multi-host authority.

## Promotion rules
### Local/reference coordination authority
May advance toward `ASSISTED_COORDINATION` when the relevant dimensions for the requested operation are >=8.5 Authority and the operation remains within the proven local/bootstrap boundary.

### Multi-host coordination authority
Must remain disabled until D06 and all distributed variants of D03/D07/D08/D09/D13/D15 are >=9.0 with real network/process evidence. Postgres or another transactional backend is an implementation option at P20, not a prerequisite for local engineering.

## Critical path from current state
1. P8 live Drive evidence/revision ingestion and retry the connector-backed checkpoint.
2. P11 end-to-end Phase06 Content/Viral → Studio → publication/performance graph qualification with #37.
3. P13 trace/correlation exporter and operator health view.
4. P14 context redaction, prompt-injection/untrusted-source and capability-boundary adversarial campaign.
5. P15 broader randomized multi-agent scenario matrix: contract drift, PR close/merge, context invalidation and crash recovery.
6. P16 full zero-context recovery using GitHub + Drive + event history, no chat transcript.
7. P18 operator `status/next/conflicts` UX.
8. P19 final 20D gauntlet and gap closure.
9. P20 only if real multi-host concurrent authority is required: select backend, deploy least privilege, then rerun distributed qualification rather than inheriting local scores.
