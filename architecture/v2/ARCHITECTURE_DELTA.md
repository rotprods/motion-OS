# MOTION.OS — Architecture Delta: Current → V2

Authority: `PROPOSED_V2_CANDIDATE`
Source revision: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`

This delta describes migration intent. It does not silently supersede current-main contracts.

| Domain | Current topology | V2 topology | Action | Why | Migration risk |
|---|---|---|---|---|---|
| Current truth | GitHub live + hand-maintained `STATE.md`, `project_state.json`, `ACTIVE_AGENTS.yaml`, Issue bodies/comments | GitHub live lifecycle/admin + canonical machine state + deterministic validated projections | REFACTOR | stale docs currently contradict live lifecycle | Medium: accidental overwrite of historical evidence |
| Events | Issue #39 bootstrap comments + repo immutable events + Runtime EventStore | one semantic Event Fabric with transport/storage adapters and shared logical event IDs | REFINE/MIGRATE | prevent three competing truths | Medium: adapter parity |
| Agent identity | agent/workstream increasingly explicit; session semantics branch-qualified | project→agent→session→workstream→objective→correlation first-class everywhere | REFINE | zero-context continuity and collision attribution | Low/Medium |
| Context | docs/chat/bootstrap snapshots + ContextPack implementation | sealed ContextPack bound to current main, event watermark, projection revision and scopes | REFINE | stale context must invalidate automatically | Medium |
| Conflict detection | some path-based consumers + stronger branch semantics | one conflict engine for path + contract + ADR + root-cause + authority + architecture scopes | REFACTOR | REG-017 proved path-disjoint semantic collisions | Medium |
| State/event authority | single-host semantics plus future distributed proposal | single-host authority remains until measured trigger; transactional distributed adapter deferred | KEEP/DEFER | avoid infrastructure astrology | Low |
| COS graph | deterministic coordination/content projections | V2 temporal hypergraph over shared IDs, explicitly no reverse-write authority | REFINE | stronger cross-domain reasoning without dual truth | Low |
| Content intelligence | Phase06 source→claims→ICP→hook→beats→script/TTS/avatar + sealed handoff | keep pipeline; harden claim/TTS/provider/spend/performance evidence boundaries | KEEP/REFINE | strong existing capability, remaining trust gaps are local | Low/Medium |
| Studio | graph-native editing/repair foundation | evidence-bound Studio consumes sealed handoff and emits typed scene/edit/render intents | KEEP/REFINE | preserve working implementation, clarify boundaries | Medium |
| QA graph | run history/repair semantics under correction | run-scoped immutable QA evidence + truthful target mutations + atomic identity preflight | REFACTOR | avoid graph lies/collisions | Medium |
| Remotion | physically verified runtime on main | production renderer adapter with reproducible dependency identity and normalized evidence | KEEP/REFINE | proof exists; provenance/reproducibility can improve | Low |
| HyperFrames | physical branch proof | provenance-bound renderer adapter | REFINE | foreign same-shape artifact must not satisfy verifier | Medium |
| Lottie | compiler/player contract, physical proof blocked | official-player physically qualified adapter | MIGRATE | renderer diversity requires real execution | Medium |
| Assembly audio | master-audio direction physically tested | exactly one assembly audio authority | KEEP | avoids duplicate/mixed audio authority | Low |
| Alpha | plane evidence exists | semantic alpha/compositor evidence | REFINE | channel presence ≠ correct transparency | Medium |
| Color | explicit normalization contract branch | canonical working/output color space physically enforced across renderer outputs | REFINE | prevent cross-render drift | Medium |
| Timing | historical mux-duration escaped bug, frame-based rules partly established | decoded frame-count/time-base is visual authority across reconstruction/critic/release | REFACTOR | prevent approximate timing from masquerading as exact | High if migration incomplete |
| Temporal QA | contract/fixtures/branch critic but real master/provider blocked | recoverable real master + decoded evidence + full-video provider + defect causality + creative tournament | MIGRATE | product release requires real semantic evidence | High / critical path |
| Primitive qualification | aggregate historical counts + branch ledger | exact primitive×renderer IDs with physical/semantic evidence | REFACTOR | aggregate counts cannot survive evidence loss | Medium |
| Benchmarking | historical 25/5 aggregate + mechanical smoke branch | exact suite manifest + per-brief creative artifacts + evidence-bound APSR/GSR | REFACTOR | mechanical repeatability does not prove style/generalization | High / product |
| Learning | observation/learning candidate implementation evolving | evidence-bound observation→controlled experiment→causal rule lifecycle | REFINE | prevent performance poisoning | Medium |
| Security | pinned Actions mostly, pip audit/static branch, manual threat reviews | layered static/dependency + boundary-specific security + supply-chain + explicit residual risks | REFINE | scanners alone cannot prove trust-boundary safety | Medium |
| CI | local-first + MERGE_SAFE, full on merge_group | preserve; add V2/package/evidence invariants and current-main/watermark preflight | KEEP/REFINE | architecture works; coverage classification must track new contracts | Low |
| Main governance | protocol discipline; GitHub ruleset not applied | GitHub-native PR-only required checks/no force/delete/combined-head enforcement | MIGRATE_EXTERNAL | code policy cannot block authorized direct push | External blocker |
| Recovery | branch-qualified cold recovery + historical docs | authority-only cold rebuild + zero-context death drill + explicit external-artifact degradation | REFINE | continuity must survive chat/local/graph deletion | Medium |
| Docs | many useful phase/ADR/state docs with mixed lifecycle freshness | typed documentation information system with authority/scope/source/supersession metadata | REFACTOR/MIGRATE | docs currently drift into accidental truth | Medium |
| Autonomy | preproduction self-driving loop | bounded scheduler activated only after Event Fabric/security/governance gates | DEFER_ACTIVATION | autonomy amplifies stale-authority defects | High if premature |
| Infrastructure | optional future Postgres/Supabase/queues/CDN concepts | interfaces now, deployments only on measured triggers | DEFER | minimize cost/cognitive/failure surface | Low |

## Net architecture movement

Current architecture is not discarded. V2 removes **ambiguity and evidence gaps**, not functioning capability. The migration concentrates authority into explicit contracts and makes everything else—graphs, docs, ContextPacks, dashboards, Todoist—rebuildable projections.

The dominant delta is:

```text
V1-ish
many strong modules + improving event/session semantics + several hand-maintained summaries

            ↓

V2
one authority hierarchy
+ one semantic Event Fabric
+ one evidence identity chain
+ session-native coordination
+ renderer normalization contracts
+ decoded temporal authority
+ empirical creative qualification
+ deterministic derived hypergraph
```

The migration is complete only when current-main surfaces adopt the V2 authority model; this document alone grants no authority.