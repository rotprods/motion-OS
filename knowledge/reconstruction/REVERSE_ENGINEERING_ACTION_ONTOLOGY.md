# MOTION.OS — Reverse Engineering Atomic Action Ontology

## Purpose

This ontology is an evidence/intermediate contract for decomposing flattened reference video into atomic, renderer-independent editing operations. It is projected into the existing MOTION.OS EditingGraph; it is **not** a competing graph authority.

## Atomic action

An action is the smallest visually meaningful, temporally bounded operation that an editor/renderer must reproduce to preserve the reference's editing identity.

Examples:
- a hero word scaling 84% → 112% → 100%;
- a phone precomp scaling/reframing over 24 frames;
- a 4-frame RGB/white glitch bridge;
- a foreground card entering above the subject;
- a carousel parent snapping horizontally to the next state;
- a UI row staggering into a list;
- a low-entropy red hold that intentionally removes stimuli.

## Mandatory fields

`action_id`, `scene_id`, `start_frame`, `impact_frame`, `end_frame`, `domain`, `verb`, `target`, `function`, `parameters`, `authority`, `confidence`, `evidence_refs`, `renderer_mapping`.

## Domains

`transition`, `caption`, `typography`, `motion`, `camera`, `object`, `depth`, `background`, `fx`, `audio`, `source_lock`.

## Authority

`measured`, `measured_heuristic`, `measured_visible`, `evidence_bound_inference`, `inferred_from_mixed_audio`, `assumption`, `unknown`.

## Function taxonomy

Functions describe **why** the action exists, not how it looks:

- hook
- disclose_information
- semantic_emphasis
- direct_attention
- pattern_interrupt
- connect_states
- preserve_continuity
- prove_system_behavior
- establish_depth
- create_breathing_window
- synchronize_audio
- reward
- payoff
- source_fidelity

## Source locks

An action with `verb=source_lock` preserves source-specific content in `RECONSTRUCT_EXACT` only. Structural/style templates must strip or slot it.

Examples: Instagram/Reels chrome, literal source screenshots, speaker footage, exact source copy, licensed source artwork.

## Renderer mapping rule

Every observable action must provide all three implementations:

- After Effects semantic implementation;
- Remotion frame-driven implementation;
- HyperFrames/GSAP deterministic implementation.

Mappings describe implementation mechanisms; they must not change edit timing or hierarchy.

## Graph projection

`Scene → CONTAINS → OperationProjection`

`OperationProjection → COMPILES_TO → AfterEffects/Remotion/HyperFrames`

Atomic operations are an evidence-friendly projection. Canonical graph semantics remain MOTION.OS `TypedEditingGraph`.
