# Phase07 Stop-the-Line Reconciliation — PR #40 ↔ PR #44

Date: 2026-08-26
Status: CANONICAL CONVERGENCE IN PROGRESS

## Incident
Two agents independently implemented overlapping Phase07 agentic coordination planes:
- PR #40 `infra/agentic-coordination-plane`
- PR #44 `feat/agentic-coordination-kernel`

Both were created from the same historical main lineage while the agents lacked a shared enforced coordination authority. This is not merely duplicate code; it is the exact failure mode Phase07 exists to eliminate.

## Stop-the-line decision
No further independent expansion of either coordination architecture until their capabilities are reconciled. One canonical bus, one epic, one Drive folder and one implementation PR must remain after convergence.

## Canonical control objects
To minimize disruption and preserve first-created shared references:
- Bootstrap Coordination Bus: **Issue #39** (keep)
- Phase07 Epic: **Issue #41** (keep)
- Drive canonical folder: **`MOTION.OS_CANONICAL/11_AGENTIC_COORDINATION`** (keep)
- Implementation/convergence PR: **PR #44** (use as convergence branch because it currently contains the broader hardened implementation and executed CI history)

Supersede after migration:
- Issue #43 → duplicate of #39
- Issue #45 → duplicate of #41
- Drive `09_AGENTIC_COORDINATION` → superseded/move contents into 11
- PR #40 → superseded only after all unique guarantees below are represented in #44 and evidence passes

## Capability comparison

| Capability | #40 | #44 | Canonical convergence |
|---|---|---|---|
| GitHub bootstrap bus | #39 | #43 | Keep #39 |
| Epic / roadmap | #41 W0–W14 | #45 W0–W10 | Keep #41, enrich with #44 gates |
| Drive coordination folder | 11_AGENTIC | 09_AGENTIC | Keep 11 |
| Cross-agent constitution | Strong command/outcome + watermark rules | Strong explicit truth-plane/outbox/COS rules | Merge both |
| Event identity | idempotency_key + payload_hash | whole-event provenance_hash | Keep both |
| Aggregate concurrency | aggregate_revision + aggregate_heads | generic expected_revision | Adopt #40 aggregate revision/head semantics |
| Causality | causation + parent_event_ids | causation + correlation | Adopt superset |
| Workstream model | explicit workstream_id/resource_scope | run_id + canonical scopes | Adopt superset |
| Provenance | structured list | evidence refs + event hash | Keep structured provenance + evidence + whole-event seal |
| Command/outcome separation | Explicit hard invariant | Event families, less explicit | Adopt #40 invariant |
| Event watermark | sequence_id + snapshots | time/event-id cursor | Adopt monotonic sequence watermark |
| Durable event DB | event log + heads + inbox/outbox/snapshots | log + consumers + outbox + rich state tables | Merge, prefer sequence/heads/inbox plus #44 work/decision/conflict/context tables |
| Outbox multi-dispatcher | Basic | leased `SKIP LOCKED`, stale ack fencing | Keep #44 hardened version |
| Consumer idempotency | inbox table + offsets | monotonic consumers | Keep both inbox/effect hash + monotonic offset |
| Lease semantics | exact resource generation, reference store | READ/WRITE/EXCLUSIVE, atomic SQL functions, canonical aliases | Keep #44 superset, add #40 workstream/path/semantic metadata |
| Resource alias safety | normalization only | explicit file/tree canonical resolver + escape rejection | Keep #44 |
| ContextPack | watermark/projection + next_safe_actions | seal + allowed/forbidden scopes + source-revision staleness | Merge both |
| Portable snapshot | no | yes | Keep #44 |
| Zero-context CLI | no | yes | Keep #44 |
| COS graph | architecture graph | executable deterministic projector + sink contract | Keep #44 + #40 source_event temporal semantics |
| Graph rebuild checkpoint | DB checkpoint table | projection_versions | Merge |
| 20D scorecard | no | yes | Keep #44 |
| Adversarial gauntlet | qualification list | 65 cases | Keep #44, add poison-event quarantine from #40 |
| Viral engine delta | strong object lineage/analytics publishing | stronger account/goal/opportunity/dual-score/platform detail | Preserve both; V3 on #37 is canonical application delta |
| Runtime vs developer bus | explicitly two buses / one event model | implied | Adopt #40 wording/model |
| Phase06 authority separation | preserve render guarantees | explicit Authority Plane Matrix | Keep #44 explicit matrix |

## Unique #40 guarantees that MUST be ported before superseding #40
1. `aggregate_revision` allocated monotonically per aggregate.
2. `aggregate_heads` with CAS / expected revision.
3. explicit `idempotency_key` distinct from event hash.
4. `payload_hash` distinct from whole-event provenance hash.
5. structured provenance refs.
6. `parent_event_ids` for multi-parent causal ancestry.
7. explicit `workstream_id` and `resource_scope` on events.
8. monotonic numeric event `sequence_id` / event watermark.
9. inbox table for consumer effect idempotency.
10. durable state snapshots at event watermark.
11. commands and outcomes are distinct facts and event families.
12. developer coordination bus and runtime event bus share one envelope without sharing aggregate authority.
13. poison/unknown-event quarantine as a qualification gate.

## Unique #44 guarantees that MUST be preserved
1. READ/WRITE/EXCLUSIVE_WRITE semantics.
2. canonical file/tree/semantic resource resolver.
3. advisory-lock + fencing-generation SQL acquisition.
4. leased multi-dispatcher outbox + stale publish acknowledgement rejection.
5. deterministic ContextPack seal and source/main/projection invalidation.
6. portable coordination snapshot.
7. zero-dependency bootstrap CLI.
8. deterministic event→graph projection with snapshot hash.
9. narrow no-writeback `CosProjectionSink` contract.
10. authority-plane separation: Phase06 SQLite render state != Phase07 Postgres coordination.
11. 20D Build/Assurance/Authority score model.
12. 65-case adversarial gauntlet.
13. real drift discovery: #34/#35 closed, #38/#42 merged.
14. tests/CI evidence and fail-open CLI defect triaged visibly.

## Current topology after drift refresh
- `main`: Studio Phase05 merged via #38; Remotion runtime v2 merged via #42.
- PR #37: ACTIVE — Content Intelligence + Avatar Factory.
- PR #40: ACTIVE but coordination-duplicate candidate.
- PR #44: ACTIVE convergence candidate.
- PR #34/#35: CLOSED_UNMERGED historical branches; must not appear as active agents.

## Convergence acceptance criteria
PR #40 may be closed as superseded only when:
- all 13 unique #40 guarantees above are represented in #44;
- one canonical event/schema contract exists, not two incompatible ones;
- one canonical Postgres DDL set exists;
- #39/#41/Drive11 are referenced everywhere canonical;
- #43/#45/Drive09 are marked/moved superseded;
- active-agent registry reflects current topology;
- latest full CI is green;
- a checkpoint describing this incident is appended to #39;
- no unique #40 test or safety invariant is silently discarded.

## Learning
The coordination system must bootstrap with a conflict detector even before the final DB exists. Merely documenting “read the bus” is insufficient if two agents can create competing buses in parallel. Future bootstrap requires discovery by semantic intent (`phase:07/agentic-coordination`) before creating a new control object.
