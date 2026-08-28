# HANDOFF.md — MOTION.OS

## Start
1. Read live GitHub `main`, open PRs and workflow conclusions before trusting this file.
2. Read `AGENTS.md` → `GOAL.md` → `STATE.md` → `TASKS.md`.
3. Inspect `state/project_state.json`, `state/checkpoints.json`, `registry/artifact_registry.json` and recent `state/agent_events/`.
4. Read Issue #39 while it remains the bootstrap coordination bus and Issue #48 while the regression audit remains open.
5. Continue the highest-priority safe P0/P1 after scope/conflict preflight.

## Current creative truth
- **RC09E is the logical working master.**
- RC09E promotion decision: `reports/rc09/RC09_DECISION.md`.
- RC09E heavy-artifact authority is **DEGRADED_EXTERNAL** until it is versioned/bound in Drive + `registry/artifact_registry.json` / `state/drive_sync.json`.
- **RC06 remains the registered rollback artifact**, retained for lineage and recovery.
- RC07: HOLD / NOT PROMOTED.
- RC09E preserves the validated 6.65–7.50s RC06 transition and the canonical narrative.

## Verified capability truth
- Remotion physical production runtime: **VERIFIED** via merged PR #42 and runtime contract evidence.
- HyperFrames compiler/adapter exists, but physical production runtime authority remains open.
- Scheduler filtered-dependency deadlock and multi-render global-clock/z-order regressions were fixed on main by merged PRs #54/#55; preserve their invariants.

## Next product move
Do not spend the next wave on generic coordination infrastructure. Highest-value product convergence remains:
1. physical HyperFrames runtime proof;
2. authoritative full-video temporal critic;
3. fresh candidate/hash-bound RC09E creative scoring;
4. RC09E artifact registration/versioning;
5. primitive and benchmark empirical qualification.

## Remaining hard gates
- HyperFrames physical production runtime.
- Authoritative full-video temporal critic.
- RC09E creative convergence >= release thresholds with candidate/hash-bound evidence.
- P0/P1 release defects = 0.

## Permanent safety invariants
- visual duration authority = frame_count / fps; mux/container padding is separate;
- fencing generations remain monotonic across release/reacquire;
- JSON Schema format validation uses a real format checker;
- replica drift never grants overwrite authority;
- timeout after possible paid-provider acceptance requires reconciliation before retry;
- main advancement invalidates prior merge proof until combined-head revalidation;
- cancelled/skipped CI is not VERIFIED evidence;
- stale docs/events never override live GitHub lifecycle;
- PRV/MNF/semantic Beat IDs fail closed at Studio boundary;
- performance correlation never self-promotes into causal authority.
