# Phase 06 — Multi-Host Runtime + Downstream Enforcement + Production Calibration Superwave

Status: EXECUTING
Date: 2026-08-26
Branch: `feat/avatar-script-engine`
PR: #37

## Mission
Advance Phase 06 from CI-proven single-host authority to a production-qualifiable distributed content/avatar runtime while preserving the Phase 05 Studio Engine ownership boundary.

## North Star
A render/content job may be created by one host, leased/reconciled by another, and consumed by the downstream Studio Engine only when its provenance and replay identity are valid. Production observations feed a calibration corpus without silently becoming causal rules.

## Wave A — Network transactional authority
1. Add a Postgres-class `RenderStateStore` implementation behind the existing protocol.
2. Preserve durable monotonically increasing fencing generations across release/expiry/reacquire.
3. Use database time/transactions for lease authority; never trust worker wall clocks for ownership decisions where avoidable.
4. Enforce unique render intent identity and provider-job reconciliation.
5. Add adapter contract tests shared with SQLite.
6. Add multi-connection/concurrent-host simulation and stale-writer tests.
7. Keep SQLite explicitly `TRANSACTIONAL_SINGLE_HOST_AUTHORITY`; never silently promote it to distributed authority.

## Wave B — Heartbeat + crash recovery
1. Add worker lease heartbeat abstraction.
2. Bound renew cadence relative to TTL.
3. Simulate worker death during provider submission, provider polling and post-acceptance ambiguity.
4. On takeover, reconcile provider state before retrying any paid operation.
5. Prove stale worker writes remain rejected after takeover.
6. Persist recovery events and reason codes.

## Wave C — Downstream PRV/MNF enforcement
1. Add a fail-closed handoff verifier at the Phase06→Studio Engine boundary.
2. Require `PRV_*` provenance root, `MNF_*` replay fingerprint and stable semantic beat IDs.
3. Recompute/verify canonical integrity before graph/timeline execution.
4. Reject semantic mutation, missing provenance, duplicate/mutated beat IDs and mismatched avatar/script identity.
5. Keep renderer/motion ownership downstream; Phase 06 supplies only verified semantic authority.
6. Add adversarial mutation tests.

## Wave D — Production calibration harness
1. Define an append-only production observation schema.
2. Capture topic family, primary/secondary viral driver, ICP, hook/angle IDs, predicted duration, actual duration, clarity, hook score, CTA score, pronunciation errors, claim violations and downstream outcome IDs.
3. Require evidence class on every observation: OBSERVATIONAL / CONTROLLED_TEST / REPLICATED_TEST / APPROVED_RULE.
4. No automatic rule promotion from correlations.
5. Build corpus aggregation for >=30 real productions, >=5 topic families and all four primary drivers.
6. Compute normalized duration error and qualification gates.

## Wave E — Replica drift authority
1. Generate deterministic replica descriptors for GitHub, Drive and ChatGPT Library artifacts.
2. Compare revision/hash without destructive auto-overwrite.
3. Classify MATCH / STALE_REPLICA / DIVERGED / MISSING.
4. Emit actionable drift reports.
5. GitHub remains software/control truth; Drive/Library remain recovery/operational replicas.

## Wave F — Gauntlet
Adversarial scenarios must include:
- two hosts acquire same intent concurrently;
- lease expires during long provider call;
- stale host resumes after takeover;
- timeout after provider acceptance;
- duplicate provider job ID;
- network partition around heartbeat;
- future schema version;
- PRV mutation with valid-looking MNF;
- MNF mutation with valid-looking PRV;
- beat deletion/reorder/duplicate;
- calibration observation poisoning;
- replica divergence;
- provider telemetry malformed/oversized/unknown state.

## Qualification gates
### MH1 — Distributed store contract
PASS only with transactional network DB implementation + contract tests.

### MH2 — Concurrent-host proof
PASS only when independent connections/process-equivalent workers demonstrate single authority and monotonic fencing.

### MH3 — Crash recovery
PASS only when takeover reconciles before retry and stale writer remains fenced.

### DS1 — Downstream fail-closed integrity
PASS only when Studio Engine entry rejects invalid PRV/MNF/beat identity before timeline execution.

### CAL1 — Harness correctness
PASS when observations are append-only, evidence-classified and aggregation cannot promote causal rules automatically.

### CAL2 — Empirical qualification
PASS only after >=30 real productions, >=5 topic families, all 4 primary drivers, normalized duration error <=7%, clarity >=9, hook >=9, CTA >=8.5, claim violations=0, pronunciation error <=1%.

### REP1 — Replica drift
PASS when GitHub/Drive/Library descriptors can be compared and divergence is surfaced without destructive overwrite.

## Non-negotiable boundaries
- Do not merge PR #37 merely because CI is green.
- Do not claim multi-host authority from SQLite.
- Do not retry a paid provider call after ambiguous acceptance without reconciliation.
- Do not allow downstream motion/render execution before PRV/MNF verification.
- Do not turn performance correlation into a canonical content rule automatically.
- Do not overwrite concurrent Phase 05 Studio Engine work.

## Current baseline
- Single-host SQLite transactional authority: CI-proven.
- Durable fencing generations: CI-proven after CI discovered/reset bug and fix.
- Latest current-base CI: Python 3.11 PASS, Python 3.12 PASS, analysis-runtime PASS, repo-health PASS.
- Security Baseline PASS.
- Runtime Smoke PASS.
- PR #37 mergeable and intentionally draft.
- Real calibrated HeyGen evidence retained: OpenMontage 42.6318s inside 30–45s target.

## Exit condition
This superwave exits only when implementation + tests + authoritative CI evidence exist for all gates that do not require the 30-production empirical corpus. CAL2 may remain OPEN only because it requires real production evidence; the harness collecting that evidence must be operational.