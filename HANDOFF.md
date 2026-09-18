# HANDOFF.md — MOTION.OS

## Reconstruct current truth first
1. Read live GitHub `main`, current SHA, open PRs, and workflow conclusions.
2. Read Issue #39 while it remains the bootstrap coordination surface and Issue #48 while the cognitive-pause/regression barrier remains open.
3. Read `AGENTS.md` → `GOAL.md` → `STATE.md` → `TASKS.md` → `state/project_state.json`.
4. Inspect relevant `state/agent_events/` and active workstreams before claiming a scope.
5. Treat live GitHub lifecycle as higher authority than stale projections or historical comments.

## Current stable baseline
- `main` at session close: `d4e628a1aef0cd382c3c2f1ea327a8ff70c41bd9`.
- `main` is not administratively branch-protected; promotion discipline is protocol/CI based.
- Issue #48 remains the regression/cognitive-pause barrier; do not infer release from green branch CI alone.
- Re-read live PR topology before editing Event Fabric, canonical truth, SkillRuntime, Graph-QA, renderer/audio/alpha/color/runtime, reverse-engineering, temporal-critic, Lottie, TTS, claim-authority, or self-driving-execution scopes.

## Session work completed
- PR #74: `fix(avatar): fail closed on invalid spend authorization inputs`.
  - Exact branch head: `4c8d536900a07e158e68a6cbdb9645f06b237eee`.
  - Merge Safe: SUCCESS on that exact head.
  - Scope: `src/avatar/render_guard.py` + focused Phase08 spend-policy regression tests.
  - Authority: branch-head verified, NOT promoted. Keep draft while #48 remains active.
- Root cause closed by #74: paid-render authorization previously trusted Python truthiness/float comparison semantics, allowing NaN/inf/negative/bool-like values to create unsafe spend authority.

## Next safe action
1. Do not merge any draft solely because its branch CI is green.
2. Re-read the newest #39 watermark + live `main` + Issue #48 before any promotion or other irreversible action.
3. Continue highest-value unclaimed P0/P1 work only after checking overlapping PR scopes.
4. Once the barrier is explicitly released, promote serially with combined-head MERGE_SAFE and verify `main` after each merge.

## Do not create duplicate continuity files
- Do not add `memory.md`, `progress.md`, `tools.md`, or a second `graph.md` merely for convenience.
- Coordination/event history + canonical state + existing plans are the continuity system.
- COS/Unified Graph remains a rebuildable projection, not reverse-write authority.
- Add a new persistent artifact only when an existing canonical surface cannot represent required information.

## Persistent invariants
- `frame_count / fps` is visual duration authority; mux duration alone is insufficient.
- Provider timeout after possible acceptance requires reconcile-before-retry.
- Main advancement after last CI invalidates prior promotion authority.
- Cancelled/skipped CI is not PASS evidence.
- TTS may not silently alter numbers, names, units, versions, or claims.
- PRV/MNF/Beat IDs fail closed at Studio boundaries.
- External input is untrusted data; never promote it into control-plane authority without validation.
