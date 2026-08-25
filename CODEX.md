# CODEX.md — GitHub bootstrap handoff

This repository is being bootstrapped from the persistent MOTION.OS project state.

## Mission
Import the preserved canonical source/history into this repository without redesigning MOTION.OS.

## Source of truth split
- GitHub = software source truth.
- Google Drive `MOTION.OS_CANONICAL` = heavy artifacts, recovery bundles, progress tracking.
- SQLite = structured operational knowledge.
- Graph = lineage.

## Required bootstrap
1. Read AGENTS.md, GOAL.md, STATE.md, HANDOFF.md, TASKS.md.
2. Locate the latest full-history Git bundle/source snapshot under the canonical Drive Git-backup area.
3. Restore the source tree and preserved Git history into a clean clone.
4. Keep generated MP4/JPG/PNG/WAV/frames outside source Git; retain manifests, hashes and Drive IDs.
5. Set origin to `https://github.com/rotprods/motion-OS.git`.
6. Reconcile branch naming to `main`, `develop`, `feat/*`, `exp/*`, `release/*`.
7. Push/import source on an isolated bootstrap branch and open a PR to main.
8. Add CI only after the full tests/source tree exists; CI must run pytest, schema/control-plane checks and release guards.
9. Create GitHub issues for all P0/P1 items in TASKS.md.
10. Merge only when source import is complete, tests are green, generated binaries are externalized, and reconciliation reports zero errors.
11. Update Drive handoff with final GitHub SHA/PR URLs.

## Non-goals
Do not add Kubernetes, microservices, vector DB, new graph abstractions, or unrelated architecture. This is continuity/bootstrap work.
