# Phase07 — Post-Merge Event Fabric Convergence Plan

Status: IMPLEMENTING_V3
Parent regression: #48
Canonical bus: #39
Current replacement PR: #58
Current base: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`
Superseded unmerged predecessors: #50, #53

## Architecture split
- **ADR-008** (PR #52): canonical coordination event source + cognitive-pause authority boundary.
- **ADR-009** (PR #58): session-native event fabric, projections, freshness and zero-context semantics layered on ADR-008.
This split resolves a cross-agent ADR-number collision without rewriting either workstream's history.

## Why this exists
Phase07 #44 merged while a regression freeze event was already posted to #39. Later, #53 obtained green checks and then became stale when `main` advanced before promotion. These incidents prove that communication and CI are insufficient unless every irreversible action consumes the newest event watermark + live GitHub state immediately before execution.

## Checkpoints
| Gate | State | Evidence / remaining work |
|---|---|---|
| EF0 freeze/race chronology | VERIFIED | Bus #39 + Issue #48 + superseded #50/#53 lineage |
| EF1 one authority/event fabric architecture | IMPLEMENTED | ADR-008 upstream authority + ADR-009 session fabric |
| EF2 session identity + surface dedupe/conflict | IMPLEMENTED_TESTED | `session_fabric.py` + tests |
| EF3 live GitHub lifecycle supersession | IMPLEMENTED_TESTED | lifecycle reconciliation tests; existing Phase07 `GitHubLifecycleSnapshot` remains canonical provider model |
| EF4 deterministic session graph | IMPLEMENTED_TESTED | projection hash + causal/resource edges |
| EF5 `/autoprompting` persisted | IMPLEMENTED | `coordination/AUTOPROMPT_MULTI_AGENT_EXECUTION.md`; historical `/autoprompt` normalized as deprecated alias |
| EF6 surface adapters to one logical identity | PARTIAL | generic `SurfaceEvent` normalization/hash/dedupe exists; provider-specific adapters remain optional follow-up |
| EF7 current-state projection binds main + watermark | IMPLEMENTED_V1 | existing `LiveContextCompiler` + CanonicalTruthConsistency |
| EF8 irreversible-action freshness | IMPLEMENTED_TESTED | main SHA + event watermark equality gate + CLI; malformed inputs fail closed |
| EF9 session/operator CLI | IMPLEMENTED_V1 | existing coordination CLI + `irreversible-preflight` + `truth-check` |
| EF10 escaped-bug matrix | IMPLEMENTED | REG-001..REG-017 including semantic-collision class |
| EF11 zero-context recovery proof | IMPLEMENTED_TESTED | deterministic LiveContext + SessionGraph test without chat history |
| EF12 exact PR MERGE_SAFE | MUST_REFRESH_ON_EACH_HEAD | evidence is head-specific only |
| EF13 code/security review | PASS_CURRENT_CODE_BEFORE_FINAL_HEAD | no unresolved P0/P1; full Codex scanner not claimed |
| EF14 merge + post-main proof | OPEN | global #39/#48 barrier + newest watermark/main required |

## Hard invariants
No independent event schema; no required chat-memory fact; identical logical events dedupe; conflicting duplicates fail closed; session_id unique by producer contract; stale lifecycle cannot override live GitHub; cancelled/skipped CI never becomes VERIFIED; graphs cannot write authority; truth drift is visible; semantic/ADR/root-cause collisions are reconciled even across different paths; Postgres remains deferred.

## Product/truth follow-ups outside this PR's write scope
PR #56 owns canonical state/release truth reconciliation. Renderer, SkillRuntime, graph-QA, HyperFrames, reverse-engineering and master-audio workstreams remain isolated. Product North Star and Promotion Risk scores remain separate. Phase06 CAL2 remains empirical qualification.

## Exit
Event Fabric convergence closes only when the final exact head passes all gates, ADR-008/ADR-009 are non-contradictory after integration, and a zero-context agent derives the same current state/next safe action without chat history. Promotion still obeys the global cognitive-pause barrier.