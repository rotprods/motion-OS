# S16 Defect Graph

Authority: append-only reconstruction / qualification ledger for `S16_FACTOR_X`.

## S16-DEF-AUTH-001 — conversational phantom render head

- domain: `CONTINUITY / AUTHORITY / PROVENANCE`
- severity: `P0 authority-integrity blocker`
- discovered during: zero-assumption reconciliation before continuing the S16 source-bound gauntlet
- stale conversational claim: a prior session described S16 as physically green at an abbreviated head `65e18050...` and implied an artifact/source-bound diff existed.
- durable Git authority at reconciliation:
  - branch `feat/reverse-engineering-s16-remotion-golden-v1` -> `628b3dcfba449ad71ddfce18a7efbe741fecfd63`
  - PR #125 head -> the same `628b3dcfba449ad71ddfce18a7efbe741fecfd63`
  - PR #125 is rooted at PR #64 base `2e26e311e506b6aaaa32f827e1579ddaa1e3ea58`.
- provider resolution: `65e18050` is not resolvable as a repository commit and is not present in the current PR #125 commit genealogy.
- durable Drive authority at reconciliation:
  - `GOLDEN_S16/00_SOURCE` contains source evidence.
  - `GOLDEN_S16/01_CONTRACT` contains measured source contracts.
  - `GOLDEN_S16/02_STRUCTURAL_RENDER` was empty.
  - `GOLDEN_S16/03_FIDELITY` was empty.
- Event Bus authority: Issue #39 contained the S16 `WORK_STARTED` event but no later durable S16 render/qualification checkpoint proving the stale claim.
- PR conversation authority: PR #125 contained no comments recording such an artifact or qualification.
- root-cause family: `CONVERSATIONAL_EXECUTION_CLAIM_WITHOUT_DURABLE_PROVIDER_EVIDENCE`.
- permanent invariant: `NO_EXECUTION_OR_FIDELITY_AUTHORITY_FROM_CHAT_STATE_ALONE`.
- status: `AUTHORITY_RECONCILED / STALE_CLAIM_INVALIDATED`.

```text
CHAT_CLAIM
  -> REFERENCES -> NON_RESOLVABLE_HEAD
  -> LACKS -> DURABLE_RUN_ARTIFACT
  -> LACKS -> DRIVE_RENDER_EVIDENCE
  -> CANNOT_GRANT -> EXECUTION_AUTHORITY
  -> REPAIRED_BY -> EXACT_HEAD_REVALIDATION
  -> GENERALIZES_TO -> NO_CHAT_ONLY_EXECUTION_AUTHORITY
```

## S16-DEF-RENDER-001 — descending physical Y used as Remotion interpolation domain

- domain: `RENDERER / MOTION MAPPING / RUNTIME`
- severity: `P0 physical-render blocker`
- failing exact-head run: `33506760636`; job `99852522767`; head `222856b3ecdb6a1c241442dbc6b4a261169b69c8`.
- pre-render gates: `13 passed`; TypeScript succeeded; composition enumeration succeeded.
- failure stage: physical `GoldenS16FactorX` render, local frame `2`.
- provider error: `inputRange must be strictly monotonically increasing but got [858,828,807,792]`.
- root-cause family: `DESCENDING_PHYSICAL_AXIS_USED_DIRECTLY_AS_MONOTONIC_INTERPOLATION_DOMAIN`.
- source trajectory is not defective: the measured column physically rises, therefore Y decreases.
- authority-preserving repair: identical mapping expressed as ascending Y domain `[792,807,828,858] -> [1,.86,.52,.20]`.
- regression: `test_column_opacity_calibration_has_monotonic_runtime_domain_and_preserves_mapping`.

### Resolution checkpoint

- repaired implementation head: `3506a5331fc042a5508d0db48beb92b6fbcb5f58`.
- exact-head run: `33507333754`; job `99854407982`.
- physical render: PASS.
- 92-frame target-isolated overlay: PASS.
- mechanical verifier: PASS.
- artifact: `9800260540`, digest `sha256:b8ceb1280fb8105e5f3aa4109b5633ad4b45c61fbbed764e858b356620688133`.
- status: `REPAIRED / EXACT_HEAD_EXECUTION_VERIFIED`.

```text
MEASURED_COLUMN_RISE
  -> DECREASES -> SCREEN_SPACE_Y
  -> WAS_USED_AS -> INTERPOLATE_INPUT_RANGE
  -> VIOLATES -> STRICT_MONOTONIC_INCREASE
  -> REPAIRED_BY -> ASCENDING_DOMAIN_SAME_MAPPING
  -> VERIFIED_BY -> EXACT_HEAD_PHYSICAL_RENDER
```

## S16-DEF-MEAS-001 — hand-compressed renderer projection diverges from durable full-frame track

- domain: `SOURCE MEASUREMENT / COMPILER / TEMPORAL GEOMETRY`
- severity: `P1 visible-geometry fidelity defect`
- discovered by: independent source-bound qualifier on artifact `9800260540` against Drive `s16_measured_track_v1.json` (`178eElG7KSsUILKpmIijqaiHiBLculKeO`).
- durable measured-track SHA256: `2b12cf3e3f30a4ddff46b931cff15ba7080e4f94fd78cfe0957f3fa076fe283b`.
- column gate: PASS; mean IoU `0.9982856`, centroid error `0.1889 px`.
- question-mark gate: FAIL; mean IoU `0.9483894`, minimum IoU `0.7898089`, centroid error `2.6319 px`.
- representative contradictions:
  - local14 Drive question bbox `[106,626,74,175]`; old Git projection `[106,621,74,163]`.
  - local91 Drive question bbox `[96,582,78,191]`; old Git projection `[106,582,74,186]`.
  - authoritative Factor X local21 remains `y=925`, while the old sparse projection omitted local21 and interpolated upward prematurely.
- root-cause family: `HAND_AUTHORED_SPARSE_PROJECTION_NOT_MECHANICALLY_DERIVED_FROM_FULL_FRAME_AUTHORITY`.
- rejected repair: loosen thresholds; manually tune only failing frames; reinterpret source evidence.
- architecture repair: compile the full 92-frame authoritative Drive track directly into executable `MEASURED_SOURCE_BOUND_FULL_FRAME_PROJECTION_V2`, with `FULL_FRAME_NO_INTERPOLATION` and the durable source-track SHA bound in code.
- permanent compiler invariant: a reduced projection may only replace full-frame evidence if an automated equivalence test proves it stays inside declared tolerances.
- original status: `OPEN_PENDING_FULL_FRAME_PROJECTION_V2`.

```text
FULL_FRAME_SOURCE_TRACK
  -> WAS_REDUCED_TO -> HAND_AUTHORED_KEYFRAMES
  -> INTRODUCED -> TEMPORAL_AND_BBOX_DRIFT
  -> REPAIRED_BY -> MECHANICAL_FULL_FRAME_PROJECTION
  -> GENERALIZES_TO -> REDUCTION_REQUIRES_EQUIVALENCE_PROOF
```

## S16-DEF-QA-001 — Factor X oracle compares layout-proxy authority to fallback glyph bbox

- domain: `QA / AUTHORITY TYPE / TYPOGRAPHY`
- severity: `P1 qualification-integrity defect`
- discovered by: independent source-bound qualifier on artifact `9800260540`.
- observed factor result before repair: mean IoU `0.7649196`, minimum IoU `0.3652519`, centroid error `11.2301 px`; timing first/last frames exact.
- root-cause family: `CROSS_AUTHORITY_GEOMETRY_COMPARISON_LAYOUT_PROXY_VS_GLYPH_OUTLINE`.
- authoritative source measurement classifies Factor X as `MEASURED_RIGHT_X_ANCHOR_PLUS_STABLE_VISIBLE_LAYOUT_PROXY`; exact source font/glyph outline is UNKNOWN.
- old measurement overlay rendered fallback `Arial Black` text, so the qualifier observed its glyph pixels instead of the source-authorized layout proxy.
- representative symptom: local21 expected layout proxy `[136,925,315,62]`, observed fallback-glyph bbox `[260,915,191,51]`.
- rejected repair: lower Factor X threshold; claim fallback glyphs exact; alter source layout proxy to fit fallback font.
- architecture repair: layout measurement mode emits the factor layout box as a flat unique-color target. Production render keeps fallback text; exact font/glyph fidelity remains explicitly blocked.
- original status: `OPEN_PENDING_AUTHORITY_ALIGNED_MEASUREMENT_SURFACE`.

```text
SOURCE_FACTOR_AUTHORITY = LAYOUT_PROXY
  -> ORACLE_OBSERVED -> FALLBACK_GLYPH_PIXELS
  -> COMPARES_DIFFERENT_TYPES -> FALSE_FIDELITY_DEFECT
  -> REPAIRED_BY -> LAYOUT_PROXY_MEASUREMENT_CHANNEL
  -> KEEPS_BLOCKED -> EXACT_FONT_AND_GLYPH_MORPHOLOGY
```

## Resolution ledger — exact-head `e34b3806...`

Authoritative rerun after `S16-DEF-MEAS-001` and `S16-DEF-QA-001` repairs:

- head: `e34b38061e2ad1d322238a011f5c6b9660b883ee`.
- `Remotion Golden S16` run: `33508449494` -> SUCCESS.
- `Merge Safe` run: `33508449528` -> SUCCESS.
- artifact: `9800670307`.
- artifact digest: `sha256:01a8a99943698a2669cf887b6a406652d07cd93e62f2e0c37b4f3d9c1794f325`.
- Drive artifact: `17SuVnL2ByUJLiolbl-qNJeqZCBjcUKri`.
- layout qualification Drive ID: `1DLr6lMwSgLrzp-TcW2JZpZuZAZ2kUR_U`.
- audio qualification Drive ID: `11Ilq0GgccRmLvYsFGlarK3pwoDTk3XnL`.

Source-bound layout/timing results:

- column: mean/min IoU `1.0`, centroid error `0 px`, timing error `0f`.
- question mark: mean/min IoU `1.0`, centroid error `0 px`, timing error `0f`.
- Factor X layout proxy: mean/min IoU `1.0`, centroid error `0 px`, timing error `0f`.
- all declared P0/P1 visible layout/timing gates: PASS.

Audio timing proxy:

- mean absolute transient error: `0.395763f`.
- max absolute transient error: `0.902109f`.
- gate: `1.5f`.
- result: PASS.

Resolution state:

- `S16-DEF-MEAS-001` -> `REPAIRED / EXACT_HEAD_SOURCE_BOUND_REQUALIFIED`.
- `S16-DEF-QA-001` -> `REPAIRED / AUTHORITY_ALIGNED_ORACLE_REQUALIFIED`.
- `S16-DEF-RENDER-001` remains `REPAIRED / EXACT_HEAD_EXECUTION_VERIFIED`.

## S16-DEF-FID-001 — structural proxy morphology remains below exact-source fidelity

- domain: `FIDELITY CEILING / STRUCTURAL PROXY APPEARANCE`
- severity: `P2; does not reopen qualified layout/timing contract`
- authority: `ADVISORY_SOURCE_VS_RENDER_VISUAL_REVIEW`.
- evidence head/artifact: `e34b3806...` / `9800670307`.
- Drive review: `1QDKeWse4PEhx4o9tZirBLZHFtwD1oMGg`.
- Drive source/render contact sheet: `11MzRd6mYxLpFsAmYYfFLb5k0cAHvbtIh`.
- fallback question-mark visible component under-fills the source red-component morphology: advisory mean bbox IoU `0.480919`, min `0.459273` across the color-observable production proxy frames.
- Factor X fallback font also differs from source glyph metrics; at local54 the source X anchor is `[397,721,54,61]` while the rendered fallback rightmost component is approximately `[400,729,49,50]`.
- interpretation: these are **not** failures of the now-qualified layout/timing tracks. They prove that layout qualification cannot be promoted to exact glyph/path/material or original-asset fidelity.
- repair options for a future exact-reconstruction tier: bind original source assets/font if recovered, or add explicitly labeled fallback visible-bounds calibration without claiming original identity.
- prohibited inference: do not claim exact question-mark path/material, exact Factor X font/glyph outline, or exact column asset/material from the structural proxy.
- status: `OPEN_AS_EXPLICIT_FIDELITY_CEILING / NOT_P0_P1_LAYOUT_BLOCKER`.

## Final source-fidelity frontier

Current highest S16 authority:

`STRUCTURAL_RENDER_EXECUTED + SOURCE_BOUND_LAYOUT_TIMING_QUALIFIED + AUDIO_TIMING_PROXY_QUALIFIED`.

This does **not** equal full source reconstruction or `CANONICAL_TEMPLATE` promotion. `full_9d_fidelity_validated = false` remains mandatory.

Remaining blocked dimensions include exact original column asset/material/lighting, exact question-mark glyph/path/material, exact `Factor X` font/glyph outline, original AE/precomp/Graph Editor/effect graph, exact opacity curves, isolated stems/SFX identities, unique original COLUMN-vs-QUESTION z-order, speaker pixel fidelity in structural mode, and causal origin of local87+ global reflow.
