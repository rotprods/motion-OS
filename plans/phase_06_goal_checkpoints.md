# Phase 06 — Define Goal + Checkpoints

## Goal
Build a production-grade upstream **Content Intelligence + Avatar Factory** that converts a raw idea/source into a validated 30–45s avatar-video package with predictable duration, simple language, strong retention architecture, correct TTS pronunciation, configurable avatar/voice routing, provenance, spend safety, idempotency, provider-state integrity and a graph-ready semantic handoff for downstream MOTION.OS editing.

## North-star acceptance
A new agent can take a raw idea and produce, without conversational context:
1. an isolated SourcePack marked `UNTRUSTED_SOURCE_DATA`,
2. explicit claim lineage and freshness,
3. an explicit ICP and primary viral driver,
4. one core transformation,
5. scored angle/hook sets,
6. semantic beats with stable IDs,
7. display/spoken/TTS scripts with protected-token integrity,
8. CTA + moral/payoff,
9. duration inside 30–45s,
10. explicit spend-authorized idempotent avatar render intent,
11. validated provider telemetry,
12. a sealed provenance-chained replayable handoff,
13. reconcilable persistence replicas,
14. transactional single-host worker authority with stale-writer rejection,
15. performance observations that cannot become causal rules without evidence,
16. a fail-closed Studio execution boundary that rejects semantic/provenance drift before any executor can run.

## Hard boundaries
Phase 06 owns content intelligence, narration, voice/avatar generation and upstream semantic metadata. It does not own motion graphics, overlays, B-roll placement, visual grammar, timeline compositing, grade or final export. Storage/topology must remain proportional to measured requirements: Postgres, queues, object storage and CDN are deferred until real deployment triggers exist.

## Checkpoint state
- CP0 persistence isolation: **PASS**
- CP1 schema contracts/migrations: **PASS**
- CP2 source trust boundary: **PASS_V1**
- CP3 claim lineage: **PASS_V1**
- CP4 strategy contracts: **PASS**
- CP5 attention/cognitive QA: **PASS_V1**
- CP6 duration calibration engine: **PASS_V1**, corpus scale open
- CP7 TTS semantic integrity: **PASS_V1**
- CP8 configurable production profile: **PASS**
- CP9 spend authorization/idempotency: **PASS**
- CP10 provider request/telemetry integrity: **PASS**
- CP11 downstream graph handoff integrity: **PASS_V4 / CI-PENDING ON LATEST HEAD** — stable beat IDs + PRV + MNF + fail-closed execution gateway. `provenance_chain` is now included in the default sealed projection, so PRV cannot remain mutable metadata beside an otherwise valid MNF. Legacy/custom seals that omit provenance are rejected at the Studio boundary.
- CP12 performance causal hygiene: **PASS_V1**
- CP13 schema/persistence resilience: **PASS_V2 / CI-PENDING ON LATEST HEAD** — deterministic replica digests plus read-only operational drift reporter. `MATCH`, `STALE_REPLICA`, `MISSING`, `CONFLICT` are advisory states only; automatic writes are forbidden and refresh requires explicit authorization.
- CP14 test/fuzz gate: **REVALIDATING LATEST HEAD**
- CP15 empirical calibration: **OPEN** — requires >=30 unique real productions across >=5 topic families before empirical promotion.
- CP16 worker authority/fencing: **PASS_V1_SINGLE_HOST** — SQLite/WAL transactional authority with durable fencing generations. No multi-host/distributed authority claim.
- CP17 end-to-end provenance: **PASS_V2 / CI-PENDING ON LATEST HEAD** — Phase06→Studio execution authorization derives expected PRV/MNF/beat identity from the sealed manifest itself; callers cannot supply their own expected IDs.

## DS1 — Canonical Studio Execution Boundary
Implementation:
- `src/content/studio_execution_gateway.py`
- `scripts/studio_execute.py`
- `tests/test_phase06_studio_execution_gateway.py`

Contract:
`sealed manifest → verify MNF seal → require provenance_chain covered by seal → derive PRV/MNF/beat IDs → verify handoff content/PRV/MNF/beats/render identity → executor reachable only on PASS`.

The authorization CLI intentionally reports `execution_started: false`: authorization and execution remain separate authority transitions. The reusable `execute_verified_studio_handoff()` wrapper proves the executor callback is unreachable on failed authority.

## Replica drift operational boundary
Implementation:
- `scripts/replica_drift_report.py`
- `src/content/replica_reconciliation.py`

This layer computes deterministic revision/hash drift reports only. It performs no connector writes. Stale or missing replicas are refresh candidates, not permissions. Conflicts are fail-closed.

## Qualification rule
The non-empirical merge candidate may only advance when CI, Repo Health, Security Baseline, Runtime Smoke and Remotion Runtime all pass on the exact latest head and final diff-level code/security review finds no P0/P1 issue. CP15 remains separately empirical: code promotion must not be misrepresented as performance calibration.

Any P0 violation in source isolation, claim lineage, spend safety, TTS protected-token integrity, manifest/provenance integrity, provider-state reconciliation or Studio execution authority blocks promotion regardless of aggregate score.
