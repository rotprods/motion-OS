# Phase 06 — Adversarial Hardening Gauntlet

Status: IN PROGRESS
Owner: upstream content/avatar lane
Goal: make `/heygen` difficult to break before production promotion.

## Wave 1 — Source trust + factual integrity
- classify all external source content as `UNTRUSTED_SOURCE_DATA`
- scan for instruction-like prompt injection
- redact obvious secrets/PII before persistence
- normalize claims to deterministic IDs
- enforce factual beat → claim lineage
- block `UNSUPPORTED` claims from factual delivery

Exit: malicious source cannot directly change privileged behavior and factual beats cannot be provenance-free.

## Wave 2 — Spend safety + idempotency
- deterministic render intent fingerprint
- explicit spend authorization
- per-render/day/concurrency limits
- bounded retry state machine
- reconcile-before-retry when provider acceptance is ambiguous
- no blind resubmit when provider job exists

Exit: a timeout cannot trivially duplicate a paid render.

## Wave 3 — Speech integrity + cognitive QA
- protected tokens for years, decimals, percentages, currencies, URLs and versions
- semantic TTS equivalence errors block render
- attention refresh replaces simplistic `new information every 3s` invariant
- sustained high cognitive load emits QA warning

Exit: TTS cannot silently change critical numbers and cadence optimization does not mandate information spam.

## Wave 4 — Provider boundary + state integrity
- provider payload allowlists
- telemetry status validation
- URL scheme validation
- duration plausibility validation
- malformed job IDs rejected

Exit: malformed provider state cannot silently poison canonical manifests.

## Wave 5 — Learning causal hygiene
- explicit evidence stages: OBSERVED_CORRELATION → CANDIDATE_HYPOTHESIS → REPEATED_PATTERN → CONTROLLED_TEST → PROMOTED_RULE
- capture timing/topic heat/distribution confounders
- no automatic promotion to canonical rule
- explicit approval required after controlled test

Exit: one viral post cannot rewrite the content policy.

## Wave 6 — Schema + persistence resilience
Open work:
- schema version field on all Phase 06 records
- migrations and compatibility matrix
- GitHub/Drive/Library replica version checks
- content fingerprint and authority metadata in replicas
- deterministic downstream beat-manifest integrity hash

## Wave 7 — Execution + recovery
Open work:
- authoritative CI
- fuzz malformed manifests/source packs/provider payloads
- simulated provider timeout after acceptance
- concurrent identical render intents
- partial persistence failure/recovery
- replay an existing render from manifest and verify reproducibility

## Wave 8 — Empirical calibration
Open work:
- >=30 real productions
- >=5 topic families
- all four viral drivers represented
- duration MAE <=7%
- clarity >=9/10
- hook >=9/10
- CTA >=8.5/10
- claim violations = 0
- pronunciation error <=1%

## Adversarial questions
1. Can a README tell the system to ignore policy?
2. Can an unsupported claim become spoken fact?
3. Can stale numerical evidence remain confidently phrased?
4. Can timeout-after-acceptance spend twice?
5. Can concurrent agents submit identical work twice?
6. Can TTS turn 2029 into 2019?
7. Can a URL or secret from a source leak to a script/log?
8. Can a malformed provider URL become an asset ref?
9. Can an unknown provider state be mistaken for completed?
10. Can a single viral topic promote a bad hook rule?
11. Can distribution/time-of-day confound performance attribution?
12. Can downstream mutate beat IDs after render authorization?
13. Can a schema upgrade silently invalidate old manifests?
14. Can Drive/Library override newer GitHub policy?
15. Can the system decide ABSTAIN/QUARANTINE instead of forcing output?
16. Can a script pass deterministic checks and still be boring?
17. Can the 3-second rule make a video harder to understand?
18. Can a provider deprecate the avatar/voice without a capability failure?
19. Can an operator know exactly why a render was blocked?
20. Can an exact production be reconstructed from its manifest and intent hash?

## Gate language
Every gate must eventually produce one of:
- PASS
- WARN
- FAIL
- ABSTAIN
- QUARANTINE

and attach machine-readable evidence.

## Current implementation delta
Implemented in this hardening wave:
- threat model
- source risk scanner/redaction
- deterministic claim IDs + lineage validator
- TTS protected-token gate
- attention refresh + cognitive-load QA
- render spend/idempotency state primitives
- provider telemetry validation
- causal-hygiene learning stages
- adversarial tests

Do not mark VERIFIED until authoritative test/CI evidence exists.
