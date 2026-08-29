# MOTION.OS V2 Architecture Package

Authority: `IMPLEMENTED_PENDING_REVIEW`
Owner: `motion://workstream/graph-refactor-v2`
Source revision: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`
Canonical candidate PR: `#91`
Donor/superseded candidate: `#90`

This directory and the linked `plans/v2/`, `graph/v2/`, `state/v2/` and schema/validator surfaces form the single V2 candidate package after convergence of the two independent `/GRAPH-REFACTOR-V2` workstreams.

It does **not** silently replace current main authority until CP4 architecture freeze + migration gates are explicitly accepted.

## Canonical V2 package

- `architecture/v2/EXECUTIVE_V2.md` — executive synthesis.
- `architecture/v2/ARCHITECTURE_DELTA.md` — current→V2 delta.
- `architecture/v2/DECISION_LEDGER.md` — architecture decisions/alternatives/triggers.
- `architecture/v2/LEXICON.md` — canonical terms and authority vocabulary.
- `architecture/v2/ASSURANCE_RECOVERY_SECURITY.md` — assurance/security/recovery model.
- `architecture/v2/GRAPH_PROJECTIONS.md` — required System/Dependency/Execution/Agent/Session/Knowledge/Decision/Risk/Test/Evidence/Artifact/Workflow/State/Recovery/Security/Architecture/Historical/Roadmap/domain projections.
- `architecture/v2/CHECKPOINTS.md` — CP0→CP14 objective gates.
- `architecture/v2/DEFINITION_OF_DONE.md` — program/phase/task/domain DoD law.
- `architecture/v2/MIGRATION_PLAN.md` — current→V2 migration, rollback and supersession.
- `graph/v2/motion_os_v2_hypergraph.json` — canonical machine temporal hypergraph candidate.
- `graph/v2/system_graph.mmd` — human graph projection.
- `schemas/v2_hypergraph.schema.json` — Draft 2020-12 graph contract.
- `plans/v2/GAP_RISK_MATRIX.md` — ranked risk/gap program.
- `plans/v2/IMPLEMENTATION_PROGRAM.md` — implementation compiler.
- `plans/v2/NEXT_ITERATION_METAPROMPT.md` — successor packet; live truth must be reverified first.
- `plans/v2/EXECUTION_PROGRESS.md` — execution ledger.
- `state/v2/v2_state.json` — canonical V2 candidate machine state.
- `state/v2/tasks.json` — derived executable task DAG projection.
- `state/v2/checkpoint.json` — derived checkpoint projection.

## Validators

```bash
python scripts/validate_v2_hypergraph.py
python scripts/validate_v2_package.py
pytest -q tests/test_v2_hypergraph_contract.py tests/test_v2_package_contract.py
```

## Authority rules

1. Live GitHub lifecycle/admin + canonical domain state override this package if they advance after its source revision.
2. Graph/docs/task/checkpoint files cannot self-promote production authority.
3. `graph/v2/motion_os_v2_hypergraph.json` is the canonical V2 graph candidate; other graph diagrams are derived projections.
4. Current active implementation PR owners remain authoritative for their code scopes.
5. Historical architecture remains durable and is marked `SUPERSEDED`, never silently rewritten.
6. Any irreversible action requires fresh main, fresh Event Fabric watermark, semantic/path conflict preflight and exact evidence.
7. Missing required V2 outputs or dangling/duplicate graph/task/checkpoint identities fail closed.
8. #90 is donor-only after convergence; no competing V2 architecture may be promoted.
