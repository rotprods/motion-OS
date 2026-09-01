# S14 Defect Graph

Authority: append-only reconstruction/qualification ledger. A defect is not a source-fidelity finding unless explicitly backed by source-bound measurement.

## S14-DEF-CI-001 — truncated GitHub Action revision

- domain: `CI / SUPPLY_CHAIN`
- severity: `P1 execution blocker`
- observed run: `Remotion Golden S14 #33453023535`
- failure stage: runner `Set up job`, before checkout/tests/render
- observed invalid pin: `actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020`
- root-cause family: `INVALID_OR_TRUNCATED_ACTION_PIN`
- consequence: physical renderer authority was `NOT_RUN`; this run is not evidence against S14 implementation correctness.
- first repair attempt: manually appended missing-looking characters to the end of the revision.
- regression introduced: the manually reconstructed revision had 43 characters and did not identify a provider commit.
- status: `SUPERSEDED_BY_S14-DEF-CI-002`

## S14-DEF-CI-002 — manually reconstructed immutable revision

- domain: `CI / SUPPLY_CHAIN / AUTHORITY`
- severity: `P1 execution blocker`
- observed run: `Remotion Golden S14 #33453202698`
- failure stage: runner `Set up job`, before checkout/tests/render
- invalid attempted repair: `actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020eca`
- root-cause family: `MANUALLY_RECONSTRUCTED_ACTION_SHA_WITHOUT_PROVIDER_VALIDATION`
- generalized lesson: a fixed-length hex token is not sufficient proof that an immutable action revision exists. Revision authority must come from a known provider commit, ideally copied from an already successful pinned workflow or verified against the provider repository.
- final repair input: known setup-node v4 commit used by the established pin set: `49933ea5288caeca8642d1e84afbd3f7d6820020`.
- permanent local invariant: every `uses:` revision in the S14 workflow must be exactly 40 lowercase hex characters.
- provider-existence verification: delegated to GitHub Actions resolution on exact-head execution; a green setup phase is required before any renderer/test authority is claimed.
- regression: `test_workflow_action_revisions_are_full_git_shas`.
- status: `PROVIDER_RESOLUTION_VERIFIED / CLOSED`

## S14-DEF-TEST-001 — dynamic-module test harness omitted `sys.modules` registration

- domain: `QA / TEST HARNESS`
- severity: `P1 execution blocker, no product authority`
- observed run: `Remotion Golden S14 #33453466612`
- failure stage: pytest collection, before TypeScript checks or render
- symptom: Python 3.12 `@dataclass` resolution failed because the dynamically loaded qualifier module was executed without first being registered in `sys.modules`.
- root-cause family: `DYNAMIC_MODULE_EXECUTION_WITHOUT_IMPORT_SYSTEM_REGISTRATION`
- consequence: qualifier implementation and renderer remained `NOT_RUN` for this attempt; the error is not evidence that either is wrong.
- repair: register `sys.modules[spec.name] = module` before `exec_module`.
- regression: `test_dynamic_qualifier_module_is_registered_for_dataclass_resolution`.
- status: `REPAIRED / REVERIFIED_BY_LATER_COLLECTION`

## S14-DEF-QA-001 — connected-component target contamination

- domain: `QA / FIDELITY ORACLE`
- severity: `P1 qualification-integrity defect`
- observed run: `Remotion Golden S14 #33453624321`
- failure stage: adversarial fidelity-oracle unit test, before render
- observed counterexample: expected card box `(50,60,101,121)` became `(50,60,111,121)` when adjacent same-alpha geometry touched the target; IoU fell to `0.90991`.
- root-cause family: `MEASUREMENT_TARGET_IDENTITY_NOT_ISOLATED`
- relationship to historical S11 failure: same higher-order family as `MEASUREMENT_ORACLE_CROSS_COMPONENT_CONTAMINATION`; S14 proves overlap/centroid scoring alone cannot recover target identity after connected components have already merged.
- rejected repair: weaken the adversarial threshold or reduce padding until the fixture passes.
- architecture repair: render a dedicated target-isolated QA projection from the same canonical measured tracks, assigning a unique flat RGB identity to every measured card/heading/annotation. The production structural render remains unchanged; only the measurement surface becomes semantically labeled.
- qualifier repair: measure exact target color inside the expected neighborhood instead of any alpha-connected component.
- authority boundary: target-isolated geometry proves renderer execution against measured tracks; it does not prove source-media pixels, exact fonts, annotation path topology or original AE internals.
- status: `REPAIRED_PENDING_LATEST_EXACT_HEAD_REVERIFY`

## S14-DEF-MEAS-001 — heading track identity swap during crossing

- domain: `SOURCE MEASUREMENT / ENTITY CONTINUITY`
- severity: `P1 evidence-integrity defect`
- discovered during: source-bound comparison after target-isolated renderer proof
- affected local frames: `52..56`
- root-cause family: `TRACK_IDENTITY_SWAP_DURING_CROSSING`
- symptom: v1 assigned incoming `texto` heading observations to the outgoing `visual` track after `visual` had already exited left.
- evidence: temporal x-continuity of the incoming heading plus visible source wording; source `texto` progresses from x≈384 → 320 → 276 → 245 → 220 → 200 → 185 → 172 while the outgoing visual heading exits by local 51.
- repair: preserve v1 raw evidence, create measured track v2, version contract to `motion-os.golden-s14-contract/v2`, and record `S14-MEAS-CORR-001`.
- Drive v1: `19r2Xhl0IYZ6ErgcCFZUrsHbw-08g4FWj`.
- Drive v2: `1VFgmwZaJdnDaRRJ8Lz-GiwUUPiKDcPum`.
- status: `REPAIRED_PENDING_LATEST_EXACT_HEAD_REVERIFY`

## S14-DEF-TEST-002 — documentation wording used as semantic authority

- domain: `QA / TEST ORACLE`
- severity: `P1 execution blocker, no renderer authority`
- observed run: `Remotion Golden S14 #33454979259`
- failure stage: pytest contract checks, before TypeScript/render
- symptom: `test_fallback_heading_calibration_never_claims_exact_font_identity` required an exact prose substring from a source-code comment.
- root-cause family: `TEST_ASSERTS_DOCUMENTATION_WORDING_INSTEAD_OF_SEMANTIC_AUTHORITY`
- why invalid: comments may be rephrased without changing the authority contract; forcing production comments to match a test would invert the authority direction.
- rejected repair: modify the renderer comment until the brittle string test passes.
- repair: assert the actual semantic surfaces instead: calibration object exists; renderer uses only a fallback font; `s14Spec.ts` declares `headingFont:'FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN'`; contract retains `exact heading font` in `unknowns`.
- regression: renamed semantic test `test_fallback_heading_calibration_preserves_unknown_font_authority`.
- status: `REPAIRED_PENDING_EXACT_HEAD_REVERIFY`

```text
TRUNCATED_PIN
  -> PREVENTS -> RUNNER_BOOTSTRAP
  -> DOES_NOT_PROVE -> RENDERER_FAILURE
  -> GENERALIZES_TO -> ACTION_REVISION_PROVENANCE_REQUIRED

DYNAMIC_TEST_IMPORT
  -> OMITS -> SYS_MODULES_REGISTRATION
  -> PREVENTS -> TEST_COLLECTION
  -> DOES_NOT_PROVE -> QUALIFIER_OR_RENDERER_FAILURE

CONNECTED_COMPONENT_ORACLE
  -> MERGES -> TARGET + ADJACENT_GEOMETRY
  -> DESTROYS -> TARGET_IDENTITY
  -> CAUSES -> FALSE_FIDELITY_DEFECT
  -> REPAIRED_BY -> UNIQUE_COLOR_TARGET_PROJECTION

TRACK_CROSSING
  -> CONFUSES -> ENTITY_IDENTITY
  -> CORRUPTS -> SOURCE_MEASUREMENT_AUTHORITY
  -> REPAIRED_BY -> TEMPORAL_CONTINUITY_ADJUDICATION
  -> PRESERVES -> V1_HISTORY
  -> PRODUCES -> MEASURED_TRACK_V2

BRITTLE_PROSE_TEST
  -> COUPLES -> COMMENT_WORDING
  -> PREVENTS -> EXECUTION_WITHOUT_SEMANTIC_DEFECT
  -> DOES_NOT_PROVE -> RENDERER_FAILURE
  -> REPAIRED_BY -> SEMANTIC_AUTHORITY_ASSERTION
```

## Source-fidelity defect frontier

Next authoritative step:

`latest exact-head CI -> physical artifact -> qualifier using measured-track-v2 + annotation-track-v1 -> audio-event diff -> defect adjudication`.

Unknowns remain explicit: exact fonts, original AE hierarchy/Graph Editor curves, exact annotation vector paths/strokes, isolated original SFX stems, hidden media mattes, full FX/color/depth/camera decomposition.
