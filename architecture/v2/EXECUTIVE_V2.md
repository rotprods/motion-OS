# MOTION.OS V2 — Executive Architecture

Authority: PROPOSED_V2 / branch-head only
Scope: architecture synthesis; no production authority
Source revision: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`
Session: `motion://session/chatgpt/graph-refactor-v2/20260829T234000+0200`
Tracker: Issue #78
Barrier: Issue #48 OPEN; no BARRIER RELEASE observed

## North Star

**Brief → professional motion-design master**, with autonomous research, reference intelligence, assets, direction, composition, motion, audio, deterministic rendering, temporal/creative QA, graph-native repair, provenance, reproducible release and zero-context recovery.

Architecture is subordinate to product quality. Product scoring and regression-risk scoring remain separate. Product weight remains Creative Quality 45% / Trust & Evidence 20% / Autonomy 20% / Engineering Quality 15%; hard correctness/security/authority blockers override both.

## V2 thesis

V2 is not a rewrite. It is a **convergence architecture** around capabilities that already work:

1. **Authoritative planes stay few and explicit.**
   - GitHub `main` + exact lifecycle = software authority.
   - Durable event history = coordination history authority when promoted.
   - Phase06 transactional SQLite = current single-host paid-render authority.
   - Artifact bytes + hashes = artifact authority; Drive is a durable artifact/recovery plane only when evidence is available.
   - Everything else—Markdown state, ContextPack, COS, dashboards, ACTIVE_AGENTS—is a rebuildable projection.

2. **One canonical semantic model, many projections.**
   Runtime EventStore, immutable repo events and Issue #39 are surfaces of one event semantics, not independent buses. Identical logical events deduplicate; contradictory duplicates fail closed. Live GitHub lifecycle overrides stale lifecycle projections.

3. **Three graph levels prevent renderer leakage into creative intent.**
   - L1 Semantic/Creative: brief, intent, emotion, narrative, attention, brand, constraints.
   - L2 Editing/Motion: beats, scenes, layers, tracks, assets, camera, audio, primitives, transitions.
   - L3 Runtime/Evidence: skills, providers, renderers, tool calls, artifacts, QA, defects, repairs, releases.
   L3 must be regenerable from L1+L2+capability inventory.

4. **Session is first-class.**
   Project → Agent → Session → Workstream → Events/Tasks/Decisions/Resources/Branch/PR/Commit/TestRun/Evidence/Handoff. A session cannot exist only in chat.

5. **Evidence has artifact identity.**
   Scores, tests and authority never float free. Evidence binds to exact artifact SHA, run/provider identity, graph revision, source revision and relevant state/event watermark.

6. **Fail closed at authority boundaries.**
   Unknown color metadata, malformed spend values, duplicated event payloads, stale main, unsupported Lottie features, ambiguous paid-provider status, unbound temporal critique, missing PRV/MNF/Beat identity: block rather than guess.

7. **Local-first, cloud-authoritative merge train.**
   Local verification finds cheap defects. Clean-runner MERGE_SAFE proves exact candidate. Main advancement invalidates stale proof. Cancelled/skipped/not-run are not PASS.

8. **Infrastructure follows measured triggers.**
   NetworkX/SQLite/local processes remain preferred. Postgres/Redis/Kafka/Kubernetes/vector DB/CDN/distributed workers require measured contention, HA, multi-user SaaS, distributed jobs or performance evidence.

## Current → V2 delta

### KEEP
- physical FFmpeg/OpenCV/OCR/audio extraction;
- FeaturePack and MotionStyle evidence boundary;
- Remotion verified production runtime;
- typed EditingGraph/impact/partial rerender foundations;
- Phase06 sealed lineage + transactional single-host authority;
- local-first MERGE_SAFE discipline;
- EventStore/EventBus separation and idempotency model;
- COS as one-way rebuildable reasoning projection;
- creative Director OS and semantic-before-effects rule.

### REFINE
- current-state files become validated/generated projections, not hand-maintained authority;
- event surfaces converge on one logical identity/dedupe contract;
- renderer routing gains complete time/z/audio/alpha/color proof;
- GraphRAG retrieval becomes evidence/history-aware, never similarity-authoritative;
- QA/repair IDs and mutations remain run/artifact scoped;
- session/workstream ownership becomes queryable and recovery-safe.

### MIGRATE
- stale RC06/RC07/RC09E state statements → one candidate-bound canonical state projection;
- bootstrap Issue #39 coordination → promoted Event Fabric when #48 release conditions are met;
- historical aggregate primitive claims → ID-bound qualification ledger;
- hand-authored README/STATE/TASKS/HANDOFF lifecycle claims → projector-backed views.

### DEPRECATE
- any independent mutable `current truth` Markdown;
- branch-name-as-ownership semantics;
- sampled/contact-sheet QA presented as full-video semantic authority;
- similarity score as evidence;
- implicit renderer-local audio selection;
- mux duration as visual duration authority;
- generic `verified/ready/complete` language without Build/Assurance evidence.

### DEFER
- multi-host coordination backend;
- general distributed queue;
- external vector/graph DB;
- Kubernetes/microservices;
- CDN/asset distribution tier;
- autonomous paid/provider execution without explicit bounded authority.

## V2 authority hierarchy

1. **Live GitHub lifecycle** — branch/PR/commit/merge/current-main facts.
2. **Exact durable domain authority** — promoted EventStore for coordination aggregates; Phase06 transactional store for single-host render intent; artifact SHA-bound registries for media.
3. **Immutable evidence** — repo events, test runs, render manifests, provider attestations, benchmark artifacts.
4. **Deterministic projections** — State Snapshot, ContextPack, Unified Graph/COS, STATE/TASKS/HANDOFF, operator views.
5. **Advisory surfaces** — Issue comments, Todoist, chat memory, embeddings/similarity, heuristics.

Lower levels never override higher ones.

## System boundaries

### Creative Intelligence
Brief → DirectorGraph → GraphRAG references → Visual DNA → MotionSystem → EditingGraph.

### Asset Intelligence
Provider candidate → trust/license/provenance → hash → semantic/style/technical fitness → registered asset/reference.

### Execution
EditingGraph → Skill DAG → per-layer renderer routing → Remotion/HyperFrames/Lottie/SVG/video plates → normalized multi-render compositor.

### Assurance
Physical verification → temporal critic → creative tournament → defect graph → localized repair → regression-protected rerender → release manifest.

### Coordination
Agent/session identity → preflight → scope claim → event append → work/checkpoint → handoff/release → replay → projections.

### Phase06 Content
SOURCE → CLAIM → ICP → DRIVER → ANGLE → HOOK → BEATS → SCRIPT → TTS → AVATAR → RENDER → PRV → MNF → STUDIO → PUBLICATION → PERFORMANCE.
Stable `content_id`, PRV, MNF and semantic Beat IDs never silently recompute.

## Critical current defects V2 must absorb, not hide

- P0: `STATE.md`, `project_state.json`, `TASKS.md`, `HANDOFF.md` disagree on candidate/remotion authority.
- P0 governance: `main` is not administratively protected.
- P0 product: RC09E physical artifact is not recoverable from inspected GitHub surfaces; full-video critic cannot be empirically qualified against it.
- P0 promotion: Event Fabric v3 remains branch-head verified but not promoted; Issue #48 remains open.
- P1 recovery: Drive evidence plane is externally degraded/unqualified in inspected sessions.
- P1 renderer: HyperFrames physical runtime, Lottie player proof, cross-render audio/alpha/color convergence are still branch/workstream dependent.
- P1 empirical: primitive qualification, 25-brief benchmark, Visual DNA corpus/retrieval and CAL2 real-production qualification remain incomplete.

## Architecture acceptance law

V2 becomes `V2_FINAL` only when:
- live truth projections converge;
- every P0/P1 has owner/test/evidence path;
- critical event/state/artifact boundaries have executable contracts;
- zero-context recovery reproduces important state/topology/blockers/next-safe-action;
- critical historical escaped bugs are permanent regression families;
- renderer/product E2E paths are physically executed;
- authoritative full-video creative qualification reaches product release thresholds;
- current main is verified after serial promotion;
- no residual uncertainty is hidden: it exists as UNKNOWN/RISK/BLOCKER/DEFERRED_DECISION with owner + trigger + resolution path.

Until then, this architecture is an implementation compiler—not release authority.
