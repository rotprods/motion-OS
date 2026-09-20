# MOTION.OS V2 — Decision Ledger

Authority: PROPOSED_V2 unless source authority says otherwise.
Source revision: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`

## D-V2-001 — Convergence, not rewrite
Problem: Current system has strong independently verified subsystems plus stale projections and unmerged convergence branches.
Selected: preserve verified capabilities and converge authority/contracts around them.
Alternatives: greenfield rewrite; freeze all feature work until total redesign.
Why selected: rewrite destroys working evidence and increases regression surface; current bottleneck is convergence/authority/product proof, not lack of architecture.
Risks: legacy coupling remains visible during migration.
Mitigation: typed boundaries, supersession ledger, staged migration, no silent replacement.
Reversibility: high.
Confidence: HIGH_CONFIDENCE.

## D-V2-002 — Few authoritative planes
Problem: Current-state split brain exists across Markdown/JSON/bootstrap/event surfaces.
Selected: live GitHub lifecycle for software; promoted durable domain stores for domain authority; immutable evidence; everything else projection/advisory.
Rejected: make COS authoritative; make STATE.md authoritative; let every store be eventually consistent authority.
Reason: authority must be reconstructable and conflict-detectable.
Risk: projection bugs.
Mitigation: deterministic projectors + drift CI + live overlay.
Reconsideration trigger: none; only implementation changes, not principle.
Confidence: HIGH_CONFIDENCE.

## D-V2-003 — One event semantics, multiple surfaces
Problem: Issue #39, repo immutable events and Runtime EventStore can look like three buses.
Selected: one logical event identity/dedupe semantics; surfaces are transports/authorities according to promotion state.
Rejected: independent event histories with later reconciliation.
Reason: contradictory duplicates would create multiple realities.
Risk: migration complexity while PR #58 is unpromoted.
Mitigation: fail-closed duplicate conflict, current promotion barrier, one-way projectors.
Confidence: HIGH_CONFIDENCE.

## D-V2-004 — Session is first-class
Problem: concurrent agents and context loss require durable work identity.
Selected: Project → Agent → Session → Workstream and all mutations/evidence linked to session/correlation.
Rejected: branch == session; chat == session.
Reason: branches are not ownership locks and chats are not durable authority.
Confidence: HIGH_CONFIDENCE.

## D-V2-005 — Three-level graph representation
Problem: renderer-specific details can leak upward and become creative truth.
Selected: L1 Semantic/Creative → L2 Editing/Motion → L3 Runtime/Evidence.
Rejected: one untyped mega-graph; renderer-native timeline as source of truth.
Reason: preserves intent and enables renderer replacement/partial rerender.
Tradeoff: compiler complexity.
Confidence: HIGH_CONFIDENCE.

## D-V2-006 — COS remains derived
Problem: graph reasoning is powerful enough to accidentally become hidden authority.
Selected: COS/Unified Graph is deterministic query/reasoning projection only.
Rejected: reverse-write from COS into authoritative state.
Reason: derived reasoning may be stale/inferred and must remain rebuildable.
Confidence: HIGH_CONFIDENCE.

## D-V2-007 — NetworkX + SQLite until measured trigger
Problem: desire for GraphRAG/distributed coordination can induce premature infrastructure.
Selected: in-process typed graph + SQLite where sufficient.
Rejected now: Neo4j/Memgraph/Pinecone/Redis/Kafka/Kubernetes/microservices.
Triggers for reconsideration: measured traversal/retrieval failure; unsafe corpus memory; real multi-host contention; HA requirement; multi-user SaaS; distributed background jobs.
Risk: later migration cost.
Mitigation: stable interfaces and exportable contracts now.
Confidence: HIGH_CONFIDENCE.

## D-V2-008 — frame_count/fps is visual duration authority
Problem: container/mux tail historically disagreed with rendered visual duration.
Selected: visual duration = exact frame_count / fps; mux duration remains separate observation.
Rejected: trust duration field alone.
Evidence: historical regression + multi-render physical proof.
Confidence: HIGH_CONFIDENCE.

## D-V2-009 — Provider acceptance requires reconciliation before retry
Problem: timeout after remote acceptance can duplicate paid work.
Selected: ambiguous/known provider job → RECONCILE_REQUIRED; no blind retry.
Rejected: retry on transport timeout.
Confidence: HIGH_CONFIDENCE.

## D-V2-010 — Evidence identity is mandatory
Problem: high score/test can be attached to wrong media/run.
Selected: evidence binds artifact SHA, run/provider, graph/source revision, candidate identity and temporal scope.
Rejected: filename/title/score-only attachment.
Confidence: HIGH_CONFIDENCE.

## D-V2-011 — Product score and promotion-risk score are separate
Problem: regression work can optimize architecture while product output stagnates.
Selected: product North Star weights remain Creative 45 / Trust 20 / Autonomy 20 / Engineering 15; Issue #48 risk score gates safety separately.
Rejected: one composite score.
Reason: a safe bad video is still product failure; a beautiful unsafe system cannot ship.
Confidence: HIGH_CONFIDENCE.

## D-V2-012 — Similarity never grants authority
Problem: embeddings/GraphRAG can retrieve plausible but wrong evidence.
Selected: similarity ranks candidates only after hard filters and graph/evidence constraints.
Rejected: nearest neighbor as proof.
Confidence: HIGH_CONFIDENCE.

## D-V2-013 — Multi-renderer per subgraph/layer
Problem: no single renderer is optimal for UI, video plates, vector microinteraction and deterministic compositing.
Selected: route layers/subgraphs to Remotion/HyperFrames/Lottie/SVG/video then normalize and composite.
Rejected: renderer-per-project monolith.
Risk: clock/z/audio/alpha/color complexity.
Mitigation: explicit assembly contracts and physical heterogeneous-master test.
Confidence: HIGH_CONFIDENCE.

## D-V2-014 — Lottie is portable vector subset, not universal compositor
Problem: unsupported expressions/features can be silently approximated.
Selected: explicit supported subset + reject/quarantine unsupported features.
Rejected: best-effort conversion.
Confidence: HIGH_CONFIDENCE.

## D-V2-015 — Human/operator docs are projections
Problem: STATE/TASKS/HANDOFF drift proves hand-maintained truth does not scale.
Selected: human views generated/validated from canonical state/event/lifecycle evidence.
Rejected: periodic manual reconciliation as normal operation.
Risk: projector failure can make docs stale.
Mitigation: source_revision metadata and drift gate.
Confidence: HIGH_CONFIDENCE.

## D-V2-016 — Local-first verification, cloud merge authority
Problem: CI used as interactive debugger burns resources and conflates environment evidence.
Selected: local quick/analysis/remotion/security/merge profiles first; clean runner proves exact candidate; combined-head proof after main drift.
Rejected: cloud-only iteration.
Confidence: HIGH_CONFIDENCE.

## D-V2-017 — Authority vocabulary is closed
Selected states: PROPOSED, IMPLEMENTED, EXECUTED, VERIFIED, EMPIRICALLY_QUALIFIED, BLOCKED, DEGRADED_EXTERNAL, SUPERSEDED.
Rule: Authority = min(Build, Assurance). Closed PR != merged; merged != verified; skipped/cancelled != pass; local contention != distributed authority.
Confidence: HIGH_CONFIDENCE.

## D-V2-018 — V2 promotion remains blocked while Issue #48 is open
Problem: architecture synthesis must not become implicit release.
Selected: branch-head artifacts may reach VERIFIED_BRANCH_HEAD_NOT_PROMOTED evidence, never V2_FINAL/main promotion without current barrier release and combined-head train.
Evidence: Issue #39/#48 current truth.
Confidence: HIGH_CONFIDENCE.
