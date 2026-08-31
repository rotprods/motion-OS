# S11 Source-Bound Fidelity Gauntlet — Defect Graph

Authority: `MEASURED_SOURCE_BOUND_LOCAL_RUN` for visible-output measurements; causal/original-project claims remain weaker.

Source: `screenrecording_2026-08-26_173251`, frames `405..534`, 130 frames @ 30fps.  
Renderer baseline: PR #107 head `71b61f69d3310c6f0005e96f21047984a8c144a1`, workflow `33379042661`, artifact digest `sha256:f227f3d50a4919138cd6afad3e111d6d0f2755f0ef830f30b86d171f8273a82a`.

## Baseline structural pass

- 130 frames / 30fps / 512×1108: PASS.
- audio stream present: PASS.
- transparent editorial overlay physically rendered: PASS.
- Merge Safe exact-head: PASS.

These prove execution, not fidelity.

## P1 defects discovered by source-bound comparison

### S11-DEF-001 — hero pill geometry / group motion
- mean pill bbox IoU: `0.69391`.
- mean pill centroid error: `22.69px`.
- minimum pill bbox IoU: `0.32204`.
- source continues growing/moving upward through late frames; baseline renderer flattens the height and stops vertical motion too early.
- root-cause family: `SUMMARY_KEYFRAMES_COLLAPSED_A_CONTINUOUS_SOURCE_VISIBLE_TRACK`.

### S11-DEF-002 — boxed `absolutamente` geometry
- mean bbox IoU against source-visible white emphasis box: `0.00433`.
- baseline renderer uses a fixed 141×23 box around `(211,493)` while source grows/moves approximately from `212×30 @ (190,424)` to `235×34 @ (182,280)`.
- root-cause family: `SEMANTIC_ANCHOR_USED_AS_PHYSICAL_LAYOUT_AUTHORITY`.

### S11-DEF-003 — X row entrance timing + size
- source first visible circle proxy: local frame `77`.
- renderer first visible circle proxy: local frame `83`.
- lateness: `+6 frames`.
- source circle grows to ~92×90; baseline remains 68×68.
- root-cause family: `STAGGER_SUMMARY_LOST_SUBEVENT_ONSET_AND_SCALE_TRACK`.

### S11-DEF-004 — diamond row entrance timing + size
- source first visible circle proxy: local frame `82`.
- renderer first visible circle proxy: local frame `91`.
- lateness: `+9 frames`.
- source circle grows to ~92×91; baseline remains 68×68.
- root-cause family: `STAGGER_SUMMARY_LOST_SUBEVENT_ONSET_AND_SCALE_TRACK`.

### S11-DEF-005 — megaphone row entrance timing + size
- source first visible circle proxy: local frame `88`.
- renderer first visible circle proxy: local frame `100`.
- lateness: `+12 frames`.
- root-cause family: `STAGGER_SUMMARY_LOST_SUBEVENT_ONSET_AND_SCALE_TRACK`.

### S11-DEF-006 — support-copy line system
- baseline lines begin too far left and use a generic 3/4/3-line recipe.
- source rows show different line counts/vertical rhythms and share a larger right-side text column anchored around x≈186.
- root-cause family: `GENERIC_UI_PLACEHOLDER_REPLACED_SOURCE_SPECIFIC_INFORMATION_GEOMETRY`.

## P2 / residual domains

### S11-RISK-001 — small words
`debe`, `dejar`, `claro` are visible and temporally useful, but exact font metrics remain unknown. Their source positions can be tied to the measured emphasis-box trajectory without claiming original AE typography.

### S11-RISK-002 — arrow morphology
Arrow timing is supported, but its precise source curve/mask/path is not yet independently vector-fitted.

### S11-RISK-003 — source chrome
The screen-recording status/dynamic-island chrome is a `SOURCE_LOCK`, not reusable editing DNA.

### S11-RISK-004 — audio
Synthetic UI hits prove audio-domain execution only. Original isolated SFX identity, envelope and layering remain unavailable from the flattened mixed master.

## Repair graph

```text
SOURCE_VISIBLE_TRACK
  ├─ MEASURES → PILL_GEOMETRY
  ├─ MEASURES → BOXED_ABSOLUTAMENTE
  ├─ MEASURES → X_ROW_ICON
  ├─ MEASURES → DIAMOND_ROW_ICON
  └─ MEASURES → MEGAPHONE_ROW_ICON

S11-DEF-001..006
  ├─ CAUSED_BY → LOSSY_SUMMARY_OR_GENERIC_PLACEHOLDER
  ├─ REPAIRED_BY → sourceMeasuredTrack.ts
  ├─ CONSTRAINS → S11UiList renderer
  └─ VERIFIED_BY → rerender + source-bound diff
```

## Repair law

The repair must live in the shared S11 scene contract/track and remain renderer-consumable. Do not introduce a one-off visual correction that only the Remotion composition knows.

## Acceptance gate for this wave

- pill mean bbox IoU ≥ 0.92 and centroid error ≤ 3px;
- boxed emphasis mean bbox IoU ≥ 0.90;
- row icon first-visible error ≤ 1 frame for X / diamond / megaphone;
- final row icon centroid error ≤ 3px and area error ≤ 8%;
- mechanical render contract still passes;
- no claim of exact fonts, original AE topology, SFX stems or full-scene 9D fidelity.
