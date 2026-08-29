# MOTION.OS V2 — Canonical Lexicon

Authority: PROPOSED_V2_CANDIDATE

| Term | Canonical definition | Aliases / deprecated usage | Anti-example |
|---|---|---|---|
| PROPOSED | Design/decision exists; no implementation claim. | planned | Calling a plan implemented. |
| IMPLEMENTED | Code/config/artifact exists in a revision. | built | Calling unexecuted code verified. |
| EXECUTED | Implementation has run in a named environment/run. | ran | Assuming execution from code existence. |
| VERIFIED | Applicable authoritative tests/evidence passed for the exact identity/revision claimed. | green | Reusing tests from an earlier SHA. |
| EMPIRICALLY_QUALIFIED | Real-world/product evidence meets declared empirical acceptance thresholds. | production proven | Mechanical render smoke called creative quality. |
| BLOCKED | Required dependency/authority/evidence prevents safe next transition. | stuck | Optional polish listed as blocker. |
| DEGRADED_EXTERNAL | External dependency unavailable; system degrades explicitly without fabricating authority. | partial outage | Pretending Drive evidence exists. |
| SUPERSEDED | Historical entity remains valid history but is no longer current authority. | obsolete | Deleting/re-writing history. |
| Authority | Right to make/validate an irreversible or canonical claim for a bounded domain. | source of truth | A dashboard summary. |
| Evidence | Immutable/reproducible observation tied to exact identity/revision/artifact. | proof | An unbound aggregate count. |
| Artifact | Produced file/media/bundle identified by content hash and lineage. | output | Filename without hash/provenance. |
| Event Fabric | Canonical event semantics projected/stored through one or more adapters. | event bus | Three independent event truths. |
| Event watermark | Monotonic read position/revision used to invalidate stale ContextPacks. | cursor | Timestamp guessed from chat order. |
| ContextPack | Sealed, derived working context bound to main/lifecycle/event revisions and scopes. | context | Chat transcript as shared state. |
| Projection | Deterministic derived representation rebuildable from authority. | cache/read model/graph | A projection that accepts authoritative writes. |
| COS Graph | Derived query/reasoning projection over shared IDs and typed edges. | supergraph | Hidden state store that overrides events. |
| Session | Globally unique material execution identity for one agent run. | chat/session | Reusing one session ID across separate executions. |
| Workstream | Bounded concurrent unit of work with branch, objective and scopes. | branch | Branch name treated as ownership lock. |
| Correlation ID | Stable task/operation grouping identity. | trace ID | Treating correlation as causation. |
| Causation | Explicit parent/trigger relation between events/actions. | parent event | Same workstream assumed causal. |
| Resource scope | Path/tree/shared resource identity. | write set | Only listing branch name. |
| Semantic scope | ADR/contract/architecture/root-cause/capability/authority domain touched. | logical ownership | File-disjoint PRs assumed conflict-free. |
| Claim | Agent request to operate on a bounded scope under a ContextPack. | ownership | Permanent ownership implied from an old claim. |
| Lease | Time/revision-bounded permission to act on a claimed scope. | lock | Resetting fencing generation after release. |
| Fencing token | Monotonic generation preventing stale writers from regaining authority. | generation | Reusing token 1 after release. |
| Current state | Projection of valid non-superseded facts reconciled with live lifecycle. | latest doc | Append-only issue body treated as current. |
| Historical state | Immutable fact valid for its historical interval. | old state | Deleting stale facts. |
| Release candidate | Exact candidate ID + media hash + source/run/evidence chain under evaluation. | RC | A logical name with missing media. |
| Mechanical render evidence | Proof that runtime produced expected media mechanics/timing. | renderer verified | Style/creative fidelity claim. |
| Creative authority | Evidence that visual/narrative/motion quality meets creative thresholds on real content. | quality pass | Runtime smoke. |
| RECONSTRUCT_EXACT | Fidelity optimizer requiring decoded frame/time/content authority. | clone | Duration-estimated frame timeline. |
| STRUCTURAL_TEMPLATE | Reusable structure with explicit approximation/generalization. | template | Claiming pixel-exact reconstruction. |
| STYLE_TRANSFER | Creative adaptation preserving chosen style invariants, not frame identity. | recreate | Using fidelity score as style score. |
| APSR | Artifact/evidence-bound aggregate pass rate over an exact benchmark suite. | pass rate | `25 briefs` counter without IDs. |
| GSR | Evidence-bound generalization/style success across the exact declared style coverage. | style score | Five arbitrary labels counted as qualification. |
| CAL2 | Empirical calibration/learning gate over real performance evidence. | learning | Promoting causal rules from one high metric. |
| P0 | Hard correctness/security/product-authority blocker; overrides weighted scores. | critical | Cosmetic issue. |
| P1 | Material release/reliability/security gap that should close before production authority. | high | Optional enhancement. |
| DONE | Implementation + executed passing tests + security/doc/state/graph/evidence/handoff obligations satisfied. | complete | PR opened or code written only. |
| READY | Candidate has satisfied entry criteria for the next explicit transition, not necessarily release. | done | Green branch called production-ready. |
