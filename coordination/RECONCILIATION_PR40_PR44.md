# Reconciliation — PR #40 → PR #44

Status: FEATURE_PARITY_IMPLEMENTED / CI_PENDING / BRANCH_SYNC_PENDING
Canonical branch: PR #44 `feat/agentic-coordination-kernel`
Predecessor: PR #40 `infra/agentic-coordination-plane`
Canonical Bus: #39
Canonical Epic: #41
Canonical Drive: `MOTION.OS_CANONICAL/11_AGENTIC_COORDINATION`

## Incident
PR #40 and PR #44 were created independently by concurrent agents. This is the exact failure mode Phase07 exists to eliminate: two valid but overlapping control planes created without shared enforced context.

## Canonical decision
One implementation survives: #44. #40 remains open only until feature-parity evidence and fresh CI are green. GitHub #39/#41 and Drive11 remain the canonical control objects because they were established first and already contain useful lineage.

## Coverage preserved from #40
- aggregate revisions + aggregate heads → `src/coordination/event_store.py`
- explicit idempotency keys + logical-event collision detection → `event_store.py`, `events.py`
- payload hash distinct from whole-event seal → `events.py`
- structured provenance refs → `events.py`
- parent event IDs + causation/correlation → `events.py`, `projection.py`
- explicit workstream ID + resource scopes → `events.py`, `projection.py`
- monotonic event watermark → `InMemoryReferenceEventStore.watermark()`
- deterministic state snapshots → `StateSnapshot`
- consumer inbox/effect idempotency → `ReferenceInbox`
- commands and outcomes remain distinct facts → `event_semantics.py`
- developer/runtime coordination share one envelope while authority remains aggregate-specific → canonical `CoordinationEvent v1`

## Coverage preserved from #44
- EventBus/transport separated from EventStore authority
- canonical file/tree/semantic resource resolver
- semantic conflict classifier
- READ/WRITE/EXCLUSIVE lease/fencing/CAS semantics
- deterministic ContextPack seal and staleness model
- portable snapshot + zero-context CLI
- leased outbox dispatcher contract
- deterministic event→graph projection + COS no-writeback sink
- authority-plane matrix
- 20D Build/Assurance/Authority scorecard
- adversarial gauntlet

## Architecture after convergence
1. EventStore owns aggregate revision, idempotency and event watermark.
2. EventBus owns ordered delivery/consumer progress, not aggregate authority.
3. Inbox owns consumer-effect deduplication.
4. Lease authority owns protected-write fencing/CAS.
5. Conflict engine resolves path/semantic/dependency/authority overlap before lease acquisition.
6. ContextPack provides bounded, sealable cross-session context.
7. COS is a rebuildable projection/query plane with no reverse authority path.
8. Phase06 SQLite render authority remains separate from Phase07 coordination state.
9. Multi-host Postgres remains an optional promotion stage, not an engineering prerequisite.

## Current repository topology
- #34 CLOSED_UNMERGED → superseded by merged #42 Remotion runtime v2.
- #35 CLOSED_UNMERGED → superseded by merged #38 Studio Engine.
- #37 ACTIVE → Phase06 Content Intelligence + Avatar Factory.
- #40 OPEN → predecessor pending final supersession gate.
- #44 ACTIVE → canonical Phase07 convergence branch.

## P0 Definition of Done
- [x] unique #40 architectural guarantees mapped
- [x] unique #40 executable guarantees ported
- [x] aggregate revision/idempotency tests
- [x] watermark/state-snapshot tests
- [x] inbox idempotency tests
- [x] command/outcome separation tests
- [x] canonical bus #39
- [x] canonical epic #41
- [x] canonical Drive11
- [x] topology no longer treats #34/#35 as active
- [x] #43/#45 identified as duplicate control objects
- [ ] fresh current-head CI green
- [ ] #44 synchronized/reconciled with current main and mergeability restored
- [ ] checkpoint appended to #39 with final CI evidence
- [ ] close #40 as superseded only after the three gates above

Until all unchecked gates pass, P0 remains IMPLEMENTED_UNVERIFIED rather than VERIFIED.
