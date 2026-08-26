# Phase 06 — Distributed Authority & Verification Superwave

## Objective
Close the authority gap between a resilient single-agent prototype and a production-capable content/avatar execution system that can safely coordinate concurrent workers, preserve deterministic provenance and provide CI-verifiable failure behavior.

## Implemented in this superwave
1. `RenderStateStore` protocol as the storage contract for render authority.
2. `SQLiteTransactionalRenderStore` with `BEGIN IMMEDIATE`, WAL mode, explicit leases and monotonically increasing fencing tokens.
3. Stale writer rejection after lease turnover.
4. Transactional intent snapshots + append-only event rows.
5. Source → claims → semantic beats → script → avatar provenance root.
6. Downstream handoff requires both manifest seal/replay fingerprint and provenance root.
7. `/heygen` CLI can attach a SourcePack, verify provenance, seal the manifest and persist render authorization into a transactional authority DB.
8. Deterministic malformed-input fuzz harness for manifests and provider telemetry.
9. Fencing/provenance/fuzz test suites.
10. CI failure root cause identified from authoritative GitHub Actions logs and stale fixture assumption corrected.

## Authority semantics
A worker may mutate a render intent only while holding a live lease for that exact `render_intent_id`. Every successful lease acquisition increments a fencing token. A stale worker with an older token cannot write after lease ownership turns over.

### Current implementation boundary
SQLite provides transactional single-host / shared-process authority. It is not claimed as a safe independent-multi-host database over arbitrary network filesystems. The `RenderStateStore` protocol is the stable seam for Postgres or another transactional multi-host implementation.

## Provenance chain
The deterministic provenance root commits to:

`SourcePack identity → normalized claims → semantic beats/claim links → display+TTS script → avatar profile`

Downstream receives:
- `content_id`
- `replay_fingerprint`
- `provenance_root`
- immutable semantic beat IDs
- provider job ID when available

Any semantic mutation after provenance construction invalidates verification.

## Fuzz strategy
The V1 deterministic fuzz harness covers:
- required-field deletion
- wrong scalar/container types
- oversized scripts
- unknown viral-driver enums
- null CTA
- duplicate beat IDs
- unsupported future schemas
- unknown provider statuses
- negative/non-numeric durations
- unsafe provider URL schemes/types
- malformed provider job IDs

The harness treats explicit validation exceptions as controlled rejection and reports unclassified crashes.

## CI evidence
An authoritative CI run on PR #37 was discovered after prior polling incorrectly returned no commit-scoped runs. The run executed 108 tests and failed exactly one stale assertion: the real OpenMontage fixture now correctly contains actual duration `42.6318`, while the old test incorrectly asserted the original fixture duration must be `None`. The test was corrected to verify non-destructive behavior by snapshotting the original value instead of assuming a fixture state.

This is evidence of a real test gate, not proof that the latest head is green. Promotion remains blocked until a fresh CI run validates the latest head.

## Remaining blockers
- green CI on the latest head
- Postgres/real multi-host `RenderStateStore` adapter before claiming multi-host authority
- lease heartbeat/worker crash integration with live provider polling
- safe non-billing provider fault-injection environment
- automated replica drift job for Drive/Library
- downstream runtime enforcement of `provenance_root` + `replay_fingerprint`
- larger property/fuzz corpus and actual multiprocess stress benchmark
- empirical 30-production calibration

## Promotion rule
Do not call this distributed multi-host authority until a transactional network database adapter and concurrent-host test evidence exist. SQLite V1 is `TRANSACTIONAL_SINGLE_HOST_AUTHORITY` only.
