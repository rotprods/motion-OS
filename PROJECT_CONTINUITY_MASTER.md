# MOTION.OS — PROJECT CONTINUITY MASTER

Status: **BOOTSTRAP POINTER / NOT CURRENT-STATE AUTHORITY**

This file exists so a zero-context agent does not need the previous conversation to find MOTION.OS authority.

## Mandatory first action

**VERIFY LIVE TRUTH BEFORE EXECUTION.** Never treat this file, chat memory, a PR body, Todoist, or a historical ContextPack as current authority by itself.

Resolve and execute `/CGEV2`, then `/PROJECT-COMPLETION-ENGINE` when completion work is intended.

Bootstrap sequence:

1. Resolve `/CGEV2` through the project command-registry pointer when available; otherwise locate the registered universal command definition and fail closed on ambiguity.
2. Read live `main` and its SHA/protection state.
3. Read `AGENTS.md` and `GOAL.md` from live `main`.
4. Read Issue #39 and obtain the **latest** coordination/Event-Bus watermark.
5. Read Issue #48 and look for an explicit authoritative barrier-release event. OPEN/no release means no promotion.
6. Read Issue #93 and live PR topology; PR body text is historical unless reconciled to its current head.
7. Inspect recent immutable `state/agent_events/` for the intended workstream.
8. Inspect the latest `state/cgev2/death_resilience_contextpack_*.json` and `graph/cgev2/death_resilience_graph_*.json` only as **derived recovery accelerators**. Any live drift invalidates their operational frontier.
9. Inspect Drive `MOTION.OS_CANONICAL`, especially `00_AGENT_HANDOFF`, and verify artifacts by SHA rather than filename.
10. Reconcile Todoist only as an operator projection.
11. Create a unique session identity, publish `WORK_STARTED`, claim non-overlapping scopes, then execute.

## Authority order

`LIVE_GITHUB_LIFECYCLE_AND_MAIN → CANONICAL_EVENT_FABRIC/IMMUTABLE_EVENTS → IDENTITY_BOUND_EVIDENCE/ARTIFACTS → CURRENT_VALIDATED_MACHINE_STATE → DERIVED_COS/CONTEXTPACK → HUMAN DOCS/TASK PROJECTIONS`.

## Current continuity defect rule

This root file must remain a **pointer**, not a hand-maintained copy of volatile project state. It must never contain a fixed `current main`, active PR head, or `PROJECT_DONE=true` claim. Those belong in revisioned evidence snapshots and must be refreshed from live authority.

## Death-resilience packet

Candidate implementation lives under:

- `coordination/cgev2/CGEV2_DEATH_RESILIENCE_HANDOFF_2026-09-01.md`
- `coordination/cgev2/NEXT_ITERATION_METAPROMPT_2026-09-01.md`
- `state/cgev2/death_resilience_contextpack_2026-09-01.json`
- `graph/cgev2/death_resilience_graph_2026-09-01.json`
- `scripts/verify_cgev2_death_resilience.py`

A successor must still refresh live truth before mutation.
