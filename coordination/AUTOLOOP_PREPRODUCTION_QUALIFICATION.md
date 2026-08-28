# MOTION.OS Autoloop — Pre-Production Qualification

State: `QUALIFICATION_PENDING_COMBINED_HEAD`

## Stack under test

```text
main
  ↓
PR #58 — canonical Event Fabric v3 / session / truth / irreversible preflight
  ↓
PR #68 — self-driving selection / gauntlet / continuation metaprogram
```

The hourly external clock MUST remain disabled until this stacked merge candidate is clean-runner qualified and the #39/#48 cognitive-pause barrier permits promotion/activation.

## Required invariants

1. GitHub live lifecycle overrides stale projections.
2. `main_sha` freshness is mandatory.
3. Event Fabric live/context watermark equality is mandatory.
4. Context projection SHA256 and Event Fabric snapshot SHA256 bind every executable next-wave packet.
5. #68 refuses EXECUTE without `motion-os.event-fabric/v3` readiness.
6. Active WRITE/EXCLUSIVE_WRITE conflicts fail closed; semantic scopes are first-class.
7. Inputs are bounded and typed; string booleans, NaN/inf, traversal, duplicate IDs/claims and unsafe branch values fail closed.
8. Candidate/title/test/evidence text is `UNTRUSTED_DATA`, not control-plane instruction text.
9. `/gauntlet-loop` uses independent verification, a maximum of three materially distinct repair attempts, stuck-loop detection and a kill switch.
10. `NEXT_ITERATION_METAPROMPT` is SHA256 sealed and must be verified before use.
11. A continuation packet is an acceleration hint only; any main/watermark/claim/PR/projection drift invalidates it.
12. No irreversible action or autonomous merge may bypass #39/#48 barriers or canonical irreversible preflight.
13. Skipped/cancelled checks are not evidence.
14. The external clock only wakes the agent; it never grants authority.

## Qualification history

Standalone #68 final pre-stack head `dc4d68454bb492c3ce9b638e54401aa9a44184f7`:
- Coordination Contracts #97: SUCCESS
- MERGE_SAFE #225: SUCCESS
- local-contract Python 3.12: SUCCESS
- immutable agent-event validation: SUCCESS
- immediately preceding code-head quick suite: `358 passed, 1 skipped`, repo-health PASS

The previous failure in MERGE_SAFE #217 was an expected regression-test mismatch after converting metaprompt fields from raw strings to JSON-marked untrusted data; production code was not weakened to satisfy the stale test. The assertions were updated to the hardened contract and subsequent exact-head gates passed.

## Activation gate

Do not set this system to operational unless all are true at the same reconstructed state:

- PR #58/event fabric v3 has promotion authority or is present in the exact combined candidate under test;
- PR #68 exact combined head is green;
- no unresolved P0/P1 code/security review finding;
- Issue #48 and #39 barrier state permits the requested action;
- latest live main SHA and Event Fabric watermark are re-read immediately before promotion/activation;
- after serial promotion, `main` is verified and canonical events are emitted;
- only then enable the hourly `MOTION OS Autoloop` clock.

Any material drift resets qualification.
