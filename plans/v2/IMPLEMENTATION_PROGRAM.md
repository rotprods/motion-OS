# MOTION.OS V2 — Implementation Compiler

Authority: PROPOSED_V2
Tracker: Issue #78
Base: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`
Promotion barrier: Issue #48 OPEN

## Program law

Every task is `NOT DONE` until implementation + executed tests + security review + documentation/state/graph/evidence update + recoverable handoff are all satisfied. Architecture work may be verified on a branch but cannot self-promote to product/release authority.

## Objective checkpoints

| CP | Name | Entry | Exit / evidence | Promotion authority |
|---|---|---|---|---|
| CP0 | Live Truth Reconstructed | session identity exists | live main + #39 + #48 + canonical docs + active PR topology recorded | session may analyze |
| CP1 | Hypergraph Contract Verified | CP0 | schema + FormatChecker + semantic validator + no dangling refs + uncertainty ownership | branch-head VERIFIED |
| CP2 | Historical Regression Complete | CP1 | major pivots/escaped bugs/failure families mapped | architecture review |
| CP3 | Architecture Gaps Classified | CP2 | all P0/P1 owner/test/evidence path; priority matrix | planning authority |
| CP4 | V2 Architecture Frozen | CP3 | Executive V2 + authority/state/event/graph model + decisions + lexicon | contract work may start |
| CP5 | Core Contracts Frozen | CP4 | event/state/session/evidence/render/content contracts versioned | implementation lanes start |
| CP6 | Implementation Kernel Verified | CP5 | truth projector + execution graph + skill/runtime + renderer core green | integrated branch authority |
| CP7 | Recovery Verified | CP6 | cold rebuild from GitHub/event/evidence; Drive degradation explicit | recovery VERIFIED |
| CP8 | Agent Death Drill | CP7 | zero-context successor resumes <5 min without chat | continuity VERIFIED |
| CP9 | Concurrency Verified | CP6 | overlapping claims/stale writers/idempotency/fencing qualified at claimed topology | coordination VERIFIED |
| CP10 | Security Gauntlet | CP6 | boundary-specific adversarial suite + dependency/static gates; residual risks owned | security VERIFIED |
| CP11 | E2E Product Path | CP6/10 | brief→master and Source→publication lineage physically pass | functional VERIFIED |
| CP12 | Empirical Qualification | CP11 | current RC full-video critic + creative thresholds; CAL2/benchmark evidence | EMPIRICALLY_QUALIFIED |
| CP13 | Migration Complete | CP7/11 | stale/parallel authorities removed or SUPERSEDED; projections regenerated | release candidate |
| CP14 | Production Authority | CP10/12/13 | combined-head full gates + serial merge + post-main verification + events | production promotion |

---

# PHASE V2-P0 — Reconstruction & Freeze

Objective: establish present truth without mutating competing active contracts.

### V2-P0-T01 Live lifecycle compiler
- Inputs: GitHub main/PRs/branches/runs; Issue #39/#48.
- Outputs: revision-pinned topology snapshot.
- Dependencies: none.
- Affected nodes: Repository, Branch, PR, Commit, Barrier, Agent/Session.
- Risk: stale pagination or historical event mistaken as current.
- Tests: lifecycle ordering; closed≠merged; cancelled/skipped≠pass.
- Adversarial: main advances mid-compile → invalidate snapshot.
- Evidence: SHA + issue comment IDs + query timestamp.
- DoD: CP0.

### V2-P0-T02 Authority inventory
- Enumerate every stateful concept and its authority/replicas/projections/caches.
- Fail if two uncoordinated authorities exist for one present-tense concept.
- Evidence: authority matrix.

### V2-P0-T03 Historical chronology
- Reconstruct bootstrap → RC06 → Phase04/05 → Phase06 → Phase07 → Phase08.
- Produce SUPERSEDES/PREVIOUS_VERSION edges; never rewrite old claims.

---

# PHASE V2-P1 — Hypergraph & Ontology Kernel

Objective: one machine-readable temporal graph shared by architecture, execution and recovery.

### V2-P1-T01 Hypergraph schema
- Files: `schemas/v2_hypergraph.schema.json`.
- Tests: Draft202012 + real FormatChecker.
- Failures: malformed URI, timestamp, duplicate IDs, dangling refs.

### V2-P1-T02 Semantic validator
- Files: `scripts/validate_v2_hypergraph.py`.
- Property: uncertainty/risk nodes require owner + resolution path.
- Property: L0–L16 dimensions represented; domain dimensions explicit.

### V2-P1-T03 Graph snapshot
- Files: `graph/v2/motion_os_v2_hypergraph.json`.
- Must contain authority contradictions rather than resolve them silently.
- DoD: CP1.

---

# PHASE V2-P2 — Canonical Truth & Event Convergence

Objective: eliminate split-brain current state and establish one logical event semantics.

### V2-P2-T01 Canonical truth projector
- Dependency: PR #56 concepts + PR #58 event projector.
- Inputs: live GitHub lifecycle, promoted event history, immutable evidence.
- Outputs: machine current-state projection.
- Tests: contradictory STATE/project_state/HANDOFF fixture fails.
- Security: untrusted issue/comment cannot override lifecycle.

### V2-P2-T02 Event logical identity
- Identical logical event on multiple surfaces dedupes.
- Same identity + different payload → fail closed.
- Out-of-order replay must converge where aggregate revisions permit.

### V2-P2-T03 Projection generation
- Generate/validate STATE/TASKS/HANDOFF/ACTIVE_AGENTS/operator view from current projection.
- Each projection declares source_revision/watermark.
- DoD: no lifecycle contradiction in canonical views.

### V2-P2-T04 Cognitive barrier transaction
- Release requires fresh main + latest event watermark + combined-head proof.
- ContextPack invalidated on either drift.
- DoD contributes CP4/CP5.

---

# PHASE V2-P3 — Documentation & Lexicon Architecture

Objective: documentation becomes an information system, not parallel truth.

### V2-P3-T01 Canonical lexicon
- Closed authority vocabulary and semantic collision tests.

### V2-P3-T02 Documentation metadata contract
- Canonical docs declare authority, scope, owner, last_updated, source_revision, supersedes.
- Historical docs become SUPERSEDED; never silently edited into fake history.

### V2-P3-T03 ADR/decision index
- Every major decision captures alternatives, evidence, risks, reversibility, reconsideration trigger.

---

# PHASE V2-P4 — Correctness / Authority Hardening Train

Objective: absorb known escaped-bug families before product promotion.

### V2-P4-T01 Skill failure durability
- Source: PR #57.
- Invariant: executor exception → sanitized FAILED trace; downstream BLOCKED; strict mode carries persistable trace.

### V2-P4-T02 QA/repair semantics
- Source: PR #59.
- Invariant: run-scoped QA/Defect; RepairCandidate ADDRESSES defect and MUTATES actual target.

### V2-P4-T03 TTS semantic integrity
- Source: PR #71.
- Preserve value + class + structure; grouped/locale ambiguity fails closed.

### V2-P4-T04 Claim verification authority
- Source: PR #73.
- Timestamp/evidence attestation inseparable; direct-constructor bypass blocked.

### V2-P4-T05 Spend authorization domain validation
- Source: PR #74.
- Finite/nonnegative values; literal booleans; valid retry/concurrency counts; ambiguous provider acceptance reconciles.

### V2-P4-T06 Escaped-bug corpus
For each bug: ROOT_CAUSE → INVARIANT → WHY_TESTS_MISSED → REGRESSION → ADJACENT FAMILY → PROPERTY/FUZZ candidate.

DoD: zero unresolved P0/P1 in these scopes; exact-head clean runner.

---

# PHASE V2-P5 — Renderer Convergence

Objective: physically prove a heterogeneous renderer pipeline without hidden temporal/media assumptions.

### V2-P5-T01 Master audio authority
- Source: PR #61.
- Renderer-local audio never silently maps; one master graph; exact trim/pad/global t0.

### V2-P5-T02 Alpha evidence
- Source: PR #63.
- Probe actual pix_fmt/channel support; alpha expectation mismatch fails.

### V2-P5-T03 Color normalization
- Source: PR #69.
- Every input has evidence-backed color profile; unknown/HDR blocks until qualified policy.

### V2-P5-T04 HyperFrames production runtime
- Source: PR #62.
- Pinned runtime, standalone composition contract, frame_count/fps evidence, partial render.

### V2-P5-T05 Lottie browser runtime
- Source: PR #66.
- Pinned `lottie-web`, DOMLoaded, goToAndStop exact frames, PNG hashes, bundle integrity.

### V2-P5-T06 Heterogeneous master
- Same EditingGraph uses ≥2 renderer backends + vector component + video plate.
- Normalize time/z/audio/alpha/color.
- Physical tests: exact visual frames, dimensions, artifact hashes, layer ordering, audio mapping, deltaE/alpha samples.
- DoD: renderer stack VERIFIED; feeds CP6/CP11.

---

# PHASE V2-P6 — Temporal / Artifact Authority

Objective: bind full-video reasoning to the exact physical candidate.

### V2-P6-T01 Recover RC09E artifact
- Locate authoritative bytes or declare unrecoverable and generate a new versioned candidate; never infer from report.
- Register SHA256, fps, frame_count, dimensions, audio, provenance.

### V2-P6-T02 Full-video temporal critic execution
- Source contract: PR #65.
- Trusted provider identity/run ID + complete artifact attestation.
- Timestamped defects must bind sampled frame evidence.

### V2-P6-T03 Evidence isolation adversarial suite
- Cross-media evidence attachment must fail.
- Mutated media with same filename must fail.
- Incomplete sample set cannot release.

DoD: temporal evidence VERIFIED for exact candidate.

---

# PHASE V2-P7 — Creative / Visual DNA Qualification

Objective: return engineering effort to visible product quality.

### V2-P7-T01 Creative tournament
- Candidate media SHA must match temporal evidence SHA.
- Thresholds: semantic≥9, motion≥9, typography≥9, transition≥8.8, finish≥9; P0/P1=0.

### V2-P7-T02 Primitive ledger
- Source: PR #67.
- Qualify all 45 primitives across declared renderer fixtures; historical 15/30 aggregate grants no per-ID authority.

### V2-P7-T03 Visual DNA corpus
- ≥10 heterogeneous references, measured FeaturePacks, evidence coverage/taxonomy consistency.
- Persist signatures; evaluate retrieval precision; physically render ≥3 analyzed references.

### V2-P7-T04 GraphRAG quality
- Hard license/renderer/type filters → graph traversal → similarity → QA/user-feedback rerank.
- Similarity never authorizes.

DoD: candidate creative score evidence + Visual DNA retrieval evidence.

---

# PHASE V2-P8 — Security, Supply Chain, Recovery & Admin

Objective: prove the system survives malicious input, agent death and infrastructure loss.

### V2-P8-T01 Security gauntlet
- Prompt injection, provider poisoning, secrets/PII, path traversal, SSRF/file URLs, shell/filter injection, media parser abuse, authority spoofing, stale writer, duplicate spend, performance poisoning.
- Source: PR #70 static gate + boundary-specific tests.

### V2-P8-T02 Supply-chain reproducibility
- Pin Actions by immutable SHA; renderer lockfiles; `npm ci` where qualified; dependency audit.

### V2-P8-T03 Cold recovery
- Delete chat/local checkout/caches/projections/local DB.
- Rebuild from GitHub + event history + available artifact evidence.
- Drive absence = DEGRADED_EXTERNAL, never fabricated recovery.

### V2-P8-T04 Agent-death drill
- Fresh agent obtains North Star/current objective/main/watermark/active claims/PRs/tests/artifacts/blockers/risks/next action within 5 minutes.

### V2-P8-T05 Main protection
- External admin applies ruleset requiring merge authority/no force push/deletion.
- Readback required; until then state remains BLOCKED_EXTERNAL.

DoD: CP7/CP8/CP10.

---

# PHASE V2-P9 — Product Benchmark & Phase06 Empirics

Objective: prove repeatability beyond one attractive master.

### V2-P9-T01 25-brief benchmark
- 5 style families; render, label and score all briefs.
- Compute APSR/GSR from artifact-bound evidence.

### V2-P9-T02 Phase06 CAL2
- ≥30 real productions across ≥5 topic families.
- Performance observations remain observational until causal experiment exists.

### V2-P9-T03 End-to-end Phase06 identity drill
SOURCE→CLAIMS→ICP→DRIVER→ANGLE→HOOK→BEATS→SCRIPT→TTS→AVATAR→RENDER→PRV→MNF→STUDIO→PUBLICATION→PERFORMANCE.
- content_id/PRV/MNF/Beat IDs fail closed on mutation.

DoD: CP12 empirical evidence where applicable.

---

# PHASE V2-P10 — Complexity / Performance Refactor

Objective: remove accidental complexity without weakening guarantees.

### V2-P10-T01 Critical-path measurement
- Task duration, queue time, retries, CI cost, provider latency, human wait, coordination overhead.

### V2-P10-T02 Delete/deprecate duplicates
- Find dead superseded adapters, parallel schemas, duplicate config representations and historical current-state surfaces.
- Delete only after consumer graph proves no required path.

### V2-P10-T03 Scale trigger review
- Evaluate NetworkX/SQLite against measured corpus/latency/concurrency.
- External graph/vector/distributed infra remains DEFERRED unless threshold crossed.

---

# PHASE V2-P11 — Recovery Graph / State Projection Hardening

Objective: prove graph/state can be destroyed and recreated.

### V2-P11-T01 Projection deletion drill
- Delete derived COS/ContextPack/State snapshots and reconstruct same important topology/hashes within tolerance.

### V2-P11-T02 Event replay corruption drill
- Duplicate, reorder, stale revision, conflicting logical duplicate, interrupted snapshot.
- Expected: idempotent convergence or fail closed.

### V2-P11-T03 Stream integrity
- Snapshot binds sequence/watermark plus content-root/hash-chain evidence when promoted.

---

# PHASE V2-P12 — Concurrency / Distributed Semantics Qualification

Objective: claim only the concurrency topology actually tested.

### V2-P12-T01 Single-host contention
- concurrent workers, lease expiry, stale fencing token, retry/reconcile.

### V2-P12-T02 Multi-host trigger decision
- If no real multi-host need: explicit NOT_APPLICABLE/DEFERRED.
- If triggered: design transactional outbox/idempotent consumer backend and execute distributed campaign before authority upgrade.

DoD: CP9 at claimed topology only.

---

# PHASE V2-P13 — E2E Studio Engine

Objective: prove the full brief→master operating system.

Flow:
Brief → DirectorGraph → GraphRAG → assets → VisualDNA → MotionSystem → EditingGraph → Skill DAG → renderer routing → compositor → temporal/creative critics → DefectGraph → localized repair → release manifest.

Tests:
- Apple-premium product/UI;
- gamified commercial;
- audio-driven commercial;
- editorial/cinematic;
- exact reconstruction.

DoD: CP11.

---

# PHASE V2-P14 — Migration & Supersession

Objective: move V1/current reality to V2 without historical deletion.

Steps:
1. promote converged truth/event contracts after barrier release;
2. regenerate state projections;
3. serially promote correctness branches against fresh main;
4. integrate renderer branches and physical master proof;
5. promote temporal/product evidence contracts;
6. mark old docs/contracts SUPERSEDED with source revision;
7. remove duplicate authority paths only after recovery proof.

Rollback: preserve previous main, RC06 artifact/registry and event history; migration must be forward/replay safe.

DoD: CP13.

---

# PHASE V2-P15 — Empirical Qualification

Objective: establish real product reliability, not just code correctness.

Requires:
- current candidate artifact recovered/versioned;
- full-video trusted critic;
- creative tournament thresholds;
- benchmark APSR/GSR;
- primitive ledger;
- Visual DNA corpus/retrieval;
- CAL2 where performance claims are made.

DoD: CP12.

---

# PHASE V2-P16 — Final 20D Gauntlet

Objective: adversarially attack every COS dimension and major decision.

Campaigns:
- stale/duplicate/out-of-order events;
- main change after CI;
- agent death mid-task;
- overlapping contract edits;
- provider acceptance then timeout;
- artifact substitution;
- graph/state/DB deletion;
- Drive outage;
- malicious source/media/path/URL;
- false authority/self-promotion;
- metric gaming/template collapse;
- expensive CI/coordination overhead;
- product technically green but creatively weak.

Maximum identical repair strategy attempts: 3 → STUCK_LOOP.

DoD: no unresolved material defect from final questions; residuals are owned nodes.

---

# PHASE V2-P17 — Production Promotion

Entry: CP10+CP12+CP13 pass; Issue #48 barrier explicitly released.

Transaction:
1. reread latest event watermark + live GitHub;
2. invalidate stale ContextPack/evidence on drift;
3. run full combined-head MERGE_SAFE;
4. code + security review exact candidate;
5. merge one PR/workstream at a time;
6. verify `main` after each irreversible transition;
7. emit `pr.merged` + `main.verified` + release events;
8. reconstruct projections from authority;
9. run smoke + zero-context handoff.

Exit: CP14 Production Authority.

## Parallelization plan

- Lane A Truth/Event: P2.
- Lane B Core correctness: P4.
- Lane C Renderer: P5.
- Lane D Product/Temporal/VisualDNA: P6–P7.
- Lane E Security/Recovery: P8/P11.
- Lane F Empirical benchmark: P9.

Shared contract changes require explicit claims. Promotion convergence is serial even if implementation lanes are parallel.

## Next safe actions from current live truth

1. Keep V2 work additive/new-file-only while barrier active.
2. Qualify this hypergraph schema/validator in clean runner.
3. Let owners finish #56/#58/#57/#59/#61/#62/#63/#65/#66/#69/#70/#71/#73/#74 without V2 branch interference.
4. After truth/event convergence, recompile this V2 graph against the new main/watermark; stale V2 snapshot must invalidate itself.
5. Redirect execution capacity to RC artifact recovery + temporal/creative product qualification once safety train permits.
