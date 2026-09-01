# S04 — Post-repair source-bound qualification v2

Authority: `SOURCE_BOUND_PARTIAL_QUALIFICATION_P0P1_CLOSED`

Source: `9b3076cb...`, frames 145..215, 71 frames @ 30fps, 512×1108.  
Renderer: Remotion head `0790a005f391327b731464d269e42864c64ea4cb`; workflow `33321379790`; artifact `9734987644`.

## P1 closure

| Defect | Baseline | Post-repair | Gate | Result |
|---|---:|---:|---|---|
| Setup bbox IoU | 0.5505 | 0.9149 | ≥0.90 | PASS |
| Setup centroid error | 6.73px | 1.19px | ≤3px | PASS |
| Setup area error | 2.47% | 5.19% | ≤8% | PASS |
| Hero bbox IoU | 0.8367 | 0.9900 | ≥0.90 | PASS |
| Hero centroid error | 6.53px | 0.32px | ≤3px | PASS |
| Hero area error | 18.09% | 0.72% | ≤8% | PASS |
| Tail bbox IoU | 0.7445 | 0.9688 | ≥0.90 | PASS |
| Tail centroid error | 5.02px | 0.51px | ≤3px | PASS |
| Tail area error | 21.43% | 0.84% | ≤8% | PASS |
| Audio onset error | 7.50f | 0.449f | ≤1.5f | PASS |

The four measured P1 defects are closed at the reconstructed-output level.

## What this does *not* prove

- exact original font identity;
- original After Effects parenting/precomp/effect graph;
- separation of source-native subject motion from editorial reframe;
- original SFX stem identity;
- original pre-grade fill tokens;
- full depth/camera fidelity of the flattened source plate.

`full_9d_fidelity_validated = false` remains deliberate.

## 9D projection

- **TEMPORAL** — `PASS`
- **TYPOGRAPHY** — `STRUCTURAL_PASS_IDENTITY_BLOCKED`
- **MOTION** — `PASS_CAPTION_TRAJECTORIES_ONLY`
- **CAMERA** — `BLOCKED_SOURCE_LAYER_LIMIT`
- **DEPTH** — `NOT_APPLICABLE_TO_RECONSTRUCTED_CAPTION_PLANE / SOURCE_NATIVE_PLATE_UNQUALIFIED`
- **COLOR** — `P2_PROXY_MISMATCH_REMAINS`
- **FX** — `PARTIAL_BLOCKED`
- **AUDIO** — `PASS_TIMING_IDENTITY_BLOCKED`
- **RETENTION** — `PASS_MODELED_EDITORIAL_BEATS`

## Adversarial residual

Mean geometry gates pass, but exact glyph morphology does not. The source font is not identified and a flattened/compressed source cannot prove original font files or AE text metrics. Therefore typography remains `STRUCTURAL_PASS_IDENTITY_BLOCKED`, not exact typography fidelity. The setup track also contains lower per-frame IoU around morph/overlap windows; this remains an explicit residual rather than being hidden by the mean score.

## Next graph frontier

S11_UI_LIST can enter structural reconstruction independently. S04 remains a qualified partial golden scene and must not be promoted to `CANONICAL_TEMPLATE` until cross-renderer parity + generalization gates exist.
