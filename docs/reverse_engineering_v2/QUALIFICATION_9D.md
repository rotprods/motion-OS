# T08 — Golden Scene 9D Qualification

Authority: `IMPLEMENTED_UNVERIFIED` until exact-head clean-runner evidence is attached.

## Purpose

T07 proved bounded source-visible behavior for four golden scenes. T08 prevents those successes from being over-promoted into claims that the original After Effects project, exact typography, 3D assets, effects, camera causality, source stems or full retention system have been reconstructed.

The canonical nine dimensions are:

1. temporal;
2. motion;
3. camera;
4. typography;
5. depth;
6. color;
7. FX;
8. audio;
9. retention.

Every dimension is an independent veto surface. There is no weighted average that can produce `FULL_9D_FIDELITY_VALIDATED` while any required claim is PARTIAL, BLOCKED or NOT_MEASURED.

## Authority law

`PHYSICALLY_MEASURED > DETERMINISTIC_HEURISTIC > EVIDENCE_BOUND_INFERENCE > EXPLICIT_ASSUMPTION > UNKNOWN`

A claim with status `QUALIFIED` requires durable evidence and `PHYSICALLY_MEASURED` claim authority. Older-scene evidence may only cross an exact-head boundary through an explicit physically measured `output_equivalence_proof`.

## Semantic-strength law

A renderer proxy cannot silently redefine a fidelity dimension. Each dimension has a minimum strong claim kind. Examples:

- typography requires `glyph_morphology`; a layout box is insufficient;
- audio requires `stem_identity`; onset timing is insufficient;
- FX requires an `effect_stack` claim;
- retention requires a `retention_grammar` claim;
- motion requires kinematic/easing claims, not only start/end boxes.

The current S11 and S14 exact-head artifacts were independently compared to the artifacts that were originally source-qualified. S11 is `141/141` internal files byte-identical; S14 is `105/105`. This bridges revision provenance without upgrading semantic scope.

## Current measured frontier

Temporal layout/timing is qualified across S04, S11, S14 and S16. Several screen-space motion, camera-static, depth partial-order, audio-timing and retention-hold subclaims are also physically measured.

The program is intentionally **not** full 9D. Material blockers include:

- original velocity/easing and Graph Editor curves;
- causal camera/reframe separation where the flattened source is ambiguous;
- exact font/glyph morphology;
- complete depth topology / unique hidden z-order;
- exact pre-grade color/material/lighting;
- original effect stacks;
- isolated original audio stems/timbre;
- cross-scene stimulus-density/pattern-interrupt/payoff-spacing retention grammar.

## Repair law

A failing dimension becomes a DefectGraph node. Repair order is:

`source/evidence -> measurement -> canonical claim/graph -> regression -> renderer adapters -> rerender -> remeasure`.

Renderer-local magic numbers are prohibited unless they are first represented in the shared canonical evidence/claim model with bounded authority.

## Promotion states

- `CROSS_SCENE_PARTIAL_QUALIFICATION`: at least one required claim is not qualified.
- `FULL_9D_FIDELITY_VALIDATED`: every required claim in all nine dimensions is independently qualified.
- `CANONICAL_TEMPLATE`: separate later gate; full 9D on one reference does not prove generalization.

Issue #48 remains an independent promotion barrier.
