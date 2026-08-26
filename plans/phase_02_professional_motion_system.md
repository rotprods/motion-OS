# Phase 02 Plan — Professional Motion System

## Goal
Turn references + brief into a locked production system before rendering. Replace prompt improvisation with studio-like structure.

## Pipeline
```text
reference corpus
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

## Motion-system compiler — IMPLEMENTED V1
`src/core/motion_system.py` emits locked tokens, rules, semantic behaviors, allowed/forbidden primitive routes, camera/material grammar and QA criteria.

## Scene contract compiler — IMPLEMENTED V1
Each scene emits objective, primary event, incoming/outgoing continuity, persistent/new layers, semantic target, grammar constraints, audio cues and QA.

## Renderer capability policy
Model-specific duration/resolution/text constraints remain time-stamped capability metadata, never permanent design law.

## QA
Drift, text integrity, geometry continuity, rhythm, hierarchy, transition motivation, grammar fidelity and brand consistency.

## Definition of Done
A new agent can take a plain-text brief + references, compile a deterministic `motion_system`, produce scene contracts, route primitives/renderers and explain every motion decision through semantics/rules rather than “looks cool”.

## Status after Gauntlet 10X
- semantic behavior map: IMPLEMENTED + UNIT TESTED
- locked motion_system contract: IMPLEMENTED + UNIT TESTED
- scene contracts: IMPLEMENTED + UNIT TESTED
- MotionStyle2JSON → Remotion compiler: IMPLEMENTED + UNIT TESTED
- Framer Motion compiler contracts: IMPLEMENTED + UNIT TESTED
- reference-derived automatic grammar selection: OPEN
- production render proof under HyperFrames/Remotion: OPEN HARD GATE

## Learning delta from Phase 04
Reference reverse engineering is now data-backed: `motion_system` can compile from evidence-bound `MotionStyle2JSON`, not only freeform summaries.

## Learning delta from Gauntlet 10X
The professional system is now executable in code. The next bottleneck is not schema design; it is renderer/runtime verification and measuring whether compiled semantics improve real motion quality.
