# T08 — Cross-Golden 9D Qualification

Authority: `DERIVED_QUALIFICATION_PROJECTION`

This document does not supersede the four golden-scene DefectGraphs. It projects their live, durable evidence into one cross-scene qualification view.

## Live inputs

| Scene | PR | Live head | Remotion exact-head | Merge Safe | Artifact |
|---|---:|---|---:|---:|---:|
| S04_CIENTIFICAMENTE | #96 | `8ec35a259399d7b196b40627d782315a019e65e2` | `33512543155` PASS | `33512543087` PASS | `9802271767` |
| S11_UI_LIST | #107 | `988e91893cb498f720b9c2656b3d6d85f2d56300` | `33513406293` PASS | `33513406383` PASS | `9802633943` |
| S14_AUDIO_VISUAL_TEXTO | #124 | `12592bd8f8149767fafcb0ad0aa6036250ce540c` | `33456714673` PASS | `33456714946` PASS | `9781727915` |
| S16_FACTOR_X | #125 | `8e6fcb79d0d7958c0f023f128297059c97a7e674` | `33509838092` PASS | `33509838099` PASS | `9801246395` |

Issue #48 remains OPEN. No branch-local result may grant global promotion while that barrier remains active.

## Why two 9D authority modes exist

`RECONSTRUCT_EXACT` and `STRUCTURAL_TEMPLATE` answer different questions.

`RECONSTRUCT_EXACT` asks whether the visible source can be reproduced as closely as evidence permits. Missing original font files, source assets, isolated stems, hidden mattes and original AE internals can remain genuine blockers.

`STRUCTURAL_TEMPLATE` asks whether the editing behavior can be reused with different content. A source-specific font or 3D asset may become a `VARIABLE_SLOT`/`SOURCE_LOCK`, but timing, motion, depth, attention choreography and audio-event relationships cannot be guessed merely because literal content is replaceable.

A property may therefore be `PARTIAL` for exact reconstruction and `QUALIFIED` for structural-template behavior. This is not a relaxation: the two modes have different contracts.

## Current cross-golden conclusion

T07 primarily established strong source-bound **temporal and layout authority**. It did not establish full 9D authority.

### RECONSTRUCT_EXACT

- temporal: qualified across all four golden scenes;
- motion: partial across all four;
- camera: blocked or partial;
- typography: partial because exact fonts/glyph morphology remain unknown;
- depth: blocked or partial;
- color: blocked or partial;
- FX: blocked across all four;
- audio: partial and scene coverage incomplete;
- retention: partial.

### STRUCTURAL_TEMPLATE

- temporal: qualified across all four;
- motion: incomplete cross-golden;
- camera: blocked/partial;
- typography: several scene roles are qualified but S11 remains partial;
- depth: incomplete;
- color: only role-level partial authority;
- FX: blocked;
- audio: S14/S16 timing relationships qualify, S04 partial, S11 blocked;
- retention: pattern structure exists but formal stimulus metrics are not yet qualified.

Therefore:

```text
FULL_9D_FIDELITY_VALIDATED = false
STRUCTURAL_TEMPLATE_9D_VALIDATED = false
CROSS_RENDERER_PARITY_VALIDATED = false
EMPIRICALLY_GENERALIZED = false
CANONICAL_TEMPLATE = false
```

## Critical gauntlet learning

The four scenes exposed failure families that are now system-level invariants, not scene anecdotes:

1. conversational execution claims cannot grant authority;
2. mean fidelity gates cannot hide worst-frame residuals;
3. semantic measurement targets must be isolated;
4. stable summaries cannot replace continuous trajectories without equivalence proof;
5. sparse hand-authored projections cannot replace full-frame evidence without automated error proof;
6. the oracle must compare the same authority type (layout vs layout, glyph vs glyph);
7. renderer interpolation domains must satisfy runtime constraints independently of physical direction;
8. source audio events and renderer latency compensation are separate nodes;
9. entity identities must survive crossings through temporal continuity and versioned corrections;
10. tests protect semantic contracts, not documentation wording;
11. immutable action pins require provider provenance and cannot be reconstructed by visual guess;
12. test-harness failures must not be mislabeled product failures.

See `qualification/golden_9d/escaped_failure_families.json` for machine-readable invariants.

## Fail-closed promotion law

T08 explicitly rejects an averaged quality score as promotion authority.

A high temporal or layout score cannot compensate for an unqualified camera, depth or FX dimension. Every required dimension must independently satisfy its contract. Global barriers, cross-renderer parity and generalization are separate gates.

`qualification/golden_9d/compile_readiness.py` enforces this model.

## Next executable frontier

The next safe wave is `T08-W1 — Motion kinematics and easing authority`.

For each measured entity across S04/S11/S14/S16, derive from source-bound tracks:

- position/scale trajectory;
- velocity;
- acceleration;
- direction changes;
- onset/impact/settle;
- overshoot;
- hold windows;
- easing-family proxy with explicit confidence;
- source-native vs editorial classification where evidence permits.

Do not infer the original After Effects Graph Editor curve from appearance alone. The objective is an evidence-bound behavioral curve that the three renderers can execute equivalently.

After W1, proceed through camera/depth/occlusion, retention/stimulus, audio-SFX grammar, typography/color/FX tiering, then cross-renderer parity and finally three-content generalization.
