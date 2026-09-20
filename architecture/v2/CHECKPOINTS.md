# MOTION.OS V2 — Objective Checkpoints

Authority: `IMPLEMENTED_PENDING_REVIEW`
Canonical candidate: PR #91

## CP0 — Live Truth Reconstructed
Entry: session identity created; live GitHub/Event Fabric/current state readable.
Required: exact main SHA, open/merged PR lifecycle, active barrier, current event watermark/revision, active claims/scopes.
Evidence: sealed topology snapshot.
Exit: no unresolved ambiguity about current lifecycle authority.
Promotion: permits architecture analysis only.
Rollback: invalidate snapshot on lifecycle/watermark advance.

## CP1 — Graph Complete
Entry: CP0.
Required: all material domains represented as nodes/hyperedges; no dangling references; COS L0–L19 applicability classified; uncertainty nodes have owner+resolution path.
Tests: JSON Schema + FormatChecker; semantic ref/duplicate/time/authority validation; package integrity validation.
Exit: every P0/P1 gap, owner, test and evidence path is queryable.

## CP2 — Historical Regression Complete
Required: major pivots, escaped bugs and stale-truth incidents mapped to root causes and permanent regression families.
Exit: every escaped P0/P1 has a regression/property/adversarial test owner.

## CP3 — Architecture Gaps Classified
Required: gap/risk matrix with severity/probability/blast radius/current mitigation/target fix/dependency/owner/evidence.
Exit: material UNKNOWN/RISK/BLOCKER/DEFERRED decisions are explicit nodes with resolution paths.

## CP4 — V2 Architecture Frozen
Required: Executive V2, Architecture Delta, Decision Ledger, Lexicon, hypergraph, implementation compiler, assurance and migration model reviewed; no competing V2 candidate.
Exit: major decisions have alternatives/tradeoffs/reconsideration triggers; #90 classified SUPERSEDED_BY_91.
Authority: architecture freeze only, never release authority.

## CP5 — Core Contracts Frozen
Required: event/session/identity/evidence/authority semantics versioned; active consumers mapped; migration compatibility explicit.
Tests: contract/schema/property compatibility.
Exit: no hidden second authority.

## CP6 — Implementation Kernel Verified
Required: canonical truth, Event Fabric, QA history, evidence adapters, content/render boundaries verified at exact candidate revisions.
Exit: P0=0/P1=0 in core kernel.

## CP7 — Recovery Verified
Required: cold reconstruction after deleting chat/local checkout/caches/graph projection; Drive absence tested.
Evidence: recovery report hashes current state + graph + next-safe-action.
Exit: important topology/blockers/ownership reproduced within declared tolerance.

## CP8 — Agent Death Drill Passed
Required: zero-context successor identifies North Star, objective, main, watermark, owners, blockers, verified/unverified work and next safe task within 5 minutes.
Exit: no conversational-memory dependency.

## CP9 — Concurrency Verified
Required: duplicate/out-of-order events, stale ContextPack, lease takeover, same semantic scope, same authority and main-advance-after-CI scenarios.
Exit: unsafe concurrency fails closed; safe disjoint work stays parallelizable.

## CP10 — Security Gauntlet Passed
Required: static/dependency security; boundary-specific input trust tests; secrets/PII/provider/spend/URL/media/filesystem/supply-chain review.
Exit: P0=0/P1=0 for production trust boundaries.
External scanner authority is claimed only when actually executed.

## CP11 — E2E Product Path Passed
Required chain: brief → source/claims → strategy → script/TTS/avatar → Studio → renderer/assembly → real full-video temporal critic → creative tournament → repair → release manifest.
Evidence: recoverable real master, exact hashes/run IDs/frame authority.
Exit: fixture/mechanical smoke cannot substitute semantic/creative authority.

## CP12 — Empirical Qualification Passed
Required: exact ID-bound primitive/benchmark suite; unseen briefs/styles; APSR/GSR; CAL2/performance evidence.
Exit: declared product thresholds met without aggregate-only authority.

## CP13 — Migration Complete
Required: V2 canonical navigation/state model; superseded registry; dependency-safe PR train; current main revalidated after every merge.
Exit: no competing V1/V2 current authority.

## CP14 — Production Authority
Entry: CP0–CP13 applicable gates passed.
Required: P0=0/P1=0; GitHub main governance active; exact release+rollback artifacts recoverable; semantic/creative thresholds ≥9 where declared; provenance complete; post-merge whole-main gauntlet green.
Exit: emit `main.verified` + production release event/manifest.
Rollback: exact hash-bound rollback artifact + runbook.

## Checkpoint law

A checkpoint cannot be satisfied by historical tests from another SHA, cancelled/skipped/not-run jobs, unbound aggregate counters, branch implementation without exact evidence, chat statements, or a derived graph asserting authority over source state.