# MOTION.OS Phase07 — Main Promotion Execution Plan

Status: EXECUTING — FINAL QUALIFICATION
Canonical PR: #44 `feat/agentic-coordination-kernel`
Phase06 dependency: #37 MERGED to `main` as `6ef91a9fe092387b888d25da67006d68f455d229`
Canonical Bus: #39
Canonical Epic: #41

## North Star
Promote MOTION.OS to `main` with one coherent agentic/content/studio graph, deterministic recovery, fail-closed authority boundaries, dedicated contract CI, operator-readable state and no unresolved competing coordination implementation.

## Non-negotiable invariants
1. Never merge a PR whose exact head/virtual merge SHA has a failing required workflow.
2. `content_id`, PRV provenance root, MNF replay fingerprint and semantic beat IDs remain Phase06 authority and cannot be recomputed by Phase07.
3. COS is a rebuildable projection/query plane only; no reverse authority/writeback.
4. Same source history must rebuild the same state/graph hashes.
5. Compatible graph claims may enrich a canonical node; contradictory claims fail closed.
6. Unknown/poison delivery is quarantined and never acknowledged as successful processing.
7. Capability/policy enforcement is default-deny.
8. Local/reference qualification is never represented as multi-host distributed authority.
9. Drive/provider failures remain explicit blockers, never fabricated evidence.
10. Merge/close/CI/deploy/empirical qualification remain separate lifecycle facts.

## Execution waves

### W1 — P11 unified content lineage closure
- [x] Fix deterministic property merge for shared graph identities.
- [x] Add compatible enrichment, recursive enrichment, contradiction and invalid-properties tests.
- [x] Qualify Opportunity → Content → PRV/MNF/Beats → Studio handoff → Publication → Performance → Experiment lineage.
- [x] Verify one graph can traverse agent/workstream/event/content/beat/performance entities.
- [x] Fix deterministic fixture identity so “same sources” means identical event IDs/timestamps.
- [x] Re-run Coordination Contracts + full pytest on the pre-Phase06-merge candidate successfully.

### W2 — P13/P18 operator observability and UX
- [x] Add deterministic operator status snapshot: health, active work, conflicts, next actions and trace records.
- [x] Add read-only CLI `status`, `health`, `next`, `conflicts`, `trace` surface.
- [x] Add trace/correlation lookup by content/work/event IDs.
- [x] Add deterministic ordering and malformed-input fail-visible tests.

### W3 — P14 adversarial trust-boundary expansion
- [x] Add untrusted-context envelope with immutable source SHA-256 provenance.
- [x] Redact secret-like fields recursively.
- [x] Detect control-plane/prompt-injection text while preserving it only as untrusted data.
- [x] Add authority-spoofing, secret-leakage and deterministic sanitization negative tests.
- [x] Keep capability policy default-deny; external payload fields never self-promote authority.

### W4 — P16 cold recovery/replay closure
- [x] Add zero-chat recovery bundle referencing canonical hashes instead of copying authority.
- [x] Bind main/event/state/coordination/unified/COS/context hashes into one sealed bundle.
- [x] Detect missing source, revision drift and content hash drift fail-closed.
- [x] Permit explicitly optional provider sources such as Drive without fabricating evidence when unavailable.
- [x] Add deterministic seal and corrupted/missing-source tests.
- [ ] Live Drive leg remains blocked by provider/connector availability; provider-neutral EvidenceManifest remains mandatory.

### W5 — P17/P19 qualification and release score
- [x] Dedicated Coordination Contracts workflow exists on Python 3.11/3.12.
- [ ] Run dedicated Coordination Contracts against post-#37 `main` virtual merge.
- [ ] Run full CI on Python 3.11/3.12 against post-#37 `main` virtual merge.
- [ ] Run physical analysis-runtime against post-#37 `main` virtual merge.
- [ ] Run Repo Health, Security Baseline, Runtime Smoke, Remotion Runtime against post-#37 `main` virtual merge.
- [ ] Final diff/review-thread/mergeability audit.
- [ ] Re-rate 20D with conservative Authority=min(Build,Assurance).

### W6 — PR #37 qualification and promotion
- [x] Read latest #37 head and exact workflow evidence.
- [x] Diagnose failing reconciliation test (`safe_to_refresh` missing).
- [x] Restore explicit fail-closed `safe_to_refresh` contract while keeping reconciliation advisory-only.
- [x] Exact head `d8a31fee1929bae0d3ecfade9c74d2c6fd0b6d64` passed CI, physical analysis-runtime, Repo Health, Security Baseline, Runtime Smoke and Remotion Runtime.
- [x] Final diff review: 59 files, additive, zero deletions; no review threads.
- [x] Merge #37 to main first.
- [x] Record merge SHA: `6ef91a9fe092387b888d25da67006d68f455d229`.

### W7 — PR #44 reconciliation and promotion
- [x] Confirm #44 remains mergeable after #37 promotion and has no Phase06 authority overwrite.
- [x] Force a new branch commit after #37 merge so GitHub must generate a fresh virtual merge against `main@6ef91a9f...`.
- [ ] Run exact-head/virtual-merge full gates again.
- [ ] Mark ready for review only after all gates pass.
- [ ] Merge #44 to main with expected-head SHA.

### W8 — Post-merge main verification
- [ ] Check workflows associated with the final main merge SHA when available.
- [ ] Verify canonical files exist on main.
- [ ] Verify #40 stays CLOSED_UNMERGED/SUPERSEDED and no duplicate coordination PR remains active.
- [ ] Update #39/#41 with final merge SHAs, score and residual external blockers.
- [ ] Close #41 only if all non-external P0–P19 gates are satisfied; otherwise leave open with a minimal residual list.

## Merge order decision — executed
`#37 → main` first, then `#44 → main` after full requalification.

Reason: Phase07 P11 consumes Phase06 identity and handoff contracts. Phase06 is now canonical on main, so #44 is being qualified against the true production base rather than a sibling branch.

## Release evidence required for #44
- PR is mergeable.
- No unresolved review threads.
- Exact tested head recorded.
- Virtual merge parent includes `main@6ef91a9f...` or later.
- Coordination Contracts success.
- CI success including Python 3.11/3.12 and physical analysis runtime.
- Repo Health success.
- Security Baseline success.
- Runtime Smoke success.
- Remotion Runtime success.
- No unexplained destructive diff.

## Rollback
No force pushes to main. If a merge causes main regression, create a revert PR referencing the exact merge SHA; do not rewrite branch history. Projection/COS data remains rebuildable from canonical source history.

## Definition of done
`main` contains the qualified Phase06 authority contracts and Phase07 agentic coordination/unified-graph kernel; all available repository workflows pass on the final merge candidates; operator/recovery/security surfaces are covered by tests; canonical issues/PR descriptions reflect final truth; remaining blockers are only external provider or deliberately deferred multi-host infrastructure, and are stated explicitly rather than counted as complete.
