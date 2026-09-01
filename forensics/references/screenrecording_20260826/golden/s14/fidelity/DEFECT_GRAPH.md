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
- repair: restore the full immutable setup-node revision and require every `uses:` revision in the dedicated workflow to match `[0-9a-f]{40}`.
- regression: `test_workflow_action_revisions_are_full_git_shas`
- status: `REPAIRED_PENDING_EXACT_HEAD_REVERIFY`

```text
TRUNCATED_PIN
  -> PREVENTS -> RUNNER_BOOTSTRAP
  -> CAUSES -> WORKFLOW_FAILURE
  -> DOES_NOT_PROVE -> RENDERER_FAILURE
  -> REPAIRED_BY -> FULL_ACTION_SHA
  -> GENERALIZED_TO -> ACTION_PIN_LENGTH_INVARIANT
  -> TESTED_BY -> test_workflow_action_revisions_are_full_git_shas
```

## Source-fidelity defect frontier

No source-fidelity defect is yet promoted here. The next authoritative step is:

`exact-head structural render -> artifact -> source-bound carousel/heading/annotation/audio diff -> defect adjudication`.

Unknowns remain explicit: exact fonts, original AE hierarchy/Graph Editor curves, exact annotation paths, isolated original SFX stems, hidden media mattes.
