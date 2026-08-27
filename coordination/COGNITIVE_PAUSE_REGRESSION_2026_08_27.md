# MOTION.OS — Cognitive Pause Historical Regression & Repository Review

Date: 2026-08-27
Baseline: `main@080dfd5c16bc06100edd716eadc770530dc47af2`
Mode: `/code` + `/repo-review` + historical regression
Authority: audit / planning only; no shared Phase07 contract mutation in this document.

## Executive conclusion

MOTION.OS has advanced much further than the historical Phase05 branch suggests. The current repository contains a verified graph-native Studio Engine foundation, a physically verified Remotion path, a Phase06 content/avatar authority plane, local-first MERGE_SAFE promotion, and a Phase07 coordination kernel with event-store, bus, leases/fencing, ContextPack, conflict detection, content lineage, COS projection and recovery semantics.

The next bottleneck is **truth convergence**, not another architecture rewrite.

The most dangerous current failure mode is not absence of infrastructure. It is the coexistence of several partially stale read models and two different event representations around an otherwise strong Phase07 kernel. The correct cognitive pause is therefore:

> Freeze new shared-contract invention, make the rich Phase07 CoordinationEvent/EventStore the canonical coordination history within its proven local/reference authority boundary, and regenerate all human/operator state as projections from explicit authorities.

The transport/bus itself is NOT the source of truth. The **durable event store/history** is the coordination source of truth; buses/websockets/GitHub comments are delivery or bootstrap surfaces.

---

# 1. Historical regression — where we came from

## H0 — Motion experiments / RC convergence
Initial system centered on generated motion fixtures and RC01→RC09-style creative iteration. Strength gained: visual QA, protected-region regression, artifact lineage, iterative repair. Weakness: state was conversation-heavy and multiple Markdown files became de facto authority.

## H1 — Phase01 Motion Grammar
Separated brand/style from motion grammar and introduced grammar fidelity, product semantics and negative constraints.

## H2 — Phase02 Professional Motion System
Formalized reference analysis → `motion_system` → semantic behavior → scenes → structured prompts → QA. `director.md` later raised this to a senior creative-direction contract.

## H3 — Phase03 Exact Reconstruction
Created separate optimizer for exact frame reconstruction: stable IDs, absolute coordinates, per-frame/dense/hybrid representation, SVG+JS and fidelity metrics. Correctly separated reconstruction fidelity from creative quality.

## H4 — Phase04 Physical Visual DNA
Moved measurable facts out of LLM opinion: FFprobe/FFmpeg/OpenCV/OCR/audio providers → FeaturePack → MotionStyle2JSON → compilers. This was the first major evidence-authority correction.

## H5 — Phase05 Studio Engine
Historical PR #35 became oversized and diverged. It was correctly superseded by clean PR #38, which promoted the graph-native Studio Engine foundation directly from current main. The system gained typed EditingGraph, Director compiler, editing/audio graphs, Skill runtime, GraphRAG, providers/assets, semantic primitives/blueprints, renderer contracts, QA/repair and Studio recovery surfaces.

## H6 — Runtime proof
PR #42 replaced historical Remotion proof #34 and physically verified the Remotion chain. It corrected container-duration authority, frame-count handling, hashing, ffprobe timeout, Node runtime and TS checks.

## H7 — Phase06 Content / Avatar + merge governance
Content Intelligence, Avatar Factory and single-host transactional render authority became canonical, while MERGE_SAFE became repository clean-runner promotion authority.

## H8 — Phase07 Coordination Kernel
PR #44 merged the current coordination foundation: rich CoordinationEvent/EventStore, idempotency/revisions/causality, consumer dedupe, leases/fencing, ContextPack, conflict classification, unified content lineage, COS shadow projection, policy/security, recovery and operator surfaces.

Current authority score is intentionally limited by unverified multi-host coordination and weak live Drive integration. This is correct epistemic discipline, not a defect.

---

# 2. Current authority map

| Aggregate / plane | Current authority | Important boundary |
|---|---|---|
| Source/code/schemas/plans | GitHub `main` | executable truth |
| Repository promotion | MERGE_SAFE clean-runner evidence | platform branch protection is still off |
| Phase06 render execution | SQLite/WAL single-host transactional store | do not migrate merely because Phase07 exists |
| Phase07 coordination | CoordinationEvent/EventStore semantics, currently local/reference qualified | NOT independent-host multi-host authority |
| Heavy media/recovery | Drive | artifact truth, not transactional bus |
| COS / unified graph | deterministic derived projection | must be rebuildable; never authorize writes |
| Markdown/YAML operator state | read model only | currently not consistently treated as projection |
| GitHub Issue #39 | bootstrap/shared coordination surface | transport/evidence bridge, not final event-store authority |

---

# 3. P0/P1 findings

## P0-01 — State/read-model split brain
`STATE.md`, `state/project_state.json`, `coordination/README_FIRST.md`, `coordination/AUTHORITY_PLANE_MATRIX.md` and `coordination/ACTIVE_AGENTS.yaml` disagree about current master/runtime/topology/bus references.

Examples:
- `STATE.md`: RC09E selected and Remotion still listed as unverified.
- `project_state.json`: RC06/RC07 still canonical, but Remotion correctly marked verified.
- `README_FIRST.md` / Authority Plane Matrix: bootstrap Bus #43, although #43 is closed duplicate and #39 is active.
- `ACTIVE_AGENTS.yaml`: Phase07 owner still shown in FINAL_QUALIFICATION after PR #44 has merged.

Impact: a zero-chat agent can obtain contradictory truth depending on which required bootstrap document it reads first.

Required fix: state projection compiler + source watermark + drift CI. Human-facing state must be generated or verified from canonical authority sources.

## P0-02 — Dual event model / authority ambiguity
There are two event representations:
1. `scripts/agent_event.py` + `schemas/agent_event.schema.json`: simple immutable lifecycle files;
2. `src/coordination/events.py` + EventStore: rich aggregate revisions, idempotency, causal links, scopes and provenance.

Both are useful, but they must not be peer authorities.

Decision required: rich CoordinationEvent/EventStore is canonical coordination state-transition history. File-per-event lifecycle JSON becomes an audit/export projection adapter from canonical coordination events or an explicitly separate repository-lifecycle evidence plane.

## P0-03 — Scheduler filtered-dependency deadlock
`build_execution_plan()` can filter steps by `executable_kinds` while preserving dependencies on nodes omitted from the plan. `scheduler_from_plan()` then creates no job for the omitted dependency, so the dependent job can never become ready.

Existing test uses three `Skill` nodes and does not cover a Skill depending on a non-executable Asset/Provider/semantic node.

Required fix: collapse non-executable dependency closure into cache/input dependencies while only scheduling executable ancestors, or include dependency sentinel/completed inputs. Add regression test.

## P0-04 — Multi-render assembly global-time semantics incomplete
`src/renderers/assembly.py` sorts artifacts by time/renderer/id, not canonical z-order. Overlay inputs are enabled at global time but are not PTS-shifted to their `start_ms`. Region-only artifacts may therefore not exist at the intended global interval. `has_alpha`, color-space normalization, base interval, audio mapping and provenance enforcement are not implemented in `ffmpeg_filter_complex()`.

Required fix: explicit CompositionLayer order + per-input `setpts=PTS-STARTPTS+start/TB`, alpha/color conversion, trim policy, audio graph mux and real region-artifact tests.

## P0-05 — Platform enforcement gap
`main` is not protected at GitHub level. MERGE_SAFE is strong repository policy/evidence, but a direct push can bypass it if credentials permit.

Required fix: branch ruleset / protection requiring MERGE_SAFE and coordination-contract checks when settings-write path is available. Until then document this as an operational P0 and fail operator review if direct-push lineage appears.

## P1-01 — Skill executor exceptions disappear from trace
`SkillRuntime.run()` calls executor without exception capture. A thrown exception exits before `SkillExecutionRecord`, ToolCall evidence or BLOCKED/FAILED record exists.

Required fix: structured FAILED record, error class/message hash, retryability, invocation idempotency and event emission before optional re-raise.

## P1-02 — QA history IDs are not run-scoped
`attach_findings()` generates IDs like `qa:001:<code>` and `defect:001:<code>` independent of `run_id`. Re-running QA on the same graph can collide instead of preserving immutable evaluation history.

Required fix: IDs include run/correlation identity and target fingerprint; repeated identical finding may dedupe through an explicit fingerprint rather than node collision.

## P1-03 — RepairCandidate relation points at defect, not mutated target
`attach_repair_candidates()` creates `RepairCandidate --MUTATES--> Defect`, while mutation payload targets the actual graph node. This weakens impact traversal and semantic graph queries.

Required fix: candidate `ADDRESSES`/`GENERATED_FOR` Defect and `MUTATES` actual target nodes. Add ontology relation if necessary through contract-change protocol.

## P1-04 — Event snapshot does not bind exact event stream contents
`StateSnapshot.state_hash` covers watermark + aggregate heads, but not an event-chain/Merkle root. Individual events are hashed, yet the snapshot cannot alone prove which exact event content produced those heads.

Required fix: append-chain root or deterministic stream root in snapshots; replay verifies chain/root and heads.

## P1-05 — Coordination timestamps / causal references under-validated
`CoordinationEvent` accepts custom `occurred_at` / `recorded_at` strings without date-time parsing. In-memory store does not enforce parent/causation existence or causation consistency.

Required fix: RFC3339 validation; configurable causal-reference policy (`STRICT_EXISTING`, `EXTERNAL_ALLOWED`) and tests for missing/cyclic/impossible causality.

## P1-06 — Relation ontology remains intentionally broad
Several relation rules are ANY_TO_ANY. This helped migration but reduces the type system's ability to reject semantic graph corruption.

Required fix: learn from real main graph, tighten high-risk relations incrementally, migration tests first. Do not mass-tighten in one PR.

## P1-07 — Event Bus authority wording is easy to misuse
The user-facing phrase “Event Bus is canonical” can accidentally promote transport to authority. `CoordinationBus` correctly says durable persistence must precede acknowledgement in production, but current concrete bus is in-memory reference only.

Canonical wording: **Coordination Event Store/history is canonical for coordination aggregates within its qualified authority boundary. Bus/realtime/Issue #39 deliver or expose events.**

## P1-08 — Drive provider assurance remains low
Coordination scorecard D17 remains materially below 9 because live provider evidence was unavailable. Do not use Drive as synchronization proof until provider bridge is verified.

## P1-09 — Product state lags coordination maturity
Remotion is now physically verified; HyperFrames and temporal critic remain true product P0s. RC09E/RC06 state is inconsistent. Coordination success must not distract from creative release gates.

---

# 4. Test review

## Strong existing evidence
- Python 3.11/3.12 coordination contracts repeatedly green on Phase07 candidate.
- MERGE_SAFE passed before Phase07 merge.
- physical analysis and physical Remotion passed.
- dependency security passed.
- immutable lifecycle-event validation passed.
- local 3-agent crash/takeover campaign, 500 takeover rounds and 100-agent competitor campaign reported qualified.
- event idempotency, consumer offsets, leases/fencing, CAS, recovery, ContextPack and unified graph have dedicated tests.

## Missing test classes discovered
1. scheduler: executable node depending on filtered non-executable node;
2. assembly: subclip starting after t=0 with global PTS alignment;
3. assembly: z-order independent of renderer lexical ordering;
4. assembly: alpha input + audio master + color normalization;
5. skill runtime: executor exception records FAILED event/trace before raise;
6. graph QA: multiple QA runs preserve distinct immutable history;
7. repair graph: candidate edges target actual mutated nodes;
8. state projections: rebuild from canonical authority → exact committed read models;
9. state drift negative test: manual STATE/project_state mutation fails MERGE_SAFE;
10. event snapshot tamper test: altered historical event invalidates stream root;
11. event timestamp and causal-reference negative tests;
12. bootstrap topology test: active Issue/PR references resolve and superseded refs cannot be marked active;
13. branch-protection/ruleset policy check if API exposure permits;
14. eventually independent-process multi-host campaign before D06 authority promotion.

---

# 5. Cognitive Pause protocol

The pause is a coordination barrier, not “agents stop thinking”.

1. `PAUSE_REQUESTED` / CLAIM announces affected shared contract scopes and expected main/event watermark.
2. Active agents finish only to a recoverable boundary.
3. Each publishes CHECKPOINT/`PAUSE_ACK` with branch, SHA, scopes, test evidence and unresolved mutations.
4. No shared contract mutation proceeds until all conflicting active writers are acknowledged/released or explicitly fenced stale.
5. Canonical event history + GitHub lifecycle + authoritative aggregate states are reconciled.
6. All projections are rebuilt and compared.
7. Conflicts become decisions/events, never silent manual edits.
8. `PAUSE_RELEASED` records canonical watermark/hash, new ContextPack revision and permitted workstreams.

Until a durable multi-host backend is qualified, Issue #39 + immutable repository events + reference coordination kernel provide assisted coordination; they do not magically create distributed transactional authority.

---

# 6. Weight realignment

Priority weighting for next implementation campaign:

- **1.00 P0 Truth Integrity:** event-model unification, projection drift, scheduler deadlock, compositor global-time correctness, current product-state reconciliation.
- **0.95 P0 Promotion Integrity:** platform enforcement / MERGE_SAFE, recovery reproducibility.
- **0.85 P1 Observability:** skill exceptions, QA immutable history, repair semantics, event stream root.
- **0.80 P1 Causal Integrity:** timestamp/parent validation, ontology tightening, ContextPack invalidation.
- **0.75 P1 Artifact bridge:** Drive evidence provider reliability.
- **0.65 Product runtime:** HyperFrames physical runtime and multi-renderer production proof.
- **0.60 Creative authority:** temporal multimodal critic + Apple-level creative benchmark; becomes highest product weight once truth integrity P0s close.
- **0.30 Optional scale:** Postgres/Supabase multi-host authority, only after actual simultaneous-host requirement.

The point is to stop rewarding architecture/file count and reward authority + executed evidence + end-to-end product quality.

---

# 7. Immediate recommendation

Do NOT create another event bus. Do NOT migrate Phase06 render state to Postgres. Do NOT rewrite Phase05.

Execute Phase08 reconciliation in small ordered PRs:
1. freeze/reconcile projections;
2. unify event representations;
3. fix scheduler/compositor/runtime-trace bugs;
4. harden event/replay integrity;
5. run cognitive-pause/multi-agent adversarial proof;
6. enforce main promotion;
7. return focus to HyperFrames + temporal critic + Apple-level benchmark.
