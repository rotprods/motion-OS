# S11 Source-Bound Fidelity Gauntlet — Defect Graph

Authority: `MEASURED_SOURCE_BOUND_LOCAL_RUN` for visible-output measurements; causal/original-project claims remain weaker.

Source: `screenrecording_2026-08-26_173251`, frames `405..534`, 130 frames @ 30fps.

## Baseline structural authority

- PR #107 baseline head `71b61f69d3310c6f0005e96f21047984a8c144a1` physically rendered 130 frames at 30fps / 512×1108 with audio and a transparent editorial overlay.
- Baseline workflow: `33379042661` SUCCESS.
- Baseline artifact digest: `sha256:f227f3d50a4919138cd6afad3e111d6d0f2755f0ef830f30b86d171f8273a82a`.
- Mechanical execution never implied source fidelity.

## Original P1 defects

### S11-DEF-001 — hero pill geometry / group motion — CLOSED_AT_VISIBLE_OUTPUT_GATE
Baseline mean pill IoU ≈ `0.694`, centroid error ≈ `22.7px`. Root cause: `SUMMARY_KEYFRAMES_COLLAPSED_A_CONTINUOUS_SOURCE_VISIBLE_TRACK`.

Repair: measured source-visible pill track consumed by `sourceMeasuredTrack.ts`.

Post-repair measurement against exact physical overlay:
- mean IoU `0.9945616731`
- mean centroid error `0.24593px`
- mean area error `0.32985%`
- minimum IoU `0.9757896591`

### S11-DEF-002 — boxed `absolutamente` geometry — CLOSED_AT_VISIBLE_OUTPUT_GATE
Baseline mean IoU ≈ `0.0043`. Root cause: `SEMANTIC_ANCHOR_USED_AS_PHYSICAL_LAYOUT_AUTHORITY`.

Post-repair:
- mean IoU `0.9850000978`
- mean centroid error `0.23438px`
- mean area error `0.58417%`
- first-visible error `0 frames`

### S11-DEF-003 — X row entrance/scale — CLOSED_AT_VISIBLE_OUTPUT_GATE
Baseline first-visible error `+6 frames` with undersized 68×68 generic circle. Root cause: `STAGGER_SUMMARY_LOST_SUBEVENT_ONSET_AND_SCALE_TRACK`.

Post-repair:
- first-visible error `0 frames`
- mean IoU `0.9909730846`
- centroid error `0.26266px`
- area error `0.34689%`

### S11-DEF-004 — diamond row entrance/scale — CLOSED_AT_VISIBLE_OUTPUT_GATE
Baseline first-visible error `+9 frames`. Same root-cause family.

Post-repair:
- first-visible error `0 frames`
- mean IoU `0.9906977494`
- centroid error `0.22786px`
- area error `0.40779%`

### S11-DEF-005 — megaphone row entrance/scale — CLOSED_AT_VISIBLE_OUTPUT_GATE
Baseline first-visible error `+12 frames`. Same root-cause family.

Post-repair:
- first-visible error `0 frames`
- mean IoU `0.9901499412`
- centroid error `0.23979px`
- area error `0.49859%`

### S11-DEF-006 — support-copy line system — REFINED / PARTIAL
Baseline used a generic 3/4/3-line recipe and incorrect horizontal anchoring. Repair now derives the support-copy column relationally from measured icon boxes and uses source-like row-specific line counts/spacing. Exact textual morphology remains outside this visible-geometry gate.

## New escaped-failure family found by the gauntlet

### S11-DEF-007 — measurement-oracle cross-component contamination — CLOSED + PERMANENT REGRESSION

Symptom after the renderer repair: the first qualifier still reported pill mean IoU ≈ `0.9185` and centroid error ≈ `4.8px`, suggesting a residual renderer defect.

Adversarial inspection disproved that conclusion. Direct source/renderer frame checks showed the measured pill geometry was effectively exact. The fidelity oracle used an 18px padded connected-component crop around the dark pill. Because a grey/dark arrow touches or approaches the pill below it, the crop admitted that adjacent component and expanded the observed pill bbox.

Root cause:
`MEASUREMENT_ORACLE_CROSS_COMPONENT_CONTAMINATION`

Repair:
- dark pill measurement uses zero padding and remains inside the expected source-visible target box;
- white/glyph/icon components retain bounded padding;
- a synthetic regression fixture explicitly draws a dark pill with a touching arrow and asserts the oracle cannot absorb it.

Invariant:
> A fidelity oracle may not let an adjacent visual component expand the measurement domain of the target entity merely because both components share color/connectivity.

This is a test-system bug, not a renderer bug. The history remains preserved rather than rewriting the false intermediate observation away.

## Visible-output qualification after oracle repair

```text
pill                  IoU 0.99456 | centroid 0.246px | area 0.330%
boxed absolutamente   IoU 0.98500 | centroid 0.234px | area 0.584%
X row                 IoU 0.99097 | centroid 0.263px | area 0.347% | timing 0f
diamond row           IoU 0.99070 | centroid 0.228px | area 0.408% | timing 0f
megaphone row         IoU 0.99015 | centroid 0.240px | area 0.499% | timing 0f
```

All declared P0/P1 visible-output geometry/timing gates PASS.

## Graph interpretation

```text
DECODED_SOURCE
   │
   ├─ MEASURES ─► SOURCE_VISIBLE_TRACK
   │                    │
   │                    ├─ CONSTRAINS ─► S11_SCENE_CONTRACT
   │                    │                     │
   │                    │                     └─ COMPILES_TO ─► REMOTION_OVERLAY
   │                    │
   │                    └─ VERIFIED_BY ─► FIDELITY_ORACLE
   │                                          │
   │                                          ├─ FAILED_BY ─► S11-DEF-007
   │                                          └─ REPAIRED_BY ─► TARGET_ISOLATION_INVARIANT
   │
   └─ DOES_NOT_PROVE ─► ORIGINAL_AE_GRAPH / EXACT_FONT / ORIGINAL_SFX_STEMS
```

## Remaining P2 / UNKNOWN domains

- exact font identities and glyph morphology;
- original After Effects parenting/precomp/effect graph;
- original Graph Editor curves;
- exact arrow path/mask morphology and whether it is shape-layer or baked graphic;
- original isolated SFX stems, layering and envelopes;
- exact pre-grade color tokens;
- full causal decomposition of camera/reframe/depth from a flattened source;
- complete FX/material stack;
- support-copy semantic text if source detail is insufficient.

## Authority ceiling

S11 may now be described as:

`SOURCE_BOUND_VISIBLE_GEOMETRY_P0P1_CLOSED`

It may NOT be described as:

`FULL_9D_FIDELITY_VALIDATED`
`ORIGINAL_AE_PROJECT_RECONSTRUCTED`
`CANONICAL_TEMPLATE`
`EMPIRICALLY_GENERALIZED`

The next promotion requires further 9D domains and later cross-renderer/generalization qualification.
