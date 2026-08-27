# Phase 06 — Execution & Resilience Superwave

Status: IMPLEMENTED_IN_BRANCH / VERIFICATION_PENDING
Date: 2026-08-26

## Goal
Make `/heygen` safe to run repeatedly and concurrently without duplicate paid renders, silent state corruption, replica drift, unverifiable downstream manifests, or schema lock-in.

## Scope
1. Persistent append-only render-intent ledger.
2. Hash-chained event integrity and duplicate submission detection.
3. Explicit schema versioning and migration registry.
4. Deterministic manifest sealing + replay fingerprint.
5. Persistence replica reconciliation for GitHub/Drive/Library.
6. Provider failure simulation, especially timeout-after-acceptance.
7. CLI integration for migrate → preflight → seal → authorize → ledger.
8. Resilience tests.

## Invariants
- Never submit the same render intent twice without reconciliation.
- Ambiguous provider acceptance is RECONCILE_REQUIRED, not retryable by default.
- A sealed manifest must fail verification after any protected downstream mutation.
- A future schema version must fail closed.
- Replica conflicts never auto-overwrite the canonical source.
- GitHub remains software/control truth; Drive/Library are recoverability replicas.
- Paid execution requires explicit authorization independently from content preflight.

## New modules
- `src/avatar/render_ledger.py`
- `src/avatar/fault_simulation.py`
- `src/content/integrity.py`
- `src/content/schema_migrations.py`
- `src/content/replica_reconciliation.py`
- `tests/test_phase06_execution_resilience.py`

## CLI flow
`/heygen` implementation path now supports:

SOURCE/MANIFEST
→ optional schema migration
→ content preflight
→ integrity seal
→ replay fingerprint
→ explicit render authorization
→ budget/concurrency gate
→ deterministic render intent
→ append to execution ledger
→ provider request compilation
→ provider submit outside this CLI
→ reconcile telemetry before retry

## Failure matrix
- timeout before provider acceptance → bounded retry may be allowed
- timeout after acceptance → reconcile required
- provider 5xx with ambiguous acceptance → reconcile required
- malformed response → reconcile required
- completed without asset → reconcile required
- duplicate callback → idempotent no-op for terminal state

## Verification gates
R1. Unit tests pass in authoritative CI/runtime.
R2. Two concurrent processes cannot append conflicting ledger events silently.
R3. Hash-chain tampering is detected.
R4. Duplicate render authorization is blocked when equivalent intent exists.
R5. Timeout-after-acceptance simulation never emits blind retry.
R6. V1 manifest migrates deterministically to current schema.
R7. Future schema fails closed.
R8. Sealed downstream manifest detects mutation.
R9. Replica conflict produces manual reconciliation requirement.
R10. Full `/heygen` dry-run emits replay fingerprint + render intent without spending credits.

## Remaining gaps after this wave
- replace local lockfile ledger with transactional shared storage for multi-host deployments
- stale-lock recovery/lease semantics
- provider-side idempotency key if HeyGen exposes one
- actual provider timeout fault injection against a non-billing sandbox
- schema migration fixtures for every historical production manifest
- persistent replica revision metadata and automated drift report job
- downstream engine verification of replay fingerprint before editing
- CI authority and fuzz/property testing
