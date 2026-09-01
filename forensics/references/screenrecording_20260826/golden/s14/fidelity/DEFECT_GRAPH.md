# S14 Defect Graph

Authority: append-only reconstruction/qualification ledger. A defect is not a source-fidelity finding unless explicitly backed by source-bound measurement.

## S14-DEF-CI-001 — truncated GitHub Action revision

- domain: `CI / SUPPLY_CHAIN`
- severity: `P1 execution blocker`
- observed run: `Remotion Golden S14 #33453023535`
- failure stage: runner `Set up job`, before checkout/tests/render
- observed invalid pin: `actions/setup-node@49933ea5288ca8642d1e84afbd3f7d6820020`
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
- invalid attempted repair: `actions/setup-node@49933ea5288ca8642d1e84afbd3f7d6820020eca`
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
- status: `REPAIRED_PENDING_EXACT_HEAD_REVERIFY`

```text
TRUNCATED_PIN
  -> PREVENTS -> RUNNER_BOOTSTRAP
  -> CAUSES -> WORKFLOW_FAILURE
  -> DOES_NOT_PROVE -> RENDERER_FAILURE
  -> BAD_REPAIR -> MANUALLY_GUESSED_SHA
  -> CAUSES -> SECOND_SETUP_FAILURE
  -> GENERALIZES_TO -> ACTION_REVISION_PROVENANCE_REQUIRED
  -> REPAIRED_BY -> KNOWN_PROVIDER_COMMIT
  -> TESTED_BY -> SHA_SHAPE_REGRESSION
  -> VERIFIED_BY -> GITHUB_ACTION_RESOLUTION_ON_EXACT_HEAD

DYNAMIC_TEST_IMPORT
  -> OMITS -> SYS_MODULES_REGISTRATION
  -> BREAKS -> DATACLASS_TYPE_RESOLUTION
  -> PREVENTS -> TEST_COLLECTION
  -> DOES_NOT_PROVE -> QUALIFIER_OR_RENDERER_FAILURE
  -> REPAIRED_BY -> IMPORT_SYSTEM_REGISTRATION
  -> TESTED_BY -> TEST_HARNESS_REGRESSION
```

## Source-fidelity defect frontier

No source-fidelity defect is yet promoted here. The next authoritative step is:

`exact-head structural render -> artifact -> source-bound carousel/heading/annotation/audio diff -> defect adjudication`.

Unknowns remain explicit: exact fonts, original AE hierarchy/Graph Editor curves, exact annotation paths, isolated original SFX stems, hidden media mattes.
