# MOTION.OS Phase07 — Main Promotion Execution Plan

Status: EXECUTING
Canonical PR: #44 `feat/agentic-coordination-kernel`
Dependent active PR: #37 `feat/avatar-script-engine`
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
- [ ] Fix deterministic property merge for shared graph identities.
- [ ] Add compatible enrichment, recursive enrichment, contradiction and invalid-properties tests.
- [ ] Qualify Opportunity → Content → PRV/MNF/Beats → Studio handoff → Publication → Performance → Experiment lineage.
- [ ] Verify one graph can traverse agent/workstream/event/content/beat/performance entities.
- [ ] Re-run Coordination Contracts + full CI.

### W2 — P13/P18 operator observability and UX
- [ ] Add deterministic operator status snapshot: health, active work, conflicts, leases, stale context, replay hashes.
- [ ] Add CLI `status`, `next`, `conflicts`, `health` or equivalent stable surface.
- [ ] Add trace/correlation lookup by content/work/event IDs.
- [ ] Tests for deterministic ordering and fail-closed malformed state.

### W3 — P14 adversarial trust-boundary expansion
- [ ] Add untrusted-context sanitization/redaction primitives for secrets and control-instruction payloads.
- [ ] Preserve evidence while marking untrusted data as data, never executable authority.
- [ ] Add prompt-injection/control-plane spoofing, secret leakage and sensitivity downgrade negative tests.
- [ ] Keep policy default-deny.

### W4 — P16 cold recovery/replay closure
- [ ] Add zero-chat recovery bundle from canonical GitHub/lifecycle + event snapshot + projection sources.
- [ ] Verify events → state → coordination graph → content graph → unified graph → COS shadow equivalence.
- [ ] Verify source/hash drift invalidates the recovery/context bundle.
- [ ] Add corrupted/missing-source fail-closed tests.
- [ ] Drive live leg remains conditional on provider health; provider-neutral EvidenceManifest remains mandatory.

### W5 — P17/P19 qualification and release score
- [ ] Run dedicated Coordination Contracts on Python 3.11/3.12.
- [ ] Run full CI on Python 3.11/3.12.
- [ ] Run physical analysis-runtime.
- [ ] Run Repo Health, Security Baseline, Runtime Smoke, Remotion Runtime.
- [ ] Diff review: deletion audit, shared-file audit, review-thread audit, mergeability.
- [ ] Re-rate 20D with conservative Authority=min(Build,Assurance).

### W6 — PR #37 qualification and promotion
- [ ] Read latest #37 head and exact workflow evidence.
- [ ] Ensure merge candidate against current main is green and mergeable.
- [ ] Final diff/security/authority review.
- [ ] Merge #37 to main first if #44 consumes its stable contracts or schemas.
- [ ] Record merge SHA and update lifecycle topology.

### W7 — PR #44 rebase/reconciliation and promotion
- [ ] Reconcile #44 against post-#37 `main` without force rewrites.
- [ ] Resolve only real conflicts; preserve Phase06 authority.
- [ ] Run exact-head/virtual-merge full gates again.
- [ ] Mark ready for review only after all gates pass.
- [ ] Merge #44 to main with expected-head SHA.

### W8 — Post-merge main verification
- [ ] Run/check workflows associated with the final main merge SHA when available.
- [ ] Verify canonical files exist on main.
- [ ] Verify #40 stays CLOSED_UNMERGED/SUPERSEDED and no duplicate coordination PR remains active.
- [ ] Update #39/#41 with final merge SHAs, score and residual external blockers.
- [ ] Close #41 only if all non-external P0–P19 gates are satisfied; otherwise leave open with a minimal residual list.

## Merge order decision
Default: `#37 → main`, then reconcile/qualify `#44 → main`.
Reason: Phase07 P11 consumes Phase06 identity and handoff contracts. Merging Phase06 first makes those contracts canonical and allows #44 to qualify against the true production base rather than a sibling branch.

If #37 exact-head qualification fails, do not merge it. #44 may only merge first if it contains no dependency on unmerged #37 implementation and all P11 assertions are explicitly framed as compatibility with a pinned sibling contract rather than main authority.

## Release evidence required for each merge
- PR is mergeable.
- No unresolved review threads.
- Exact tested head recorded.
- CI success.
- Repo Health success.
- Security Baseline success.
- Runtime Smoke success.
- Remotion Runtime success.
- Coordination Contracts success for #44.
- No unexplained destructive diff.

## Rollback
No force pushes to main. If a merge causes main regression, create a revert PR referencing the exact merge SHA; do not rewrite branch history. Projection/COS data remains rebuildable from canonical source history.

## Definition of done
`main` contains the qualified Phase06 authority contracts and Phase07 agentic coordination/unified-graph kernel; all available repository workflows pass on the merge candidates; operator/recovery/security surfaces are covered by tests; canonical issues/PR descriptions reflect final truth; remaining blockers are only external provider or deliberately deferred multi-host infrastructure, and are stated explicitly rather than counted as complete.
