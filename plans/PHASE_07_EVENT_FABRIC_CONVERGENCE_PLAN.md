# Phase07 — Post-Merge Event Fabric Convergence Plan

Status: IMPLEMENTING_V3
Parent regression: #48
Canonical bus: #39
Current replacement PR: #58
Current base: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`
Superseded unmerged predecessors: #50, #53

## Why this exists
Phase07 #44 merged while a regression freeze event was already posted to #39. Later, #53 also obtained green checks and then became stale when `main` advanced before promotion. These incidents prove that communication and CI are insufficient unless every irreversible action consumes the newest event watermark + live GitHub state immediately before execution.

## Checkpoints
| Gate | State | Evidence / remaining work |
|---|---|---|
| EF0 freeze/race chronology | VERIFIED | Bus #39 + Issue #48 + superseded #50/#53 lineage |
| EF1 one semantic fabric ADR | IMPLEMENTED | ADR-008 in #58 |
| EF2 session identity + surface dedupe/conflict | IMPLEMENTED_TESTED | `session_fabric.py` + tests |
| EF3 live GitHub lifecycle supersession | IMPLEMENTED_TESTED | lifecycle reconciliation tests; existing Phase07 `GitHubLifecycleSnapshot` remains canonical provider model |
| EF4 deterministic session graph | IMPLEMENTED_TESTED | projection hash + causal/resource edges |
| EF5 `/autoprompt` persisted | IMPLEMENTED | `coordination/AUTOPROMPT_MULTI_AGENT_EXECUTION.md` |
| EF6 surface adapters to one logical identity | PARTIAL | generic `SurfaceEvent` normalization/hash/dedupe exists; provider-specific #39/repo/EventStore adapters still optional follow-up |
| EF7 current-state projection binds main + watermark | IMPLEMENTED_V1 | existing `LiveContextCompiler` binds main/watermark; session snapshot binds same values; CanonicalTruthConsistency added for lifecycle drift |
| EF8 irreversible-action freshness | IMPLEMENTED_TESTED | main SHA + event watermark equality gate + CLI; malformed authority inputs fail closed |
| EF9 session/operator CLI | IMPLEMENTED_V1 | existing coordination CLI + new `irreversible-preflight` and `truth-check`; dedicated semantic aliases for every lifecycle event are not required |
| EF10 escaped-bug matrix | IMPLEMENTED | REG-001..REG-016 |
| EF11 local/contract tests | CODE_READY | cloud clean-runner currently supplies evidence; local-first remains preferred when checkout available |
| EF12 exact PR MERGE_SAFE | MUST_REFRESH_ON_EACH_HEAD | green evidence is head-specific only; latest head must pass |
| EF13 code/security review | IN_PROGRESS | diff review found no P0/P1 so far; final exact-head review required |
| EF14 merge + post-main proof | OPEN | requires newest bus watermark + live main immediately before action |

## Hard invariants
No independent event schema; no required chat-memory fact; same logical event deduplicates; conflicting duplicate fails closed; session_id unique by producer contract; stale lifecycle cannot override live GitHub; cancelled/skipped CI never becomes VERIFIED; session/COS graph cannot write authority; truth drift is visible rather than silently overwritten; Postgres remains deferred.

## Regression invariants added by this wave
1. A green PR proof becomes stale when main advances before promotion.
2. An irreversible-action ContextPack becomes stale when either main SHA or event watermark advances.
3. A declared surface payload hash must match canonical normalized payload.
4. Session graph rejects cross-session and cross-correlation injection.
5. Historical claims may remain immutable evidence but must be marked non-current when they conflict with live lifecycle.
6. Truth-consistency detection never grants mutation authority over stale files.

## Current known product/truth follow-ups outside this PR's write scope
- canonical state surfaces (`project_state`, STATE, TASKS, checkpoints, ACTIVE_AGENTS) require reconciliation by the regression owner without conflicting writes;
- current release evidence must be candidate/media-hash bound;
- duplicate alignment-weight sources require canonicalization or enforced parity;
- Product North Star score and Promotion Risk score remain separate;
- Phase06 CAL2 remains empirical, not code qualification.

## Exit
Issue #48 may consider Event Fabric convergence closed only when EF0–EF14 have exact evidence and a zero-context agent can derive the same current state and next safe action without chat history. Product regression work then regains priority over generic coordination expansion.