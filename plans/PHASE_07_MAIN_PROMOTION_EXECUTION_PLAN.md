# MOTION.OS Phase07 — Main Promotion Execution Plan

Status: **FINAL COMBINED-HEAD QUALIFICATION**
Canonical PR: #44 `feat/agentic-coordination-kernel`
Canonical Bus: #39
Canonical Epic: #41
Repository merge authority: `MERGE_SAFE`

## North Star
Promote MOTION.OS to `main` with one coherent agentic/content/studio graph, deterministic recovery, fail-closed authority boundaries, dedicated coordination contracts, local-first clean-runner merge authority and no competing coordination implementation.

## Executed dependency topology
- Phase06 PR #37: **MERGED + VERIFIED** (`6ef91a9fe092387b888d25da67006d68f455d229`).
- Local-first/MERGE_SAFE train PR #46: **MERGED + VERIFIED** (`746c9243ba22452af993e78ca4db89faacc267ca`).
- Follow-up merge-train evidence/main-reconciliation commit observed on main: `0de63a1e56cd289655c45d0b19796442d406ce83`.
- PR #40: **CLOSED_UNMERGED / SUPERSEDED** by #44.
- PR #44 has been structurally reconciled with Phase06 + MERGE_SAFE using real two-parent Git merge commits, never force-pushed.

`main` may advance while this plan is executing. Therefore **hard-coded SHA age never grants merge authority**: the PR virtual merge plus `MERGE_SAFE` against the latest GitHub base is the authoritative final proof.

## Non-negotiable invariants
1. Never merge if the current virtual candidate has a failing required gate.
2. `content_id`, PRV provenance root, MNF replay fingerprint and semantic beat IDs remain Phase06 authority and are consumed read-only by Phase07.
3. COS is a rebuildable projection/query/reasoning plane only; no reverse write authority.
4. Same source history rebuilds identical state/projection hashes.
5. Compatible graph claims enrich a canonical node deterministically; contradictory claims fail closed.
6. Unknown/poison delivery is quarantined and never acknowledged as successful processing.
7. Capability/resource/sensitivity policy is default-deny; untrusted external context cannot self-promote authority.
8. Local/reference qualification never implies independent-host distributed authority.
9. Drive/provider failures are explicit gaps; evidence is never fabricated.
10. Merge/CI/deploy/empirical qualification remain separate lifecycle facts.
11. `MERGE_SAFE` is repository merge authority; `Coordination Contracts` is focused complementary evidence.
12. Concurrent `main` advances require a fresh combined-head proof before canonical verification.

## W1 — P11 unified content lineage — EXECUTED
- [x] Deterministic recursive compatible-property merge.
- [x] Contradictory same-key claims fail closed.
- [x] Invalid node-property JSON/object shape rejected.
- [x] Opportunity → Content → PRV/MNF/Beats → Studio → Publication → Performance → Experiment lineage.
- [x] One canonical graph traverses agent/workstream/event/content/beat/performance/experiment identities.
- [x] Fixed deterministic source fixtures so identical histories really are identical.
- [x] Coordination Contracts/full tests passed during implementation waves.

## W2 — P13/P18 operator observability + UX — EXECUTED
- [x] Deterministic sealed operator status snapshot.
- [x] Health, active work, conflicts, next actions and traces.
- [x] Read-only CLI: `status`, `health`, `next`, `conflicts`, `trace`.
- [x] Content/work/event correlation lookup.
- [x] Malformed input fails visibly; no authority mutation path.

## W3 — P14 trust-boundary hardening — EXECUTED
- [x] Untrusted-context envelope with immutable source SHA-256.
- [x] Recursive secret-like field redaction.
- [x] Prompt/control-plane instruction detection without executing it as authority.
- [x] External authority/trust spoof fields remain untrusted data.
- [x] Deterministic sanitization + negative tests.

## W4 — P16 recovery/replay — EXECUTED LOCALLY
- [x] Zero-chat recovery bundle referencing canonical hashes, not copying authority.
- [x] Main/event/state/coordination/unified/COS/context hashes sealed together.
- [x] Missing source, revision drift and hash drift fail closed.
- [x] Optional provider sources can be absent without synthetic evidence.
- [x] Cold local replay/projection equivalence qualified.
- [ ] Live Drive leg remains external/provider-blocked; not a code-merge blocker and not represented as verified.

## W5 — P17/P19 qualification — FINAL RUN ACTIVE
- [x] Dedicated Coordination Contracts workflow exists on Python 3.11/3.12.
- [x] MERGE_SAFE local-first train exists and is canonical merge authority.
- [x] Prior reconciled candidate passed Python 3.11/3.12, physical analysis, physical Remotion and dependency security.
- [x] 20D scorecard re-rated conservatively after P11/P13/P14/P16/P18.
- [ ] **Final requirement:** current post-documentation virtual merge must receive fresh `Coordination Contracts=SUCCESS` and `MERGE_SAFE=PASS`.
- [ ] Final review-thread/diff/mergeability audit after those gates.

## W6 — Phase06 promotion — COMPLETE
- [x] Diagnosed #37 failing replica-reconciliation contract.
- [x] Restored fail-closed `safe_to_refresh` semantics while retaining advisory-only reconciliation.
- [x] #37 exact head passed Python 3.11/3.12, analysis runtime, Security, Repo Health, Runtime Smoke and Remotion.
- [x] 59-file additive diff, zero deletions, no review threads.
- [x] Squash merged #37 to main as `6ef91a9fe092387b888d25da67006d68f455d229`.

## W7 — Phase07 reconciliation + promotion — FINAL GATE
- [x] Preserved latest main Phase06 files.
- [x] Preserved local-first/MERGE_SAFE workflows, hooks, scripts and immutable event bus.
- [x] Added only Phase07-owned files/subtrees over the latest main tree.
- [x] Merged `AGENTS.md` cumulatively: local-first rules + cross-session constitution.
- [x] Reconciled ADR-007: current local/reference authority; distributed backend optional P20.
- [x] Refreshed bootstrap/active-agent read models and scorecard.
- [ ] Wait for current combined-head `MERGE_SAFE` + Coordination Contracts.
- [ ] Mark #44 ready only after PASS.
- [ ] Merge #44 with expected-head SHA.

## W8 — post-merge main verification
- [ ] Confirm final main SHA and that Phase06, MERGE_SAFE and Phase07 files all exist.
- [ ] Inspect post-merge push/combined-head gates available from GitHub.
- [ ] Persist `pr.merged` / `main.verified` lifecycle evidence using the canonical immutable agent-event format.
- [ ] Verify #40 remains closed/superseded and no duplicate Phase07 PR is active.
- [ ] Update #39/#41/#44 metadata with final truth and residual external-only gaps.

## Merge strategy
Phase06 was merged first because Phase07 consumes its identity/handoff contracts. PR #44 is then merged only after reconciliation with whatever `main` currently contains. No branch-history rewrite is used.

## Rollback
No force push to `main`. Any post-merge regression is handled through a revert PR referencing the exact merge SHA. COS/projection state remains rebuildable from canonical source history.

## Definition of done
`main` contains Phase06 authority contracts, local-first/MERGE_SAFE train and the qualified Phase07 coordination/unified-graph kernel; the current combined candidate passes all applicable merge gates; documentation/read models describe actual topology; remaining gaps are only explicitly external (Drive provider) or deliberately deferred distributed authority (P20), not hidden unfinished code.
