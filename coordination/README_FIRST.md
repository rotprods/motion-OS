# MOTION.OS Coordination — README FIRST

Use this when resuming with zero chat context.

## 1. Reconstruct product truth
Read in order:
1. `/AGENTS.md`
2. `/GOAL.md`
3. `/STATE.md`
4. `/TASKS.md`
5. `/HANDOFF.md`
6. `/state/project_state.json`

## 2. Reconstruct concurrent-work truth
Read:
1. `coordination/AGENT_PROTOCOL.md`
2. `coordination/ACTIVE_AGENTS.yaml`
3. `coordination/CONFLICT_MATRIX.md`
4. GitHub Issue #43 Coordination Bus latest CHECKPOINT/CLAIM/CONFLICT messages
5. PRs relevant to your dependency neighborhood

## 3. Reconstruct Phase07 architecture
Read:
1. `plans/phase_07_agentic_coordination_cos_graph_masterplan.md`
2. `architecture/ADR_007_AGENTIC_COORDINATION_AUTHORITY.md`
3. `architecture/agentic_coordination_cos_graph.mmd`
4. `schemas/coordination_event.schema.json`
5. `schemas/resource_lease.schema.json`
6. `schemas/context_pack.schema.json`
7. `migrations/phase07_coordination_kernel.sql`

## 4. Authority model
- GitHub: executable software truth
- Drive: artifacts / progress / recovery
- SQLite: single-host operational state
- PostgreSQL/Supabase: target multi-host coordination/event authority
- COS: rebuildable deterministic projection/query/reasoning plane
- Issue #43: interim low-frequency coordination bus only

## 5. Current concurrent topology
- #34 Remotion runtime
- #35 Studio Engine / physical analysis
- #37 Content Intelligence / Avatar Factory
- #44 Phase07 coordination kernel

Exact changed-file overlap among #34/#35/#37 was zero at the 2026-08-26 snapshot; semantic contract overlap is high.

## 6. Before writing
Publish/read work intent, determine resource scope, detect active overlap, acquire a durable lease when W2 authority exists, and record the ContextPack/source revisions used. Do not treat a branch name as a lock.

## 7. Session close
Publish a structured CHECKPOINT to the durable coordination plane (Issue #43 during bootstrap) and release active claims/leases.
