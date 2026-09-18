# S14 Defect Graph

Authority: append-only reconstruction/qualification ledger. A defect is not a source-fidelity finding unless explicitly backed by source-bound measurement.

## S14-DEF-CI-001 — truncated GitHub Action revision
- domain: `CI / SUPPLY_CHAIN`
- observed run: `33453023535`
- root-cause family: `INVALID_OR_TRUNCATED_ACTION_PIN`
- authority impact: renderer `NOT_RUN`; never source-fidelity evidence.
- status: `SUPERSEDED_BY_S14-DEF-CI-002`

## S14-DEF-CI-002 — manually reconstructed immutable revision
- domain: `CI / SUPPLY_CHAIN / AUTHORITY`
- observed run: `33453202698`
- root-cause family: `MANUALLY_RECONSTRUCTED_ACTION_SHA_WITHOUT_PROVIDER_VALIDATION`
- repair: provider-valid setup-node revision + full-SHA regression.
- status: `CLOSED`

## S14-DEF-TEST-001 — dynamic import harness registration
- domain: `QA / TEST HARNESS`
- observed run: `33453466612`
- root-cause family: `DYNAMIC_MODULE_EXECUTION_WITHOUT_IMPORT_SYSTEM_REGISTRATION`
- repair: `sys.modules` registration before `exec_module`.
- status: `CLOSED`

## S14-DEF-QA-001 — measurement target identity contamination
- domain: `QA / FIDELITY ORACLE`
- observed run: `33453624321`
- root-cause family: `MEASUREMENT_TARGET_IDENTITY_NOT_ISOLATED`
- counterexample: adjacent alpha-connected geometry inflated a canonical card bbox and generated a false defect.
- rejected repair: weaken thresholds or shrink crop until green.
- architecture repair: target-isolated measurement render with unique semantic colors for cards, headings and annotations, driven by the same canonical tracks as the structural renderer.
- status: `CLOSED / REVERIFIED`

## S14-DEF-MEAS-001 — heading identity swap during crossing
- domain: `SOURCE MEASUREMENT / ENTITY CONTINUITY`
- root-cause family: `TRACK_IDENTITY_SWAP_DURING_CROSSING`
- affected local frames: `52..56`
- repair: preserve v1 and create measured-track v2 using temporal continuity + visible wording; record `S14-MEAS-CORR-001`.
- Drive v1: `19r2Xhl0IYZ6ErgcCFZUrsHbw-08g4FWj`
- Drive v2: `1VFgmwZaJdnDaRRJ8Lz-GiwUUPiKDcPum`
- status: `CLOSED / REVERIFIED`

## S14-DEF-TEST-002 — prose wording used as semantic authority
- domain: `QA / TEST ORACLE`
- observed run: `33454979259`
- root-cause family: `TEST_ASSERTS_DOCUMENTATION_WORDING_INSTEAD_OF_SEMANTIC_AUTHORITY`
- rejected repair: mutate production comment prose to satisfy a brittle string test.
- repair: assert semantic authority surfaces: calibration exists, fallback font is explicit, spec remains `FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN`, contract keeps exact font in `unknowns`.
- status: `CLOSED / REVERIFIED`

## S14-DEF-SRC-001 — stable annotation summary collapsed temporal trajectory
- domain: `SOURCE-BOUND MOTION / ANNOTATION`
- baseline artifact: `9781244633` at head `ebe8eedf210e4c2bd9c0465d38dfbb584d7a0471`
- root-cause family: `STATIC_SUMMARY_COLLAPSED_ANNOTATION_TRAJECTORY`
- baseline failures:
  - audio annotation mean IoU `0.42922`, centroid error `23.82px`
  - visual annotation mean IoU `0.91885`, centroid `4.64px`
  - texto annotation mean IoU `0.90233`, centroid `2.20px`
- repair: measured source screen-space annotation track (`1VYdmrkBHIa3SlytJg36ZDTJua3icx55D`) compiled into `annotationMeasuredTrack.ts`; exact original vector path remains unknown.
- post-repair artifact: `9781474661` at renderer head `1ec6a2e561b2e7f67569242dbd3fbaebc724defa`
- post-repair:
  - audio mean IoU `0.99980`, centroid `0.026px`
  - visual mean IoU `0.99771`, centroid `0.237px`
  - texto mean IoU `0.99675`, centroid `0.230px`
  - timing error all states `0f`
- status: `REPAIRED_VERIFIED`

## S14-DEF-AUDIO-001 — rendered transient peak latency
- domain: `AUDIO / RENDERER ADAPTER`
- baseline artifact: `9781244633`
- source proxy peaks: local `10.05, 14.40, 16.80, 45.75, 50.25, 56.25, 62.85`
- baseline mean absolute error `1.23183f`, max `1.54252f` => FAIL `<=1.5f`
- root-cause family: `RENDERER_TRANSIENT_PEAK_LATENCY`
- repair: preserve canonical source event frames; schedule deterministic structural hit one renderer frame early (`syntheticHitLeadFrames=1`).
- post-repair mean absolute error `0.26837f`, max `0.56973f` => PASS.
- residual unknown: source SFX identity/timbre, stems and exact source envelope.
- status: `REPAIRED_VERIFIED`

## Final source-bound qualification

Renderer-qualified artifact: `9781474661` at `1ec6a2e561b2e7f67569242dbd3fbaebc724defa`.

Visible-state gates:
- card geometry/timing: PASS
- heading geometry/timing: PASS
- annotation geometry/timing: PASS

Audio proxy gate:
- max rendered-transient/source-proxy offset `0.56973f`: PASS

`p0_p1_visible_state_gates_pass = true`
`audio_onset_peak_gate_pass = true`
`full_9d_fidelity_validated = false`

## Exact-head evidence-only reverify

Final branch head `84edb0b223576673e283f326554b298e02604ce7` differs from renderer-qualified head `1ec6a2e...` by exactly three added evidence projections and no executable code/test changes. Remotion Golden S14 run `33456298657` is SUCCESS. Artifact `9781589363` has digest `sha256:ec66de33ae40d143614909ec1390ead248ff8bb0aacc76a4f66eba385d81112b`; its rendered MP4 is byte-identical to the qualified artifact (`sha256:5a3333fdd72e9f9390ce25a44c1439500528ea407cdbd081ccf32e30ceb3894d`) and the target-isolated overlay aggregate is also byte-identical.

Merge Safe run `33456298568` is queued at this checkpoint. Therefore no merge/promotion authority is inferred from it.

## Residual unknowns / blockers
- exact heading font/source glyph outlines
- original AE precomp/parenting/effect graph and Graph Editor curves
- exact annotation vector paths/stroke construction
- isolated original SFX/music/VO stems
- source-specific nested media pixels remain `SOURCE_LOCK`
- full FX/color/depth/camera decomposition
- cross-renderer parity
- structural generalization

Current authority: `SOURCE_BOUND_VISIBLE_AND_ONSET_P0P1_CLOSED / FULL_9D_NOT_VALIDATED / NOT_CANONICAL_TEMPLATE`.
