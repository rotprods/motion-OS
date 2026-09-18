# MOTION.OS V2 — Canonical Lexicon

Authority: PROPOSED_V2 terminology contract.

| Term | Canonical definition | Aliases | Deprecated/unsafe usage |
|---|---|---|---|
| Authority | Maximum justified claim supported by both build and assurance evidence. | qualification | “works”, “done”, “ready” without evidence |
| PROPOSED | Designed but not implemented. | planned | complete |
| IMPLEMENTED | Code/config/contract exists. Execution not implied. | built | verified |
| EXECUTED | Relevant runtime path actually ran. Correctness beyond observed run not implied. | ran | production-ready |
| VERIFIED | Required tests/evidence passed for stated scope. | qualified branch/head | empirically excellent |
| EMPIRICALLY_QUALIFIED | Real-world/production corpus supports the product/domain claim. | CAL2 qualified | unit-tested |
| BLOCKED | Required external/internal prerequisite prevents justified continuation/promotion. | hard gate | failed, unless actual failure |
| DEGRADED_EXTERNAL | External dependency/evidence plane unavailable; system explicitly operates with reduced authority. | degraded | pass |
| SUPERSEDED | Historical entity retained for lineage but replaced as current authority. | deprecated historical | deleted truth |
| Live GitHub lifecycle | Current branch/PR/commit/merge state from GitHub API. | live repo truth | stale PR description |
| Event history | Durable ordered logical coordination/domain events with identity, causation, revisions and provenance. | event ledger | websocket/realtime notifications |
| Event Bus | Delivery/notification mechanism for events; never truth by itself. | transport | event store |
| Event Store | Durable event history and aggregate revision authority for its promoted domain. | ledger | cache |
| Projection | Deterministic/rebuildable view of authority. | read model, snapshot | independent source of truth |
| ContextPack | Sealed session context projection bound to live main/event watermark/revision. | context bundle | chat memory |
| COS | Rebuildable graph reasoning/query projection. | Unified Graph shadow | write authority |
| Session | Durable first-class execution identity for one material agent run. | run context | branch, chat |
| Workstream | Bounded objective/resource scope executed through one branch/ownership claim. | lane | session |
| Claim | Declared right/intention to mutate a resource scope under current revision. | ownership claim | branch ownership |
| Lease | Time-bounded mutable-scope authorization with fencing semantics where durable kernel applies. | lock | branch |
| Fencing generation | Monotonic token preventing stale writers from regaining authority. | fence token | lease counter reset |
| Artifact | Immutable/rendered/measured output identified by bytes/hash and metadata. | media output | filename-only identity |
| Evidence | Observation/test/run bound to exact subject identity and provenance. | proof item | opinion/score without binding |
| Observation | Measured fact that may support a claim but does not establish causation alone. | metric | causal rule |
| Fact | Evidence-supported statement within explicit scope/time. | known state | assumption |
| Assumption | Unproven premise required by reasoning and explicitly marked. | hypothesis input | fact |
| Hypothesis | Testable proposed explanation/relationship. | candidate rule | production authority |
| Decision | Selected option with problem, alternatives, evidence, tradeoffs and reconsideration trigger. | ADR outcome | undocumented convention |
| Invariant | Property that must remain true across valid system states. | hard rule | guideline |
| Regression | Previously working/invariant behavior becomes invalid. | escaped bug | any failure |
| Failure family | Generalized class surrounding an observed bug. | adjacent failures | single incident |
| Product score | Quality/utility score governed by North Star. | creative score | regression-risk score |
| Regression-risk score | Promotion safety/risk assessment. | assurance score | product quality |
| Visual duration | frame_count / fps for rendered visual timeline. | exact duration | mux/container duration |
| Runtime duration | Container/mux reported duration, preserved separately. | mux tail | visual duration |
| Renderer | Backend executing render subgraphs/layers. | Remotion, HyperFrames | creative authority |
| Primitive | Reusable semantic motion behavior with renderer mappings and QA constraints. | motion component | fixed template |
| Blueprint | Structural composition topology/grammar without fixed copy. | composition archetype | template clone |
| GraphRAG | Retrieval combining hard graph filters, traversal, semantic similarity and evidence/history reranking. | graph retrieval | vector nearest-neighbor authority |
| L1 Semantic Graph | Intent/emotion/narrative/attention/brand/constraint layer. | creative graph | renderer timeline |
| L2 Editing Graph | Scene/layer/track/asset/camera/audio/primitive/transition layer. | motion graph | runtime evidence |
| L3 Runtime Graph | Skill/provider/renderer/tool/artifact/QA/repair/release layer. | evidence graph | semantic source |
| PRV | Stable Phase06 production/review identity; fail closed at Studio boundary. | — | recomputed ID |
| MNF | Stable Phase06 manifest identity; fail closed at Studio boundary. | — | regenerated identity |
| Beat ID | Stable semantic beat identity through Phase06 lineage. | beat key | array index |
| Canonical current state | Highest-authority present-tense state after live lifecycle/domain authority reconciliation. | truth projection | stale Markdown |
| Historical truth | Immutable record of what was believed/observed/valid at a past revision. | lineage | current state |
| Recovery | Reconstruction from durable authority without chat/local caches. | cold rebuild | copying stale projections |
| Agent-death drill | Test that successor resumes objective/state/ownership/tests/blockers/next action without prior chat. | continuity drill | hand-written summary only |

## Semantic collision rules

- `VERIFIED` always names scope; never imply empirical product quality.
- `current`, `active`, `ready`, `done`, `complete` are prohibited in machine authority unless paired with canonical state enum + source revision.
- `event bus`, `event store`, `event ledger` are not interchangeable.
- `similar`, `correlated`, `associated` never imply `CAUSES`.
- `closed PR` never implies `merged`; `merged` never implies `verified`; `CI skipped/cancelled` never implies pass.
- `single-host concurrency` never implies multi-host/distributed authority.
- `artifact name/path` never substitutes SHA-bound identity.
