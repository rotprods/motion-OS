# S04 Source-Bound Fidelity Gauntlet — Defect Graph

Authority: `MEASURED_SOURCE_BOUND_LOCAL_RUN` for measurements; causal/root-layer claims remain explicitly weaker.

Source: `screenrecording_2026-08-26_173251`, frames `145..215`, 71 frames @ 30fps.  
Renderer artifact: workflow `33311662438`, artifact `9732173147`, head `85c45c68faefe50f76217216bae075d32804eaca`.

## What passed

- Caption visibility intervals match the measured source-visible tracks exactly: setup `0..68`, hero `10..68`, tail `38..68`.
- Source and overlay share the same 512×1108 / 30fps coordinate authority.
- Structural render and transparent overlay were physically executed in CI.

## P1 defects

### S04-DEF-001 — setup visible bounds
- mean bbox IoU: `0.5505`
- mean centroid error: `6.73px`
- mean Y offset: `+6.78px`
- root-cause family: SVG font metrics are not calibrated to source-visible bounds.

### S04-DEF-002 — hero visible bounds
- mean bbox IoU: `0.8367`
- mean centroid error: `6.53px`
- mean area error: `18.09%`
- mean top offset: `-14.08px`
- mean height excess: `+15.11px`
- root-cause family: SVG font metrics are not calibrated to source-visible bounds.

### S04-DEF-003 — tail visible bounds
- mean bbox IoU: `0.7445`
- mean centroid error: `5.02px`
- mean area error: `21.43%`
- root-cause family: SVG font metrics are not calibrated to source-visible bounds.

### S04-DEF-004 — emphasis audio onset
- source strongest transient proxy: local frame `8.85`
- rendered synthetic transient proxy: local frame `16.35`
- renderer lateness: `+7.50` frames
- source ActionInventory independently links the strong onset near source frame 154 (`≈ local 9`).
- SFX class remains inferred from the mixed master; timing is the measured claim.

## High-confidence structural inference — common caption parent

After the hero entrance, source-visible width trajectories behave almost as one transform:

- setup ↔ hero scale correlation: `0.997520`
- setup ↔ tail correlation: `0.993996`
- hero ↔ tail correlation: `0.996812`
- setup/hero normalized RMSE: `0.004853`

Interpretation: the hero has an independent entrance, but once established the caption system strongly behaves as if it shares a screen-space parent/reframe transform. This is an `EVIDENCE_BOUND_INFERENCE`, not proof of the original After Effects parenting graph.

AE reconstruction implication:

```text
S04_MASTER
├── SUBJECT_PRECOMP
└── CAPTION_GROUP_NULL / PRECOMP   # inferred shared transform
    ├── SETUP
    ├── HERO_CIENTIFICAMENTE       # independent entrance before joining common transform
    └── TAIL_IMPOSIBLE
```

Remotion/HyperFrames should preserve the same relationship semantically rather than independently tuning three unrelated scaling curves.

## P2 visible-color proxies

These compare visible video output after grade/compression against transparent renderer pixels. They do **not** identify the original AE Fill values.

- hero ΔE76 proxy: `16.46`
- tail ΔE76 proxy: `11.45`
- setup ΔE76 proxy: `2.29`

Do not promote these measurements into exact original color tokens without a clean compositing plate.

## Repair wave

1. Calibrate visible SVG text bounds by role, using measured source-visible bounding boxes as the physical output target.
2. Move synthesized impact from the historical local-frame 15 anchor to a measured-onset-aligned anchor near local frame 8/9.
3. Preserve the shared-caption-parent inference in the S04 graph/contract.
4. Rerender on the exact branch head.
5. Re-run `scripts/qualify_s04_fidelity.py` against the private source frames and new overlay.
6. Accept geometry only if mean bbox IoU ≥0.90, mean centroid error ≤3px and mean area error ≤8% for every caption role.
7. Accept onset timing only if absolute error ≤1.5 frames.
8. Do not claim exact font/stem/camera-depth fidelity from these gates.

## Residual unknowns

- exact font identity and font files;
- original AE Graph Editor curves;
- original compositing/precomp structure;
- original isolated SFX stem;
- exact pre-grade caption fill token;
- full subject/depth/camera decomposition without a source-clean plate.

These remain explicit `UNKNOWN`, not silently approximated authority.
