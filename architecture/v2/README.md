# MOTION.OS V2 Architecture Package

Authority: `PROPOSED_V2_CANDIDATE`
Owner: `motion://workstream/graph-refactor-v2`
Source revision: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`
Session: `motion://session/chatgpt/graph-refactor-v2/20260829T2344+0200`
Current status: IMPLEMENTED on branch, NOT PROMOTED, NOT production authority.

This directory is the candidate single V2 architecture package. It does **not** silently replace current main documents until reviewed and migrated through the release train.

## Required outputs

- `EXECUTIVE_V2.md` — final architecture synthesis and authority model.
- `ARCHITECTURE_DELTA.md` — explicit current→V2 KEEP/REFINE/REFACTOR/MIGRATE/DEFER delta.
- `hypergraph.snapshot.json` — machine-readable nodes/edges/hyperedges + COS dimension mapping.
- `system_graph.mmd` — human system/authority graph.
- `GRAPH_PROJECTIONS.md` — System, Dependency, Execution, Agent, Session, Knowledge, Decision, Risk, Test, Evidence, Artifact, Workflow, State, Recovery, Security, Architecture, Historical, Roadmap and domain projections from shared IDs.
- `GAP_RISK_MATRIX.md` — ranked gap/risk program.
- `DECISION_LEDGER.md` — major architecture decisions, alternatives and triggers.
- `LEXICON.md` — authority/state/domain vocabulary.
- `IMPLEMENTATION_PROGRAM.md` — phases/waves/tasks/parallelization/executable frontier.
- `CHECKPOINTS.md` — CP0→CP14 objective gates.
- `DEFINITION_OF_DONE.md` — program/phase/task/domain DoD law.
- `ASSURANCE_MODEL.md` — test/security/recovery/performance strategy.
- `MIGRATION_PLAN.md` — current→V2 migration, rollback and supersession.
- `NEXT_ITERATION_METAPROMPT.md` — self-contained successor packet; live truth must be reverified first.

Machine state candidates live in `state/v2/`.

Executable integrity validator:

```bash
python scripts/validate_v2_architecture.py
pytest -q tests/test_v2_architecture_package.py
```

## Authority rules

1. Live GitHub and current canonical domain state override this package if they advance after `source_revision`.
2. No V2 document may self-promote release authority.
3. Current active implementation PR owners remain authoritative for their code scopes.
4. Historical architecture remains historical; migration uses SUPERSEDED metadata rather than deletion.
5. Any merge/promotion requires fresh main + Event Fabric watermark + conflict preflight + exact evidence.
6. Graph projections are derived from shared IDs and never become reverse-write authority.
7. A required V2 output missing from the package is an integrity failure, not optional documentation polish.
