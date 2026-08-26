# Phase 06 — Runtime Authority + Downstream Enforcement + Production Calibration Superwave

Status: EXECUTING
Date: 2026-08-26
Branch: `feat/avatar-script-engine`
PR: #37
Storage decision: `architecture/ADR_006_STORAGE_AND_DATABASE_TRIGGERS.md`

## Mission
Qualify Phase 06 for real content production while preserving the Phase 05 Studio Engine ownership boundary and refusing infrastructure that does not remove a measured bottleneck.

## North Star
A content/avatar job is reproducible, spend-safe, provenance-bound and accepted downstream only when its semantic identity is valid. Production observations improve calibration without silently becoming causal rules. Network-distributed authority is activated only when actual deployment requires more than one independent authority host.

## Wave A — Authority without premature infrastructure
1. Keep `RenderStateStore` as the abstraction boundary.
2. Keep SQLite WAL as `TRANSACTIONAL_SINGLE_HOST_AUTHORITY` for current operation.
3. Preserve durable monotonically increasing fencing generations across release/expiry/reacquire.
4. Enforce deterministic render intent identity and provider-job reconciliation.
5. Add/retain shared authority contract tests so a future network adapter must satisfy identical invariants.
6. **DEFER Postgres/network authority until an ADR-006 trigger fires**: >1 independent worker host, remote scheduled workers, multi-user/workspace SaaS, measured SQLite contention, or HA/failover requirement.
7. Do not store heavy media bytes in Postgres. When remote/shared delivery is required, use content-addressed object storage and optional CDN; DB stores metadata, hashes, object keys, provenance and state.

## Wave B — Single-host crash/reconciliation quality
1. Add bounded worker heartbeat only where a long-running local worker actually needs lease renewal.
2. Simulate worker death during provider submission, polling and post-acceptance ambiguity.
3. On recovery, reconcile provider state before retrying any paid operation.
4. Prove stale worker writes remain rejected after lease turnover.
5. Persist recovery events and reason codes.
6. Multi-host partition/heartbeat tests become active only when network authority is activated.

## Wave C — Downstream PRV/MNF enforcement
1. Fail closed at the Phase06→Studio Engine boundary.
2. Require `PRV_*` provenance root, `MNF_*` replay fingerprint and stable semantic beat IDs.
3. Recompute/verify canonical integrity before graph/timeline execution.
4. Reject semantic mutation, missing provenance, duplicate/reordered/mutated beat IDs and mismatched avatar/script identity.
5. Keep renderer/motion ownership downstream; Phase 06 supplies verified semantic authority only.
6. Maintain adversarial mutation tests.

## Wave D — Production calibration harness
1. Append-only production observations with unique `production_id`.
2. Capture topic family, primary/secondary driver, ICP, hook/angle IDs, predicted/actual duration, clarity, hook, CTA, pronunciation errors **and pronunciation-check denominator**, claim violations and downstream outcome IDs.
3. Require evidence class: OBSERVATIONAL / CONTROLLED_TEST / REPLICATED_TEST / APPROVED_RULE.
4. Never promote correlations automatically.
5. Aggregate >=30 real productions, >=5 topic families and all four primary drivers.
6. Compute normalized duration error and true pronunciation error rate.

## Wave E — Replica and asset authority
1. Generate deterministic descriptors for GitHub, Drive and ChatGPT Library control/recovery artifacts.
2. Compare revision/hash without destructive overwrite.
3. Classify MATCH / STALE_REPLICA / DIVERGED / MISSING.
4. Emit actionable drift reports.
5. GitHub remains software/control truth; Drive/Library remain recovery/operational replicas.
6. Add object storage/CDN only when ADR-006 asset triggers fire; do not make CDN a prerequisite for local content generation.

## Wave F — Gauntlet
Always active:
- lease expires during provider call;
- stale worker resumes after lease turnover;
- timeout after provider acceptance;
- duplicate provider job ID;
- future schema version;
- PRV mutation with valid-looking MNF;
- MNF mutation with valid-looking PRV;
- beat deletion/reorder/duplicate;
- calibration duplicate IDs / observation poisoning;
- replica divergence;
- malformed/oversized/unknown provider telemetry.

Activated only with network authority:
- two independent hosts race for the same intent;
- network partition around heartbeat;
- failover across authority hosts.

## Qualification gates
### AUTH1 — Current authority
PASS when SQLite transactional authority + fencing + reconcile-before-retry + spend safety are CI-proven for the actual single-host deployment.

### AUTH2 — Network authority
`DEFERRED_BY_DESIGN` until ADR-006 trigger. When activated, PASS requires transactional network implementation and independent-host proof. It is not a blocker before the trigger exists.

### DS1 — Downstream fail-closed integrity
PASS only when Studio Engine entry rejects invalid PRV/MNF/beat identity before timeline execution.

### CAL1 — Harness correctness
PASS when observations are append-only, unique-ID, evidence-classified, pronunciation denominator-aware and cannot auto-promote causal rules.

### CAL2 — Empirical qualification
PASS only after >=30 real productions, >=5 topic families, all 4 primary drivers, normalized duration error <=7%, clarity >=9, hook >=9, CTA >=8.5, claim violations=0 and pronunciation error rate <=1%.

### REP1 — Replica drift
PASS when GitHub/Drive/Library descriptors can be compared and divergence is surfaced without destructive overwrite.

## Non-negotiable boundaries
- Green CI is necessary but not sufficient for product qualification.
- Do not introduce Postgres, queues, Kubernetes, external graph DBs or CDN unless a measured/required trigger exists.
- Do not claim multi-host authority from SQLite.
- Do not retry a paid provider call after ambiguous acceptance without reconciliation.
- Do not allow downstream motion/render execution before PRV/MNF verification.
- Do not turn performance correlation into a canonical content rule automatically.
- Do not overwrite concurrent Phase 05 Studio Engine work.

## Current baseline
- SQLite transactional authority + durable fencing generations: CI-proven.
- Latest reviewed Phase06 head before current review fixes: CI, Repo Health, Security Baseline and Runtime Smoke PASS.
- `RenderStateStore` preserves a clean future migration seam.
- Real calibrated HeyGen evidence: OpenMontage 42.6318s inside 30–45s target.
- Postgres: `DEFERRED_BY_DESIGN` under ADR-006.

## Exit condition
Exit current superwave when all non-empirical gates needed by the actual single-host production topology have implementation, adversarial tests and authoritative CI evidence. CAL2 remains open only for real-production evidence. AUTH2 remains deferred until its deployment trigger becomes real.