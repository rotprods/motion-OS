# MOTION.OS V2 — Implementation Compiler Output

Authority: PROPOSED_V2_CANDIDATE
Program ID: `motion://program/v2-architecture-migration`
North Star: `motion://northstar/professional-motion-master`
Source revision: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`

## Program laws

A task is not DONE because code exists. DONE requires implementation + executed passing tests + security implications reviewed + docs/state/graph/evidence updated + no unresolved P0/P1 introduced + zero-context handoff.

No task may merge using stale main/event-watermark evidence. Active implementation PR owners remain owners; this program coordinates and compiles, not duplicates them.

## Milestone M0 — V2 truth and graph freeze

### Phase P0 — Live truth reconstruction
Objective: current lifecycle, barriers, active claims and source-of-truth hierarchy become machine-queryable.

- `V2-P0-T01` Reconcile live main/open PRs/issues/rulesets with canonical state projections.
  - Inputs: GitHub live, Bus #39, Issue #48, project state, ACTIVE_AGENTS.
  - Outputs: exact topology snapshot.
  - Affected nodes: Authority, PullRequest, Agent, Session, Barrier.
  - Tests: stale lifecycle; merged PR marked active; closed-unmerged vs merged distinction.
  - Evidence: live API snapshot + state hash.
  - Owner type: authority/state agent; #56 current owner.
  - DoD: zero contradictory current lifecycle facts.

- `V2-P0-T02` Mark bootstrap/stale docs as historical or projections; no silent authority.
  - Dependencies: T01.
  - Tests: doc metadata validation.
  - Rollback: docs-only revert.

### Phase P1 — Hypergraph + ontology
Objective: one shared ID/edge vocabulary across execution, evidence, risk, decisions and agents.

- `V2-P1-T01` Freeze V2 node/edge/hyperedge ontology.
  - Inputs: `hypergraph.snapshot.json`, current domain schemas.
  - Output: schema + lexicon.
  - Tests: duplicate ID, dangling edge, invalid edge type, unknown state.
  - Owner: graph architecture workstream.

- `V2-P1-T02` Implement deterministic V2 package validator.
  - Inputs: graph/tasks/checkpoints/state JSON.
  - Outputs: fail-closed CLI/test.
  - Tests: broken refs, dependency cycles in checkpoint DAG, invalid task evidence links.
  - Risk: validator becomes second authority; mitigation: it validates documents, never writes domain state.

Checkpoint target: CP1 Graph Complete.

## Milestone M1 — Authority core converged

### Phase P2 — Event/state/session convergence

- `V2-P2-T01` Promote one Event Fabric semantics after current #58 qualification.
  - Owner: #58.
  - Required: identical logical event cross-surface dedupe; conflicting duplicate fail; sequence/watermark binding; live lifecycle overlay.
  - Tests: duplicate/out-of-order/late event, stale watermark, cross-session/correlation injection.

- `V2-P2-T02` Make all autonomous selectors/SDKs consume canonical conflict semantics.
  - Owner: #68 after #58.
  - Tests: same ADR/root-cause/authority/contract/architecture collision; authority precedence; malformed scopes fail closed.

- `V2-P2-T03` Agent-death/zero-context continuation drill.
  - Inputs: repo + Event Fabric + live GitHub + available evidence, no chat.
  - Output: North Star/current objective/main/watermark/owners/blockers/next-safe-task in <=5 minutes.
  - Evidence: sealed recovery report.

- `V2-P2-T04` Enforce COS projection no-reverse-authority.
  - Tests: graph deletion/rebuild; attempted reverse-write rejected.

Checkpoint targets: CP5 Core Contracts Frozen, CP8 Agent Death Drill, CP9 Concurrency Verified.

### Phase P3 — Content trust and provider boundaries

Parallel bounded PR train:

- `V2-P3-T01` Claim verification evidence binding (#73).
- `V2-P3-T02` TTS semantic class preservation (#71).
- `V2-P3-T03` Spend authorization finite/literal/current policy (#74).
- `V2-P3-T04` Provider telemetry validation/SSRF boundary (#76).
- `V2-P3-T05` Performance-learning evidence/causal authority (#77).

For each:
- exact-head clean-runner;
- mutation/adjacent failure-family tests;
- no claim beyond classifier-executed jobs;
- combined-head qualification when entering train.

Checkpoint: content/avatar trust boundary has zero known P0/P1.

## Milestone M2 — Truthful render and repair kernel

### Phase P4 — QA Graph + common EvidenceEnvelope

- `V2-P4-T01` Converge #59 with stronger #60 invariants.
  - Atomic preflight all generated identities before graph mutation.
  - Reject `run_id` alias to non-Run node.
  - Preserve run-scoped history.
  - `RepairCandidate DERIVED_FROM Defect`; MUTATES only actual target.

- `V2-P4-T02` Define/adapter-map common promotion EvidenceEnvelope.
  - Fields conceptually: subject_id, source_revision/hash, spec/contract hash, runtime/provider identity, run_id, artifact/media hash, evidence revision, authority state.
  - Do not break active contracts; introduce adapters after impact analysis.
  - Property: evidence from artifact A cannot authorize artifact B.

- `V2-P4-T03` Evidence cross-attachment adversarial suite.
  - Cases: wrong media SHA, wrong provider run, wrong source manifest, stale candidate, tampered evidence revision.

Checkpoint: CP6 Implementation Kernel Verified.

### Phase P5 — Renderer fabric production contracts

Parallel owners, serialized where files overlap:

- `V2-P5-T01` Master audio exact single-authority assembly (#61) — preserve physical proof.
- `V2-P5-T02` HyperFrames provenance binding (#62): spec/source manifest + HyperFrames version + run + artifact.
- `V2-P5-T03` Alpha semantic composite proof (#63): not just alpha plane presence; expected transparent/opaque pixels survive compositor.
- `V2-P5-T04` Color normalization integration (#69): explicit input profiles -> canonical BT.709 working/output space; physical heterogeneous composite + ΔE/metadata evidence.
- `V2-P5-T05` Lottie official player physical qualification (#66).
- `V2-P5-T06` Remotion dependency lock/reproducibility: generate valid package-lock, switch clean runner to `npm ci`, bind dependency identity where appropriate.

Required test classes: physical runtime, deterministic re-render, malicious path/label safety, exact frame/fps, audio timing, alpha/color preservation.

Checkpoint: >=2 renderer paths physically verified with provenance-bound evidence.

## Milestone M3 — Temporal intelligence becomes authoritative

### Phase P6 — Frame authority / reverse engineering

- `V2-P6-T01` Refactor #64 exact-mode authority.
  - `RECONSTRUCT_EXACT` requires decoded frame count/time base.
  - Duration-derived estimates permitted only in explicit approximate/template modes.
- `V2-P6-T02` Real-video frame clock fixtures: VFR, CFR, container tail, audio tail, missing metadata.
- `V2-P6-T03` Editing template invariants separate content slots/style invariants/fidelity facts.

Checkpoint: every exact reconstruction fact has deterministic provenance.

### Phase P7 — Full-video temporal critic + release manifest

- `V2-P7-T01` Close #65 P0/P1 causality:
  - result provider_run_id == evidence provider_run_id;
  - sampled timestamp aligns to decoded frame clock within declared tolerance;
  - defect evidence frames intersect claimed temporal interval;
  - first/last frame binding;
  - media hash exact.
- `V2-P7-T02` Recover or regenerate a real canonical master with immutable SHA.
- `V2-P7-T03` Execute qualified full-video multimodal provider/critic.
- `V2-P7-T04` Run 15-dimension creative tournament.
- `V2-P7-T05` Emit release manifest binding candidate/media/evidence/ranking.
- `V2-P7-T06` Adversarial mutation: swap media, rankings, defects, provider result, sample clocks; every mismatch fails closed.

Checkpoint: CP11 E2E Product Path Passed.

## Milestone M4 — Empirical product authority

### Phase P8 — Primitive + benchmark + Visual DNA qualification

- `V2-P8-T01` Primitive ledger (#67): qualify exact primitive × declared renderer cases; no aggregate-only authority.
- `V2-P8-T02` Benchmark suite (#75): exact suite manifest and per-brief artifacts.
- `V2-P8-T03` Replace generic runtime-proof visual grammar where it fails style fidelity.
- `V2-P8-T04` Visual DNA extraction/retrieval: similarity can retrieve references, never grant authority.
- `V2-P8-T05` Unseen brief campaign across declared style families.
- `V2-P8-T06` Compute APSR/GSR only from exact suite evidence.

Acceptance: individual release-relevant creative quality >=9; mean >=9; no FAIL/BLOCKED/ambiguous evidence in qualifying suite.

### Phase P9 — CAL2 / learning loop

- `V2-P9-T01` Bind publication/performance records to exact content manifest.
- `V2-P9-T02` Deduplicate supporting examples; independent example count derives from IDs.
- `V2-P9-T03` Controlled-test identity required for causal promotion.
- `V2-P9-T04` Learning candidate -> controlled experiment -> promoted rule lifecycle.
- `V2-P9-T05` Poisoning tests: NaN/inf, duplicate support, cross-content attribution, truthy approval.

Checkpoint: CP12 Empirical Qualification Passed.

## Milestone M5 — Security, recovery and governed promotion

### Phase P10 — Assurance architecture

- `V2-P10-T01` Promote #70 high-signal static/dependency security gate after integration reconciliation.
- `V2-P10-T02` Add boundary-specific security suites: URL/SSRF consumer, media parser, path traversal, imported prompt/control-plane injection, artifact poisoning.
- `V2-P10-T03` Distinguish PASS/FAIL/SKIPPED/CANCELLED/NOT_RUN in evidence schema and reports.
- `V2-P10-T04` Mutation/property tests for historical escaped-bug families.
- `V2-P10-T05` SBOM/dependency identity policy when reproducible manifests exist.

Checkpoint: CP10 Security Gauntlet Passed.

### Phase P11 — Recovery + GitHub governance

- `V2-P11-T01` Cold restore: GitHub + immutable event history -> state + graph + next-safe-action.
- `V2-P11-T02` Drive missing -> explicit DEGRADED_EXTERNAL; never fabricate artifact authority.
- `V2-P11-T03` Apply GitHub-native main ruleset (external admin action): PR-only, required MERGE_SAFE, no force/delete, freshness/merge-group behavior.
- `V2-P11-T04` Adversarial admin proof: stale/unverified candidate cannot merge.

Checkpoint: CP7 Recovery Verified.

## Milestone M6 — Migration and production authority

### Phase P12 — Autonomous agent runtime activation

- `V2-P12-T01` Promote #58 first.
- `V2-P12-T02` Requalify #68 stacked against promoted Event Fabric.
- `V2-P12-T03` Keep external wakeup/autoloop disabled until security/governance gates are met.
- `V2-P12-T04` Activate bounded autonomous loop only for safe/reversible/evidence-backed tasks; kill switch and attempt cap remain mandatory.

### Phase P13 — Documentation/current-state migration

- `V2-P13-T01` Choose V2 docs as canonical architecture after review.
- `V2-P13-T02` Add authority headers to current canonical docs.
- `V2-P13-T03` Replace hand-maintained duplicated current state with generated/validated projections where justified.
- `V2-P13-T04` Create SUPERSEDED registry for older architecture docs/ADRs without deleting history.
- `V2-P13-T05` Update AGENTS/README/GOAL/STATE/TASKS/HANDOFF to V2 navigation and definitions.

### Phase P14 — Final product gauntlet

Run:
- full local merge profile;
- clean-runner full MERGE_SAFE on exact combined candidate;
- concurrency/replay/recovery/death drill;
- full-video temporal critic on real artifact;
- creative tournament;
- benchmark/unseen suite;
- security gauntlet;
- cost/performance report;
- 20D graph audit.

No P0/P1 may remain except explicit external blocker that itself prevents production promotion.

### Phase P15 — Controlled promotion train

Serialize by dependency, re-reading latest main + Event Fabric before every irreversible step. Indicative dependency order, not blanket merge authorization:

1. canonical truth/current-state convergence;
2. Event Fabric;
3. isolated content/security correctness PRs;
4. QA graph / exact frame authority;
5. renderer contracts;
6. temporal critic;
7. empirical qualification;
8. autonomous execution;
9. V2 documentation/state migration;
10. post-merge whole-main gauntlet.

Every main advance invalidates downstream stale proof.

Checkpoint: CP13 Migration Complete.

### Phase P16 — Production authority

Entry: CP0–CP13 applicable checkpoints passed.
Exit:
- North Star product E2E >= declared thresholds;
- P0=0/P1=0;
- main governance active;
- zero-context recovery passes;
- empirical suite passes;
- release artifact and rollback artifact recoverable and hash-bound;
- post-merge `main.verified` event emitted.

Checkpoint: CP14 Production Authority.

## Parallelization map

Can run concurrently when scopes remain isolated:
- content trust (#71/#73/#74/#76/#77);
- security (#70);
- primitive/benchmark ledgers (#67/#75);
- renderer-specific contracts (#62/#63/#66/#69) subject to shared assembly/runtime files;
- graph/refactor V2 documentation package.

Must serialize or explicitly coordinate:
- #58 Event Fabric -> #68 autonomous runtime;
- #59 QA graph before temporal repair integration;
- #64 frame authority with #65 temporal evidence semantics;
- #61 assembly before color/alpha integration touching same assembly surface;
- canonical state #56 before documentation/state migration;
- every merge against latest main.

## Exact current executable frontier

1. Finish branch qualification of this V2 package and publish PR.
2. Keep V2 isolated from active code owners.
3. Have #59 absorb remaining stronger #60 invariants and requalify.
4. Close #64 exact frame-authority gap and #65 temporal causality gap in coordination.
5. Complete HyperFrames provenance / alpha semantic composite / Node lockfile work.
6. Prepare external GitHub main ruleset application.
7. Recover or regenerate a real master artifact for full-video critic.
8. Once barrier criteria are actually met, run serialized promotion train rather than batch merges.
