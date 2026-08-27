# MOTION.OS Live Conflict / Dependency Matrix

Snapshot: 2026-08-26
Observed active PRs: #34, #35, #37.

## Physical changed-file overlap

Current exact filename intersection:
- #34 ∩ #35 = ∅
- #34 ∩ #37 = ∅
- #35 ∩ #37 = ∅

Conclusion: current collision risk is primarily semantic/contractual, not same-file textual collision. Do not introduce repository-wide locks.

## Workstream ownership

| PR | Primary ownership | Produces | Consumes | Cross-contract risk |
|---|---|---|---|---|
| #34 | Remotion runtime qualification | renderer capability/evidence | scene/runtime spec | scene-spec, renderer capability registry |
| #35 | Visual DNA + Studio Engine/downstream editing | editing graph, Studio runtime, render stack | MotionStyle2JSON, provider assets, Phase06 handoff | studio-entry, editing graph, renderer selection, beat mapping |
| #37 | Content Intelligence + Avatar Factory + render authority | sealed content/avatar handoff, stable beats, provenance/replay IDs | sources/provider state | avatar-handoff, stable-beat-identity, provenance-root, replay-fingerprint |

## Canonical semantic dependency direction

```text
PR #37 Content + Avatar
    │ produces sealed handoff
    ▼
contract:avatar-handoff
contract:stable-beat-identity
contract:provenance-root
contract:replay-fingerprint
    │
    ▼
PR #35 Studio Engine
    │ compiles downstream editing/render plan
    ├──────────────► renderer capability router
    │                         │
    │                         ▼
    └────────────────────► PR #34 Remotion runtime evidence
```

This is a semantic dependency, not necessarily a Git branch dependency.

## Contract leases

### PR #37 may claim
- `contract:avatar-handoff`
- `contract:stable-beat-identity`
- `contract:provenance-root`
- `contract:replay-fingerprint`

### PR #35 may claim
- `contract:studio-entry`
- `contract:editing-graph`
- `contract:motionstyle2json`

### PR #34 may claim
- `contract:remotion-runtime-capability`
- `contract:scene-spec-runtime-consumption`

## Shared semantic boundaries requiring coordination

### avatar-handoff → studio-entry
Any field removal/rename/type change in the upstream handoff requires:
1. impact declaration;
2. compatibility/migration decision;
3. downstream consumer test in #35 lineage;
4. stale ContextPack invalidation.

### stable beat identity
Beat IDs become downstream anchors after render authorization. #35 must map/edit around them without silent identity mutation. Any split/merge semantics require an explicit derived-ID policy.

### provenance root / replay fingerprint
#35 and #34 may extend evidence lineage but must not reinterpret or regenerate upstream identity with incompatible algorithms.

### renderer capability
#34 verifies technical Remotion authority. #35 may consume that capability only after evidence state reaches VERIFIED; presence of code is not capability authority.

## Merge/convergence strategy

1. Keep #34/#35/#37 independently reviewable while exact file overlap is zero.
2. Establish shared contract tests before any breaking interface convergence.
3. Promote contracts additively where possible.
4. Merge order should be evidence-driven, not PR-number-driven.
5. After any one merges to main, mark ContextPacks for the other active workstreams stale and require revision refresh/rebase review.
6. Before final v1.0 convergence, run an integration branch/vertical slice that consumes #37 handoff through #35 Studio Engine and uses #34-verified Remotion runtime.

## Current conflict score

- Textual collision: LOW
- Semantic contract collision: HIGH
- Stale-context risk: HIGH
- Duplicate-infrastructure risk: MEDIUM-HIGH
- Merge-order risk: MEDIUM
- Data/provenance incompatibility risk: HIGH

## Stop-the-line triggers

Immediately publish `CONFLICT` on Coordination Bus #43 if:
- any PR begins editing a file already modified by another active PR without explicit reconciliation;
- #35 defines a competing upstream content/avatar manifest;
- #37 defines a competing Studio editing graph/runtime entrypoint;
- #34 changes scene-spec semantics rather than only consuming/validating them;
- provenance/replay hashing algorithms diverge;
- stable beat IDs are mutated after authorization;
- SQLite is described/promoted as network multi-host authority;
- COS graph is used as transactional authority rather than rebuildable projection.
