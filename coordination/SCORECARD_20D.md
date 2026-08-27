# MOTION.OS Agentic Coordination — 20D Scorecard

Scoring model:
- **Build** = design/implementation/static-review maturity.
- **Assurance** = executed evidence maturity.
- **Authority** = `min(Build, Assurance)`.

A dimension is never promoted by file count or architectural sophistication alone. Scores describe the qualified **local/reference + shadow + repository-merge** system unless explicitly marked multi-host. They do not imply distributed transactional authority.

Snapshot: 2026-08-27 — final PR #44 promotion candidate after Phase06 #37 and local-first/MERGE_SAFE #46 landed on main.

Current evidence already executed during this release wave:
- Phase06 #37 exact-head CI Python 3.11/3.12: SUCCESS
- Phase06 physical analysis-runtime: SUCCESS
- Phase06 Security / Repo Health / Runtime Smoke / Remotion Runtime: SUCCESS
- Phase06 #37: MERGED to main as `6ef91a9fe092387b888d25da67006d68f455d229`
- MERGE_SAFE train #46: MERGED and independently recorded as verified on main
- Phase07 Coordination Contracts Python 3.11/3.12: repeated SUCCESS on reconciled candidates
- Phase07 quick/full tests: repeated SUCCESS on Python 3.11/3.12 before final documentation reconciliation
- Phase07 physical analysis, Remotion and dependency security: SUCCESS on the reconciled candidate before this final canonical-doc refresh
- predecessor #40: CLOSED_UNMERGED / SUPERSEDED
- unified graph deterministic enrichment + contradiction rejection: QUALIFIED
- 3-agent crash/takeover + 500 takeover rounds + 100 competitor campaign: QUALIFIED locally
- untrusted-context redaction/control-instruction detection: QUALIFIED locally
- sealed zero-chat recovery bundle + drift detection: QUALIFIED locally
- operator status/health/next/conflicts/trace surface: QUALIFIED locally

The **final combined-head MERGE_SAFE run after this documentation refresh remains the release gate**. Scores below intentionally do not upgrade multi-host or live-Drive authority.

| # | Dimension | Build | Assurance | Authority | Current evidence / remaining gap |
|---|---|---:|---:|---:|---|
| D01 | Truth ownership | 9.7 | 9.3 | 9.3 | GitHub/main + MERGE_SAFE, Drive evidence plane, Phase06 SQLite single-host authority, Phase07 local/reference state and COS boundaries are explicit and reconciled |
| D02 | Canonical identity | 9.5 | 9.1 | 9.1 | canonical motion:// agent/session/work/content/resource identities across events, context, planning, lineage and tests |
| D03 | Event state semantics | 9.4 | 9.0 | 9.0 | revisions, expected revisions, heads, idempotency, watermark, snapshots and replay pass reference qualification; distributed durability is P20 |
| D04 | Event idempotency | 9.5 | 9.2 | 9.2 | duplicate event/idempotency conflicts and inbox effect dedupe are tested fail-closed |
| D05 | Ordering / causality | 9.4 | 9.1 | 9.1 | aggregate revision order, parent/causation/correlation and deterministic replay semantics qualified |
| D06 | Multi-host concurrency | 7.5 | 1.0 | 1.0 | intentionally unpromoted; no independent-host transactional authority campaign has been executed |
| D07 | Leases / fencing | 9.6 | 9.3 | 9.3 | READ/WRITE/EXCLUSIVE semantics, crash takeover, 500 takeovers, 100 competitors and stale-generation rejection qualified locally |
| D08 | CAS / stale writer control | 9.5 | 9.3 | 9.3 | stale expected revisions and stale fencing generations reject deterministically in reference campaigns |
| D09 | Recovery / replay | 9.4 | 9.0 | 9.0 | events→state→coordination graph→unified graph→COS hashing plus sealed recovery-source drift checks; live Drive leg unavailable |
| D10 | Cross-session ContextPack | 9.6 | 9.2 | 9.2 | deterministic seal/order, lifecycle/main/source/projection invalidation and live lifecycle reconciliation tested |
| D11 | Unified graph correctness / rebuild | 9.6 | 9.2 | 9.2 | coordination + Phase06 content lineage share canonical content identity; compatible properties enrich recursively, contradictions fail closed; COS remains one-way shadow |
| D12 | Provenance / evidence | 9.5 | 8.8 | 8.8 | structured provenance, payload/event hashes, Phase06 PRV/MNF preservation and revision-pinned EvidenceManifest; live Drive revision read/write unavailable |
| D13 | Security / policy | 9.4 | 9.2 | 9.2 | dependency security green, default-deny capability/resource/sensitivity policy, untrusted-context envelope, secret redaction and authority-spoof negative tests |
| D14 | Isolation / sensitivity | 9.3 | 9.1 | 9.1 | sensitivity ceilings/default deny plus external control-instruction detection and non-self-promoting trust envelope qualified |
| D15 | Delivery / outbox recovery semantics | 9.2 | 8.4 | 8.4 | duplicate logical effects, unknown/poison quarantine and retry-after-repair tested; durable distributed dispatcher crash/restart is P20 |
| D16 | GitHub / merge lifecycle integration | 9.7 | 9.3 | 9.3 | #39/#41 control objects, PR lifecycle reconciliation, immutable agent events, local-first verification and MERGE_SAFE serial promotion are integrated |
| D17 | Drive integration | 8.3 | 5.8 | 5.8 | provider-neutral evidence/recovery contracts exist; live connector returned provider errors, so no live authority/evidence is claimed |
| D18 | Contract governance / collision control | 9.7 | 9.3 | 9.3 | #40/#44 duplicate architecture reconciled, #37 authority consumed read-only, semantic/path/dependency/authority conflict classification and merge-train race handled explicitly |
| D19 | Testing / adversarial qualification | 9.7 | 9.5 | 9.5 | Coordination Contracts, full tests, MERGE_SAFE subgates, 3-agent crash/takeover, deterministic contention campaign, trust/recovery/unified-graph negative tests |
| D20 | Operator DX / observability | 9.4 | 9.1 | 9.1 | protocol/SDK/CLI plus deterministic status, health, next, conflicts and trace lookup; external dashboard/export is optional enhancement rather than correctness dependency |

Approximate means:
- **Build:** ~9.4/10
- **Assurance:** ~8.6/10
- **Authority:** ~8.6/10

The mean is intentionally depressed by D06 and D17. This is a feature, not a scoring defect: local evidence must not silently become distributed or provider-backed authority.

## Promotion interpretation
### Repository / local-reference coordination
The current candidate supports `LOCAL_REFERENCE_VERIFIED` and can support `ASSISTED_COORDINATION` within the tested authority boundary once the final combined-head `MERGE_SAFE` run succeeds.

### Distributed multi-host authority
`MULTI_HOST_AUTHORITY` remains disabled until D06 and the distributed variants of D03/D07/D08/D09/D13/D15 are >=9.0 with independent-process/network evidence. PostgreSQL/Supabase or an equivalent transactional backend is an optional P20 implementation choice, not a prerequisite for the current merge.

## Residual gaps after code promotion
1. **P8 live Drive provider bridge** — retry only when connector/provider access is healthy; do not fabricate checkpoint evidence.
2. **P20 distributed authority** — execute only if simultaneous independent-host writes become a real requirement.
3. Optional operator dashboard/trace exporter and live COS backend load/query equivalence may raise operational assurance further but are not merge blockers for the local/reference kernel.
4. Empirical Phase06 performance/calibration gates remain separate from code correctness and cannot be promoted by this Phase07 release.

## Final release rule
No merge from #44 until the current combined-head `MERGE_SAFE` aggregator and Coordination Contracts both pass after the latest canonical-document reconciliation, the PR is mergeable, review threads are empty and the final diff contains no unexplained destructive change.
