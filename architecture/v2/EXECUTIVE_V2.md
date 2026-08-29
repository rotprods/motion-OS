# MOTION.OS V2 — Executive Architecture Synthesis

Authority: PROPOSED_V2_CANDIDATE / NOT CURRENT MAIN AUTHORITY
Owner: workstream `motion://workstream/graph-refactor-v2`
Source revision: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`
Session: `motion://session/chatgpt/graph-refactor-v2/20260829T2344+0200`
Supersedes: no current canonical document until promotion; this package is a migration candidate.

## North Star

`Brief -> evidence-bound professional motion master`

A result is successful only when it is visibly strong, reproducible, temporally coherent, provenance-complete, safe to promote, and recoverable by a zero-context successor.

## V2 architecture in one sentence

MOTION.OS V2 is a **single-authority event/state core with deterministic graph projections**, surrounded by domain engines for content, creative direction, render, temporal QA, repair and empirical learning; every promotion is evidence-bound, every agent/session is first-class, and every derived graph/cache/document can be rebuilt or invalidated without becoming hidden write authority.

## Architecture principles

1. **Authority before convenience.** GitHub live lifecycle and versioned domain state are promotion truth; event history is immutable evidence; graph/COS/README/Todoist are projections.
2. **One semantic Event Fabric, many adapters.** GitHub Bus #39, immutable repo events and runtime EventStore are transports/storage surfaces, not independent truths.
3. **Session-native coordination.** `project_id -> agent_id -> session_id -> workstream_id -> objective_id -> correlation_id` is present on material work.
4. **Evidence-bound authority.** A claim, benchmark, render, critic result or release cannot self-promote from aggregate counters or caller assertions.
5. **Projection, never reverse authority.** COS Graph Engine, search indexes, dashboards and ContextPacks are rebuildable read/reasoning planes.
6. **Product quality outranks architecture volume.** Architecture changes must remove measured risk/bottlenecks or improve motion quality/fidelity.
7. **Local-first assurance, clean-runner promotion.** Local tests are the development loop; `MERGE_SAFE`/combined-head clean-runner evidence is promotion authority.
8. **No implicit distributed authority.** SQLite/single-host semantics remain valid until measured multi-host contention justifies a network store.
9. **Fail closed at irreversible boundaries.** Merge, spend, publish, deploy, delete and release require current main + current event watermark + valid evidence.
10. **History is append-only; current truth is projected.** Supersede stale state instead of deleting historical facts.

## System boundaries

### A. Authority Kernel
Owns identity, canonical event semantics, state transitions, revisions, leases/fencing, idempotency, evidence references, promotion preflight and recovery seals.

### B. Content Intelligence
Owns SourcePack -> claims -> ICP -> driver -> angle -> hook -> beats -> script -> TTS -> avatar intent. It never manufactures verification evidence; performance learning remains correlation unless controlled evidence exists.

### C. Studio / Creative Runtime
Consumes sealed content handoffs and creative direction. Owns SceneSpec/EditingGraph composition, primitives, render selection, assets and repair candidates. `director.md` remains creative-direction authority; schemas/code are execution authority.

### D. Renderer Fabric
Adapters for Remotion, HyperFrames, Lottie and future engines. Renderer evidence binds exact spec/source/runtime version/run/artifact hashes. Cross-render color, alpha, audio and timing contracts are explicit.

### E. Temporal Quality & Repair
Owns decoded frame-clock authority, full-video temporal evidence, multimodal critic contract, creative tournament, defect graph and evidence-bound repair proposals. Derived repair graphs cannot directly authorize mutation or release.

### F. Empirical Qualification
Owns benchmark suites, primitive qualification, APSR/GSR, CAL2 and performance learning. Aggregate historical numbers have `authority_effect=NONE` unless mapped to exact IDs/artifacts/runs.

### G. Coordination / Agent Runtime
Owns ContextPack creation, semantic scope conflict detection, session graph, claims, checkpoints, handoffs and zero-context continuation. Autonomous selection is bounded by the same Event Fabric and authority rules.

### H. Evidence / Artifact Plane
GitHub: code, contracts, PR/test lifecycle.
Drive/object storage: large immutable artifacts when available.
Repo evidence manifests: hashes/IDs/revisions linking artifacts to authority.
Local sandbox: disposable compute only.

## Authority hierarchy

1. **Live irreversible-system truth:** GitHub live branch/PR/check lifecycle + externally verified admin controls.
2. **Canonical domain state:** versioned machine state/contracts committed in the repository or qualified runtime authority store.
3. **Immutable event/evidence history:** canonical semantic events and evidence records.
4. **Artifacts:** exact hash-bound media/test outputs.
5. **Derived projections:** ContextPack, COS, unified graph, operator dashboard, docs summaries, Todoist.
6. **Conversation memory:** convenience only; never promotion authority.

When layers disagree, lower layers lose authority and must be rebuilt/reconciled.

## Current-to-V2 diagnosis

### Keep
- Local-first MERGE_SAFE architecture.
- Phase06 content/avatar lineage and sealed Studio handoff.
- Phase07 session/event/lease/COS projection model.
- Remotion physical runtime proof.
- Single-master-audio direction.
- Evidence-first primitive/benchmark qualification direction.

### Refine
- Event Fabric convergence and ContextPack freshness.
- Renderer provenance binding across source/runtime/artifact.
- Full-video critic causality and decoded frame authority.
- Security gate to include boundary-specific trust tests in addition to static/dependency scans.
- Current-state documentation projection.

### Refactor
- Hand-maintained duplicated current-state surfaces.
- Ambiguous `verified/complete/ready` vocabulary.
- QA graph histories that can collide or lie about mutation targets.
- Release/benchmark aggregate counters without ID-bound evidence.

### Migrate
- Current fragmented architecture docs -> this V2 package after review/promotion.
- Bootstrap Bus #39 body -> historical bootstrap; current state comes from projector/watermark.
- ACTIVE_AGENTS bootstrap snapshot -> derived live read model.

### Delete / deprecate after migration
- Duplicate active-state claims that are not generated/validated.
- Superseded ADR namespace collisions.
- Duplicate solution PRs after stronger invariants are absorbed.

### Defer
- Postgres/Supabase event kernel until multi-host contention is measured.
- Redis/Kafka/Kubernetes/vector DB/CDN unless a measured operational trigger exists.

## Hard blockers to V2 production authority

P0/P1 override any weighted score:
- stale or contradictory current-state authority;
- no administrative protection on `main`;
- temporal critic evidence not bound to decoded frame-clock + provider/run/artifact identity;
- renderer proof not bound to exact source/spec/runtime/artifact provenance;
- release artifact/media unavailable or mismatched;
- unresolved destructive cross-agent semantic collision;
- any P0 security issue or false authority claim;
- inability to cold-recover state/graph/next-safe-action without chat.

## V2 acceptance condition

V2 is `PRODUCTION_AUTHORITY` only when:

- all canonical state surfaces reconcile to live GitHub;
- one Event Fabric semantic contract is used by all coordination surfaces;
- zero-context recovery + agent-death drill passes;
- every historical escaped bug has a permanent regression/property/adversarial test;
- renderer, audio, alpha, color and temporal evidence are exact-ID/hash bound;
- full-video temporal critic + creative tournament execute on a recoverable real artifact;
- unseen vertical-slice semantic/creative mean >=9 under evidence-bound scoring;
- primitive and benchmark qualification is ID-bound, not aggregate-only;
- CAL2/performance learning separates observation from causality;
- security/recovery/merge governance gates pass;
- no unresolved P0/P1;
- `main` is verified after the final migration merge.

Until then, V2 states must remain precise: PROPOSED, IMPLEMENTED, EXECUTED, VERIFIED, EMPIRICALLY_QUALIFIED, BLOCKED, DEGRADED_EXTERNAL or SUPERSEDED.