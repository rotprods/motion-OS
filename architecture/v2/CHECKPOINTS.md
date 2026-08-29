# MOTION.OS V2 — Objective Checkpoints

Authority: PROPOSED_V2_CANDIDATE

## CP0 — Live Truth Reconstructed
Entry: session identity created; live GitHub/Event Fabric/current state readable.
Required: exact main SHA, open/merged PR lifecycle, active barrier, current event watermark/revision, active claims/scopes.
Evidence: sealed topology snapshot.
Exit: no unresolved ambiguity about current lifecycle authority.
Promotion: permits architecture analysis only.
Rollback: invalidate snapshot on any lifecycle/watermark advance.

## CP1 — Graph Complete
Entry: CP0.
Required: all material domains represented as nodes/edges/hyperedges; no dangling references; COS L0–L19 applicability classified.
Tests: schema/ref validator; orphan scan; duplicate ID scan.
Exit: every P0/P1 gap, owner, test and evidence path is queryable.
Promotion: permits V2 freeze review.

## CP2 — Historical Regression Complete
Required: major pivots, escaped bugs and stale-truth incidents mapped to root causes and permanent regression families.
Exit: every escaped P0/P1 has a regression/property/adversarial test owner.

## CP3 — Architecture Gaps Classified
Required: gap/risk matrix with severity/probability/blast radius/current mitigation/target fix/dependency/owner/evidence.
Exit: no material unknown hidden in prose; residual unknowns are explicit nodes.

## CP4 — V2 Architecture Frozen
Required: Executive V2, Decision Ledger, Lexicon, Hypergraph, migration strategy reviewed; no competing V2 architecture.
Exit: major decisions have alternatives/tradeoffs/reconsideration triggers.
Authority: architecture freeze only, not runtime/release.

## CP5 — Core Contracts Frozen
Required: event/session/identity/evidence/authority semantics versioned; active consumers mapped.
Tests: contract/schema/property compatibility.
Exit: breaking change path and migration defined.

## CP6 — Implementation Kernel Verified
Required: canonical truth, event fabric, QA history, EvidenceEnvelope adapters, core content/render boundaries verified at exact candidate revisions.
Exit: no known P0/P1 in kernel; no second hidden authority.

## CP7 — Recovery Verified
Required: cold reconstruction from durable authority after deleting chat/local checkout/caches/graph projection; Drive absence tested.
Evidence: recovery report hashes current state + graph + next-safe-action.
Exit: important topology/blockers/ownership reproduced within documented tolerance.

## CP8 — Agent Death Drill Passed
Required: zero-context successor identifies North Star, current objective, main, watermark, owners, blockers, verified/unverified work and next safe task within 5 minutes.
Exit: no conversational memory dependency.

## CP9 — Concurrency Verified
Required: duplicate/out-of-order events, stale ContextPack, lease expiry/takeover, same semantic scope, same authority, main-advance-after-CI scenarios.
Exit: unsafe concurrency fails closed; safe disjoint work stays parallelizable.

## CP10 — Security Gauntlet Passed
Required: static/dependency security; boundary-specific input trust tests; secret/PII review; provider/spend/URL/media/filesystem threats; supply-chain evidence.
Exit: P0=0, P1=0 for production-relevant trust boundaries.
Note: full external scanner claim only when actually executed.

## CP11 — E2E Product Path Passed
Required chain: brief -> source/claims -> strategy -> script/TTS/avatar -> Studio -> render -> assembly -> full-video temporal critic -> creative tournament -> repair if needed -> release manifest.
Evidence: one recoverable real master, exact hashes and run IDs.
Exit: no fixture/mechanical substitution for semantic authority.

## CP12 — Empirical Qualification Passed
Required: ID-bound primitives/benchmarks; unseen brief suite; APSR/GSR exact evidence; CAL2 performance learning evidence.
Exit: declared product thresholds met without aggregate-only evidence.

## CP13 — Migration Complete
Required: V2 canonical docs/state navigation; superseded registry; active PR train landed in dependency-safe order; current main revalidated after each merge.
Exit: no parallel V1/V2 authority surfaces.

## CP14 — Production Authority
Entry: CP0–CP13 applicable checkpoints passed.
Required: P0=0/P1=0; GitHub main governance active; exact release+rollback artifacts recoverable; semantic/creative thresholds >=9; provenance complete; post-merge main gauntlet green.
Exit: emit `main.verified` + production release event/manifest.
Authority: PRODUCTION_AUTHORITY.
Rollback: hash-bound rollback artifact + documented release rollback runbook.

## Global checkpoint law

A checkpoint cannot be satisfied by:
- historical tests from another SHA;
- cancelled/skipped/not-run jobs;
- unbound aggregate counters;
- branch implementation without exact evidence;
- chat statements;
- a derived graph claiming authority over source state.
