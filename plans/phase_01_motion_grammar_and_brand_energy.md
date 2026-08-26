# Phase 01 Plan — Motion Grammar + Brand Energy

## Goal
Separate visual style, product semantics, motion grammar and brand overlay so MOTION.OS does not apply one generic animation language to every brief.

## Canonical model
```text
brief
→ product_semantics
→ brand_energy
→ motion_grammar
→ visual_style
→ brand_overlay
→ beat_architecture
→ primitive_route
→ audio/camera/material grammar
→ render
→ grammar QA
```

## Current families
- APPLE_PREMIUM_DESKTOP
- HYPER_COMMERCIAL_GAMIFIED
- HYPER_COMMERCIAL_AUDIO
- DUOLINGO_FLUID_GAME_UI overlay
- SPOTIFY_FLUID_AUDIO_UI overlay

## Checkpoints
### P1.1 Grammar registry — IMPLEMENTED
Machine-readable grammar IDs, permitted/forbidden primitive concepts, pacing, camera/material constraints live in config.

### P1.2 Semantic primitive routing — IMPLEMENTED V1
`src/core/semantic_behavior.py` compiles controlled semantic concepts into visual behaviors before primitive selection. Initial contracts include autonomy, copilot, productivity, bottleneck, coordination, growth, focus, save, streak, discover and sync.

### P1.3 Brand-energy pacing — CONTRACT IMPLEMENTED / EMPIRICAL CALIBRATION OPEN
Grammar configuration carries pacing envelopes; benchmark calibration against heterogeneous references remains open.

### P1.4 Grammar critic — IMPLEMENTED V1
`src/qa/grammar_critic.py` scores hierarchy_under_motion, beat_focus, motion_intent, transition_motivation, product_ui_authenticity, material_consistency, AV sync, final hold and text integrity. Text integrity and beat focus are hard gates.

### P1.5 Evidence-conditioned grammar selection — IMPLEMENTED BRIDGE / CALIBRATION OPEN
`src/core/reference_conditioning.py` converts retrieved StyleSignatures into provenance-bearing **soft** constraints. Low-similarity/low-evidence neighbors are ignored. Retrieved sources are forbidden from directly copying source copy, logos, exact scene composition or protected assets.

The grammar router may use measured reference tendencies as evidence, but explicit brief/brand rules remain higher authority.

## Definition of Done
- same brief rendered under >=3 grammars yields structurally distinct motion, not recolors
- grammar critic rejects visually attractive but semantically wrong candidates
- primitive router cannot violate hard grammar constraints without explicit override
- text integrity preserved across all grammars
- reference-conditioned grammar selection improves style fit on labeled benchmark without copying source-specific content

## Current status
- Semantic-before-effects architecture: VERIFIED BY UNIT CONTRACTS.
- Primitive route enforcement: VERIFIED BY UNIT CONTRACTS.
- Grammar QA schema: IMPLEMENTED.
- Evidence-conditioning bridge: IMPLEMENTED + PROVENANCE-LOCKED.
- Cross-grammar production render benchmark: NOT YET AUTHORITATIVE.

## Learning delta from Phase 04
Measured Visual DNA can now flow into grammar selection through retrieved, evidence-covered StyleSignatures rather than description-only labels.

## Learning delta from Gauntlet 10X
A grammar must be executable, not prose. Controlled semantics produce candidate primitives and the critic can reject forbidden/non-allowed motion.

## Learning delta from Real Analysis Superwave
Reference intelligence now has a physical evidence root. New invariant: `retrieval similarity` is not grammar truth. It may propose soft constraints only when evidence coverage and similarity clear explicit thresholds, and every resulting `motion_system` retains source IDs + `forbidden_copy` provenance. Next proof is an A/B render benchmark: unconditioned vs evidence-conditioned grammar selection across heterogeneous references.
