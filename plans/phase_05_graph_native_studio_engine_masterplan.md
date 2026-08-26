# PHASE 05 — GRAPH-NATIVE MOTION.OS STUDIO ENGINE

Status: MASTER IMPLEMENTATION PLAN / proposed against verified current repo
North Star: compile creative direction + evidence + assets into an executable editing graph that can be retrieved, mutated, rendered, criticized, repaired and learned from without losing intent or provenance.

## 0. CURRENT REPO TRUTH / DELTA

Existing strengths to preserve and extend:
- `src/graph/{model,impact,patch_planner,runtime_mutation,scheduler}.py`: causal graph + impact/repair foundations.
- `src/extraction/*`: real FFmpeg/OpenCV/OCR/audio evidence providers and FeaturePack path.
- `src/knowledge/{style_signature,style_store}.py`: SQLite style signatures/retrieval seed.
- `src/compilers/{remotion,framer}.py`: compiler seed.
- `src/renderers/{contracts,router,partial,compositor,source_generators}.py`: renderer abstraction/partial render seed.
- `src/qa/*`: creative, grammar, semantic, multimodal, release and Gauntlet foundations.
- `src/agents/pipeline.py`: orchestration seed.
- schemas: FeaturePack, MotionStyle2JSON, SVG reconstruction.
- `/plans` living-plan protocol, `director.md`, motion grammars and Visual DNA taxonomy.

Missing to reach Studio Engine:
1. typed EditingGraph ontology spanning creative semantics → render nodes;
2. graph-native RAG over references/styles/motion/success/failure/renderer history;
3. first-class Skill Registry and capability/fallback DAG;
4. provider layer for external reference/asset discovery with licensing/provenance;
5. Director OS compiler into structured creative graph;
6. canonical layer/track/beat/audio/camera graphs;
7. renderer compilers for HyperFrames + Lottie and stronger Remotion execution;
8. graph-aware asset intelligence and composition blueprints;
9. QA/repair as graph mutations with affected-subgraph rerender;
10. editor/preview/observability and end-to-end release evidence.

Rule: extend existing modules; do not create parallel replacement architectures unless migration is explicit.

---

# 1. TARGET REPRESENTATION — THREE LEVELS

## L1 Semantic / Creative Graph
Nodes: Project, Brief, Intent, EmotionState, NarrativeBeat, BrandRule, AttentionTarget, ProductSemantic, StyleSignature, MotionGrammar, NegativeConstraint.

## L2 Editing / Motion Graph
Nodes: Scene, Shot, Layer, Track, Asset, AssetVariant, Primitive, Transition, CameraRig, Material, LightRig, TypographyRole, AudioCue, MusicBeat, VoiceLine, Effect, Mask, CompositionBlueprint.

## L3 Render / Evidence Graph
Nodes: Renderer, Skill, Provider, ToolCall, Composition, RenderRegion, Artifact, Run, QAResult, Defect, RootCause, RepairCandidate, Release.

Invariant: render-specific implementation never becomes the source of creative intent. L3 must be regenerable from L1+L2+capabilities.

---

# 2. CANONICAL LAYER STACK
L0 ENVIRONMENT
L1 BACKGROUND_GRAPHICS
L2 FOOTAGE_PLATES
L3 SUBJECT
L4 MIDGROUND
L5 PRIMARY_UI
L6 TYPOGRAPHY
L7 FOREGROUND
L8 FX
L9 CAPTIONS_BRAND

Each Layer node requires: stable id, layer_class, z, continuity_id, asset_ref?, semantic_role, attention_role, entry/settle/exit contract, renderer_support, provenance refs.

---

# 3. GRAPHRAG MEMORY PLANES
- Reference Memory
- Style Memory
- Motion Memory
- Success Memory
- Failure Memory
- Renderer Memory
- Asset Memory
- User Feedback Memory

Retrieval order:
1. hard graph filters;
2. graph neighborhood traversal;
3. semantic/vector similarity;
4. historical QA/user-feedback reranking.

Initial stack: NetworkX MultiDiGraph + SQLite + inspectable vectors. Do NOT add external graph/vector DB until corpus/latency benchmarks prove need.

Reference ranking target:
`0.25 semantic + 0.20 style + 0.15 motion + 0.10 composition + 0.10 brand compatibility + 0.10 historical QA + 0.10 user approval`, after hard license/renderer/aspect/asset filters.

---

# 4. SKILL RUNTIME CONTRACT
Every skill must declare:
- skill_id/version;
- input/output schemas;
- required capabilities;
- tools/providers;
- authority level;
- deterministic flag;
- cost/latency class;
- failure modes;
- fallbacks;
- QA contract;
- graph node/edge effects.

No agent may call a tool merely because it exists; skill dependency resolution chooses an ordered executable path.

---

# 5. PROVIDER POLICY
Providers: Pinterest reference discovery, Pexels stock/photo/video, Flaticon icon/vector discovery, Swishy code/composition references, local/library, generated assets.

All provider results enter as candidates, never trusted assets. Required lifecycle:
DISCOVER → LICENSE/POLICY → HASH → QUALITY → SEMANTIC FIT → STYLE FIT → TECH FIT → PROVENANCE → REGISTER.

Pinterest defaults to reference/mood/composition discovery; no assumption of downstream commercial asset rights.
Swishy defaults to pattern/reference extraction, not blind template copying.

---

# 6. RENDERER ROUTING
Remotion: deterministic React/video/data-driven compositing, server rendering, partial/frame workflows.
HyperFrames: HTML/CSS/GSAP, UI motion, kinetic type, SVG, web-native/audio-reactive compositions.
Lottie: portable vector components/microinteractions/icons; not the universal full-video compositor.
SVG+JS: exact reconstruction/vector deterministic playback.
FFmpeg: media normalization, splice, encode, mux, region extraction.
Generated video: plates/organic/cinematic regions only, isolated behind evidence/provenance contracts.

Routing is per subgraph/layer, not necessarily per whole video.

---

# 7. IMPLEMENTATION PROGRAM — 16 PHASES / 32 ORDERED PRs

## P05.0 — Baseline Freeze & Architecture Contract
Goal: freeze current verified behavior and create migration map.
CP: current graph/extraction/renderer/QA tests green; no duplicate architecture.
PR-01 `docs: Studio Engine architecture + ADRs + migration map`
PR-02 `schema: editing graph + skill + provider asset contracts`
Exit: schemas validate representative fixtures and map every current module to target ownership.

## P05.1 — Typed EditingGraph Core
Goal: extend current graph into typed heterogeneous MultiDiGraph.
Deliver: ontology, node/edge registry, validation, serialization, graph versioning, stable IDs.
PR-03 `feat(graph): typed editing ontology`
PR-04 `feat(graph): graph validation serialization and migrations`
CP: zero orphan required nodes; illegal edges rejected; deterministic round-trip.

## P05.2 — Impact / Dependency / Execution DAG
Goal: graph determines what must rerun after a mutation.
Extend existing `impact.py`, `scheduler.py`, `runtime_mutation.py`.
PR-05 `feat(graph): descendant impact and invalidation engine`
PR-06 `feat(graph): topological execution planner and cache keys`
CP: typography change does not rerun OCR; source-video change does invalidate extraction descendants.

## P05.3 — Director Compiler
Goal: compile `director.md` into structured graph instead of leaving it prompt-only.
Outputs: IntentGraph, EmotionCurve, AttentionGraph, TemporalArchitecture, PhysicsProfile, CameraPlan, TypographyPlan, MaterialPlan, AudioPlan, ContinuityPlan, BrandMotionLanguage, NegativeRules.
PR-07 `feat(direction): director OS structured contracts`
PR-08 `feat(direction): brief-to-director graph compiler`
CP: 100% beats have intent + attention target + narrative function; movement without purpose is rejected.

## P05.4 — Canonical Editing Graph
Goal: beats/scenes/layers/tracks become one representation.
PR-09 `feat(editing): beat scene layer track graph`
PR-10 `feat(editing): camera depth material typography graphs`
CP: 100% timeline covered; no competing primary attention motions; transitions link adjacent states.

## P05.5 — Audio Graph
Goal: sound is choreographed, not post-added.
PR-11 `feat(audio): beat VO SFX event graph`
PR-12 `feat(audio): AV synchronization contracts and critic`
CP: major motion events can point to beat/accent/silence/VO evidence; intentional unsynced motion is explicit.

## P05.6 — Skill Registry & Runtime
Goal: replace ad-hoc tool use with typed skill execution.
PR-13 `feat(skills): registry contracts capability resolver`
PR-14 `feat(skills): dependency DAG fallback authority execution trace`
CP: unavailable capability cannot silently PASS; fallback provenance recorded.

## P05.7 — GraphRAG v1
Goal: graph-native retrieval using current SQLite StyleStore as seed.
PR-15 `feat(rag): graph neighborhood retrieval + hybrid ranking`
PR-16 `feat(rag): success failure renderer asset memory`
CP: retrieval explains why every candidate ranked; no opaque nearest-neighbor-only result.

## P05.8 — Provider & Asset Intelligence
Goal: pluggable external discovery without licensing/provenance loss.
PR-17 `feat(providers): provider contracts policy provenance`
PR-18 `feat(assets): candidate fitness license technical gates`
CP: every accepted external asset has provider, source ref, policy/license state, SHA256 and fitness evidence.

## P05.9 — Composition Blueprints / Lava-like Primitive System
Goal: reusable semantic motion components, not fixed templates.
Blueprints: Apple Product Reveal, SaaS UI Proof, Hyper Reward, Audio Pulse, Editorial Kinetic, Minimal Orbit, Portal Glass.
Primitive contract includes intent, channels, physics, easing envelope, attention role, supported renderers, forbidden combinations, QA.
PR-19 `feat(primitives): semantic Lava-like motion component contract`
PR-20 `feat(blueprints): graph-native composition blueprints`
CP: blueprints contain no fixed copy; primitive choice is semantic/grammar constrained.

## P05.10 — Remotion Production Compiler & Runtime
Goal: L1/L2 graph → actual deterministic Remotion composition/render.
Use current compiler as seed; align with current Remotion SSR `bundle → selectComposition → renderMedia` model and Player preview.
PR-21 `feat(remotion): editing-graph compiler + typed props`
PR-22 `feat(remotion): production renderer partial regions and preview`
CP: real MP4 from graph; deterministic replay; partial region render; renderer evidence stored.

## P05.11 — HyperFrames Production Compiler
Goal: graph → static hero layouts → deterministic HTML/CSS/GSAP timelines.
Hard rules: visual identity first, layout-before-animation, synchronous deterministic timelines, no random timing, transition contract.
PR-23 `feat(hyperframes): graph compiler and layout contracts`
PR-24 `feat(hyperframes): production render + partial composition evidence`
CP: at least one complex UI/kinetic composition renders from graph and round-trips timeline evidence.

## P05.12 — Lottie / SVG Interop
Goal: portable vector subgraphs and exact reconstruction bridge.
PR-25 `feat(lottie): supported-subset compiler validator`
PR-26 `feat(vector): embed Lottie/SVG subgraphs in Remotion/HyperFrames`
CP: unsupported Lottie features are rejected/quarantined, never silently approximated; stable IDs retained.

## P05.13 — Multi-Renderer Compositor
Goal: one project may route different subgraphs to different backends.
PR-27 `feat(render): multi-renderer graph router + manifests`
PR-28 `feat(render): FFmpeg assembly temporal/color/audio integrity`
CP: one benchmark combines Remotion + HyperFrames + Lottie/SVG/video plate with exact final duration and provenance.

## P05.14 — Graph QA & Autonomous Repair
Goal: critics attach defects to graph nodes and mutate only affected subgraphs.
PR-29 `feat(qa): graph-native technical grammar brand temporal critics`
PR-30 `feat(repair): root-cause subgraph branching tournament promotion`
CP: defect → root cause → candidate graph mutation → partial rerender → regression check → promote/rollback.

## P05.15 — Studio Preview / Observability / Release
Goal: inspect graph/timeline/assets/render state and make release reproducible.
PR-31 `feat(studio): graph timeline inspector + Remotion Player preview`
PR-32 `feat(ops): session-close observability recovery release attestation`
CP: zero-context agent can reconstruct current project; run manifests link Git SHA ↔ graph version ↔ assets ↔ renderer outputs ↔ QA ↔ Drive artifacts.

---

# 8. PR DEPENDENCY ORDER
01→02→03→04→05→06
then parallel lanes after ontology stabilizes:
- Creative lane: 07→08→09→10→11→12
- Runtime lane: 13→14→21→22→23→24→25→26→27→28
- Intelligence lane: 15→16→17→18→19→20
All converge: 29→30→31→32.

No PR > ~1 conceptual migration. Every PR requires tests, migration notes, plan delta and graph delta when relationships change.

---

# 9. CHECKPOINT SCORECARD
CP05-A Graph Integrity: >=9.5/10
CP05-B Director/semantic coverage: >=9.0
CP05-C Skill runtime reliability: >=9.5
CP05-D Retrieval relevance: >=0.85 human precision@5 on labeled corpus
CP05-E Asset provenance: 100%
CP05-F Remotion production path: VERIFIED
CP05-G HyperFrames production path: VERIFIED
CP05-H Lottie/SVG subset: VERIFIED/explicitly quarantined
CP05-I Multi-renderer temporal integrity: 100%
CP05-J Temporal/creative critic authority: VERIFIED
CP05-K Repair localization: unaffected-region regression within threshold
CP05-L Zero-context recovery: PASS

---

# 10. END-TO-END VALIDATION MATRIX
Must complete five authoritative projects:
1. Apple-premium desktop/product motion.
2. Gamified hyper-commercial.
3. Audio-driven hyper-commercial.
4. Editorial/cinematic product piece.
5. Exact reconstruction benchmark.

Each must exercise different graph topology, motion grammar and renderer mix.

Release-level DoD:
- zero orphan graph nodes;
- zero missing asset provenance;
- zero unresolved renderer assignments;
- zero unintended timeline gaps;
- zero invalid transitions;
- P0/P1 = 0;
- creative/semantic >=9 where applicable;
- text integrity strict;
- final hold stable;
- deterministic replay from manifests;
- APSR + GSR measured on benchmark corpus.

---

# 11. ANTI-OVERENGINEERING / SCALE TRIGGERS
Stay NetworkX + SQLite until one of these is measured:
- graph traversal latency exceeds target on representative corpus;
- corpus size makes in-process graph memory operationally unsafe;
- multi-worker concurrent graph mutation becomes a real requirement;
- SQLite retrieval latency/recall fails benchmark;
- external vector/graph DB yields measurable retrieval/ops gain.

Do not add Kafka/Kubernetes/distributed queues/vector DB/graph DB because they are fashionable.

---

# 12. NORTH-STAR EXECUTION FLOW
`Brief → DirectorGraph → GraphRAG → Reference/Asset candidates → VisualDNA evidence → MotionSystem → EditingGraph → Skill DAG → renderer routing → Remotion/HyperFrames/Lottie/SVG/video subgraphs → compositor → temporal/grammar/creative QA → DefectGraph → localized Gauntlet repair → release → success/failure memory`.

This plan supersedes ad-hoc plugin growth. Existing Phase 01–04 capabilities become upstream modules of the graph-native Studio Engine rather than parallel systems.
