# HANDOFF.md — MOTION.OS

## Bootstrap order
1. Read `AGENTS.md`.
2. Read `GOAL.md`.
3. Read `STATE.md`.
4. Read `TASKS.md`.
5. Run `python scripts/reconcile_planes.py`.
6. Run `python scripts/session_close.py --dry-run`.
7. Inspect `state/project_state.json`, `registry/artifact_registry.json`, and Drive progress tracking.

## Persistence model
- GitHub = software source of truth.
- Drive = heavy artifacts + progress + recovery.
- SQLite = structured operational knowledge, reproducible from migrations/seeds.
- Graph = execution/causal lineage.
- Local sandbox = disposable compute only.

## Working master
RC05 remains canonical until RC06 formal comparison completes.
