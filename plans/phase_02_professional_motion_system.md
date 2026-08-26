# Phase 02 Plan — Professional Motion System

## Goal
Turn references + brief into a locked production system before rendering. Replace prompt improvisation with studio-like structure.

## Pipeline
```text
reference corpus
→ physical analysis / Visual DNA
→ evidence retrieval
→ structural reverse engineering
→ pattern extraction
→ motion_system lock
→ semantic behavior mapping
→ scene contracts
→ structured contract
→ renderer compilation
→ QA
→ repair / rerender
```

## Required `motion_system`
### Tokens
spacing, radii, typography roles, palette, grid, materials, FX limits, camera grammar and easing.

### Rules
no drift, strict text integrity, stable anchors, geometric continuity, one dominant idea per beat, motivated transitions, persistent IDs.

### Reusable patterns
Typing, split, expand, collapse, seed→card, collect→condense→brand, reward unlock, audio pulse, UI module build, object→behavior→system.

## Semantic translation layer — IMPLEMENTED V1
`src/core/semantic_behavior.py` translates controlled concepts to behaviors before primitive selection.

## Motion-system compiler — IMPLEMENTED V1.1
`src/core/motion_system.py` emits locked tokens, rules, semantic behaviors, allowed/forbidden primitive routes, camera/material grammar and QA criteria. It now preserves reference-conditioning source IDs and anti-copy provenance rather than erasing how style evidence entered the build.

## Reference-conditioning layer — IMPLEMENTED V1
`src/core/reference_conditioning.py` converts retrieved, evidence-covered StyleSignatures into soft style candidates. Explicit project/brand tokens are never silently overwritten. `forbidden_copy=true` propagates into motion-system and scene contracts.

## Scene contract compiler — IMPLEMENTED V1.1
Each scene emits objective, primary event, continuity, persistent/new layers, semantic target, grammar constraints, audio cues, QA, and reference-provenance constraints.

## Renderer capability policy
Model-specific duration/resolution/text constraints remain time-stamped capability metadata, never permanent design law.

## QA
Drift, text integrity, geometry continuity, rhythm, hierarchy, transition motivation, grammar fidelity, brand consistency and reference provenance.

## Definition of Done
A new agent can take a plain-text brief + references, compile a deterministic `motion_system`, produce scene contracts, route primitives/renderers and explain every motion decision through semantics/rules/evidence rather than “looks cool”. Reference-driven output must be system-transfer, not source copying.

## Current status
- semantic behavior map: IMPLEMENTED + UNIT TESTED
- locked motion_system contract: IMPLEMENTED + UNIT TESTED
- scene contracts: IMPLEMENTED + UNIT TESTED
- reference provenance / anti-copy conditioning: IMPLEMENTED + UNIT TESTED
- MotionStyle2JSON → Remotion compiler: IMPLEMENTED + UNIT TESTED
- Framer Motion compiler contracts: IMPLEMENTED + UNIT TESTED
- measured reference corpus runner: IMPLEMENTED; real corpus execution OPEN
- automatic grammar selection calibration: OPEN
- production render proof under HyperFrames/Remotion: OPEN HARD GATE

## Learning delta from Phase 04
Reference reverse engineering is data-backed: `motion_system` can compile from evidence-bound `MotionStyle2JSON` and retrieved StyleSignatures, not only freeform summaries.

## Learning delta from Gauntlet 10X
The professional system became executable in code; renderer/runtime verification became the dominant bottleneck.

## Learning delta from Real Analysis Superwave
The reference stage is no longer a prose-only precursor. It can now be a measurable production dependency:

`reference MP4 → physical evidence → StyleSignature → retrieval → soft conditioning → locked motion_system → scene contracts`.

New hard rule: no retrieved source may silently become canonical tokens. Every conditioned source is traceable and anti-copy constrained. The next production experiment must compare outputs built with and without retrieved conditioning, using the same brief and grammar, to measure whether reference intelligence improves brand/style fit without reducing originality.
