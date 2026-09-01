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
  - PR #125 contains 16 durable commits rooted at PR #64 base `2e26e311e506b6aaaa32f827e1579ddaa1e3ea58`.
- provider resolution: `65e18050` is not resolvable as a repository commit and is not present in the current PR #125 commit genealogy.
- durable Drive authority at reconciliation:
  - `GOLDEN_S16/00_SOURCE` contains source evidence.
  - `GOLDEN_S16/01_CONTRACT` contains measured source contracts.
  - `GOLDEN_S16/02_STRUCTURAL_RENDER` is empty.
  - `GOLDEN_S16/03_FIDELITY` is empty.
- Event Bus authority: Issue #39 contains the S16 `WORK_STARTED` event but no later durable S16 render/qualification checkpoint proving the stale claim.
- PR conversation authority: PR #125 contains no comments recording such an artifact or qualification.

### Root-cause family

`CONVERSATIONAL_EXECUTION_CLAIM_WITHOUT_DURABLE_PROVIDER_EVIDENCE`

### Consequence

The prior `65e18050...` claim is **invalid evidence**. It must not grant:

- `STRUCTURAL_RENDER_EXECUTED`
- source-bound visible fidelity
- audio-sync qualification
- `CANONICAL_TEMPLATE`
- merge or promotion authority

Current maximum S16 authority after reconciliation is:

`SOURCE_CONTRACT_FROZEN + RENDERER_IMPLEMENTED_UNVERIFIED`

### Repair

1. Treat `628b3dcf...` lineage as the only durable pre-reconciliation implementation authority.
2. Persist this defect before making further renderer changes.
3. Trigger a fresh exact-head S16 workflow from a new durable commit.
4. Require the workflow to execute tests, TypeScript, composition enumeration, physical render, target-isolated overlay and mechanical verifier.
5. Download the resulting artifact for the exact head.
6. Run source-bound geometry/depth/retention/audio qualification against the frozen Drive source contracts.
7. Persist any mismatch as a new DefectGraph node before changing renderer or thresholds.

### Permanent invariant

`NO_EXECUTION_OR_FIDELITY_AUTHORITY_FROM_CHAT_STATE_ALONE`

Any claim of a physical render or qualification must identify a provider-resolvable commit/run/artifact and/or a durable Drive evidence object.

### Status

`OPEN_PENDING_EXACT_HEAD_PHYSICAL_REVALIDATION`

```text
CHAT_CLAIM
  -> REFERENCES -> NON_RESOLVABLE_HEAD
  -> LACKS -> DURABLE_RUN_ARTIFACT
  -> LACKS -> DRIVE_RENDER_EVIDENCE
  -> CANNOT_GRANT -> EXECUTION_AUTHORITY
  -> REPAIRED_BY -> EXACT_HEAD_REVALIDATION
  -> GENERALIZES_TO -> NO_CHAT_ONLY_EXECUTION_AUTHORITY
```

## Source-fidelity frontier

The source contract remains authoritative for the measured claims already frozen in `s16_contract.json`. The renderer is not yet qualified against it.

Next authoritative step:

`fresh exact-head CI -> physical artifact -> source-bound geometry/depth/hold/audio diff -> defect adjudication`.

Unknowns remain explicit: exact original column asset, exact question-mark asset, exact `Factor X` font/source metrics, original AE/precomp/Graph Editor/effect graph, exact opacity curves, isolated stems/SFX identities, and unique original COLUMN-vs-QUESTION z-order.
