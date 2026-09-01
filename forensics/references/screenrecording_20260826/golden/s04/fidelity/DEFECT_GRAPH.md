# S04 Source-Bound Fidelity Gauntlet — Defect Graph

Authority: measurements are `MEASURED_SOURCE_BOUND`; causal claims weaker unless explicitly stated. Historical states are preserved by commit lineage and are never silently rewritten.

Source: `screenrecording_2026-08-26_173251`, frames `145..215`, 71 frames @ 30fps.

## Historical defect state — pre-repair

Initial source-bound qualification exposed four P1 defects:

- `S04-DEF-GEOMETRY-SETUP` — mean bbox IoU `0.5505`, centroid `6.73px`; family `SVG_FONT_METRICS_NOT_CALIBRATED_TO_SOURCE_VISIBLE_BOUNDS`.
- `S04-DEF-GEOMETRY-HERO` — mean bbox IoU `0.8367`, centroid `6.53px`, mean area error `18.09%`; same family.
- `S04-DEF-GEOMETRY-TAIL` — mean bbox IoU `0.7445`, centroid `5.02px`, mean area error `21.43%`; same family.
- `S04-DEF-AUDIO-ONSET` — source emphasis transient near local `8.85`, old synthetic render peak local `16.35`, lateness `+7.50f`; family `SYNTHETIC_IMPACT_ANCHORED_TO_HISTORICAL_INFERENCE_NOT_MEASURED_ONSET`.

P2 visible-color proxies also differed (`hero ΔE76≈16.46`, `tail≈11.45`) but do not identify original AE fill tokens.

## Repair

The renderer moved caption placement to the measured screen-space track, calibrated fallback SVG visible bounds by role, preserved the evidence-bound shared-caption-parent relationship, and moved the synthetic impact anchor from the historical local-15 inference toward the measured local-9 onset.

The exact reconstruction artifact used for the post-repair measurement is:

- renderer head: `0790a005f391327b731464d269e42864c64ea4cb`;
- workflow: `33321379790` -> SUCCESS;
- artifact: `9734987644`;
- digest: `sha256:e3943283f2f63add79b3a51016fc7d1349053223e6f809952443be46104e214d`;
- Drive artifact: `1_q_LfzsQjcGyWQa6I0u0Ujy-AYyMQYJe`;
- Drive qualification: `1D5bfqJhU6-_fJyKTotUz1wl6WT8T7l4Q`;
- Drive qualification hypergraph: `1IY15RWLALxjLE1OH1_j2g1XqCALsxOP1`.

## Resolution checkpoint — declared P0/P1 layout/timing gates

| Defect | Post-repair | Gate | State |
|---|---:|---:|---|
| setup mean bbox IoU | `0.914885` | `>=0.90` | CLOSED |
| setup mean centroid | `1.191px` | `<=3px` | CLOSED |
| setup mean area error | `5.188%` | `<=8%` | CLOSED |
| hero mean bbox IoU | `0.989969` | `>=0.90` | CLOSED |
| hero mean centroid | `0.324px` | `<=3px` | CLOSED |
| hero mean area error | `0.722%` | `<=8%` | CLOSED |
| tail mean bbox IoU | `0.968761` | `>=0.90` | CLOSED |
| tail mean centroid | `0.510px` | `<=3px` | CLOSED |
| tail mean area error | `0.836%` | `<=8%` | CLOSED |
| audio onset absolute error | `0.449f` | `<=1.5f` | CLOSED |

Current declared capability state:

`SOURCE_BOUND_PARTIAL_QUALIFICATION_P0P1_CLOSED`

## S04-ADV-GLYPH-001 — mean gate does not prove exact glyph morphology

Adversarial per-frame replay of the post-repair overlay found a residual the mean gate alone would hide:

- setup minimum bbox IoU: `0.6913195796`;
- worst local frame: `66`;
- additional low frames: `19,20,21,22,23,24,65`;
- hero minimum IoU: `0.901639`;
- tail minimum IoU: `0.931034`.

The setup residual is classified `P2_FIDELITY_CEILING_NOT_ACTION_LAYOUT_BLOCKER`, not silently ignored. The source track proves screen-space layout/trajectory; the renderer uses fallback fonts and the exact source font/glyph outline is unavailable. Therefore P0/P1 closure **cannot** promote typography to pixel-exact font/glyph authority.

Future exact-reconstruction options:

1. recover and bind the original font;
2. create an explicit source-locked glyph/mask tier from reference evidence;
3. calibrate visible bounds further while retaining `FONT_IDENTITY_UNKNOWN`.

Structural-template mode may preserve measured layout + font class without source-locking literal glyphs/copy.

## High-confidence structural inference — common caption parent

After hero entrance the measured width trajectories support one shared screen-space parent/reframe behavior:

- setup ↔ hero correlation `0.997520`;
- setup ↔ tail `0.993996`;
- hero ↔ tail `0.996812`;
- setup/hero normalized RMSE `0.004853`.

This is `EVIDENCE_BOUND_INFERENCE`, not proof of the original After Effects hierarchy.

```text
S04_MASTER
├── SUBJECT_PRECOMP
└── CAPTION_GROUP_PARENT          # behavioral inference
    ├── HERO_CIENTIFICAMENTE      # independent entrance
    ├── SETUP
    └── TAIL_IMPOSIBLE
```

## Graph closure

```text
PRE_REPAIR_MEASUREMENT
  -> EXPOSES -> 3x CAPTION_GEOMETRY_P1
  -> EXPOSES -> AUDIO_ONSET_P1
  -> CAUSES -> MEASURED_RENDERER_REPAIR
  -> VERIFIED_BY -> HEAD_0790_PHYSICAL_RENDER
  -> MEASURED_BY -> DRIVE_POSTREPAIR_QUALIFICATION
  -> CLOSES -> DECLARED_P0P1_LAYOUT_TIMING_GATES
  -> DOES_NOT_CLOSE -> EXACT_GLYPH_MORPHOLOGY
  -> DOES_NOT_CLOSE -> FULL_9D
  -> LEAVES -> P2_COLOR_PROXY + P2_GLYPH_CEILING + UNKNOWN_AE/STEM/CAMERA_DEPTH
```

## Residual unknowns / blocked dimensions

- exact font identity and font files;
- exact source glyph morphology under fallback renderer fonts;
- original AE Graph Editor curves;
- original precomp/parenting/effect graph;
- original isolated SFX stem/timbre;
- exact pre-grade caption fill tokens;
- causal separation of source-native subject motion from editorial reframe;
- full subject/depth/camera decomposition from the flattened source.

`full_9d_fidelity_validated = false` and `canonical_template = false` remain mandatory.
