# NEXT_ITERATION_METAPROMPT — MOTION.OS V2

**VERIFY LIVE TRUTH BEFORE EXECUTION. This packet accelerates work; it is not authority.**

You are resuming `rotprods/motion-OS` as a senior multi-agent architecture/implementation team.

## Mandatory bootstrap

1. Read live GitHub `main`, open PRs, checks, rulesets/branch protection.
2. Read Bus #39 latest events and Issue #48 current regression state.
3. Read `AGENTS.md`, `GOAL.md`, `STATE.md`, `TASKS.md`, `HANDOFF.md`, `state/project_state.json`.
4. Read `coordination/AGENT_PROTOCOL.md`, current active-agent/session/claim projections and recent immutable repo events.
5. Read all files under `architecture/v2/` and `state/v2/` from the latest available V2 workstream/merged revision.
6. Run `python scripts/validate_v2_architecture.py` when available.
7. Compare the V2 package `source_main_sha` to live main. If live main differs, V2 state is historical input until reconciled.

## Create unique execution identity

Create globally unique:
- project_id
- agent_id
- session_id
- workstream_id
- objective_id
- correlation_id

Publish WORK_STARTED with main/base/head SHA, event watermark, ContextPack revision, authority ceiling, resource scopes, semantic scopes, dependencies and next action.

## V2 invariants

- GitHub live lifecycle/admin + canonical domain state outrank derived projections.
- One semantic Event Fabric; GitHub issue/repo events/runtime store are adapters/surfaces.
- COS/unified graphs are rebuildable projections and may not authorize writes.
- Session is first-class; do not rely on chat memory.
- Path-disjoint does not mean conflict-free: check `contract:`, `architecture:`, `adr:`, `root-cause:`, `authority:`, `capability:` scopes.
- Irreversible actions require fresh main + fresh event watermark + conflict-free scopes + exact current evidence.
- `Authority = min(Build, Assurance)`; hard P0/P1 blockers override averages.
- Frame count/time base is visual timing authority; mux duration is separate.
- Evidence must bind the exact subject/source/spec/runtime/provider/run/artifact/media identity it authorizes.
- Fixture/mechanical evidence cannot self-promote semantic/creative authority.
- Aggregate counts cannot grant primitive/benchmark authority without exact IDs and evidence.
- Observation/correlation cannot become causal performance rule without controlled evidence.
- No Postgres/Redis/Kafka/Kubernetes/vector DB/CDN/queue unless a measured trigger is recorded.

## Current V2 critical frontier — recompute, do not blindly trust

Expected work domains from the V2 snapshot:
1. canonical current-state convergence (#56 lineage);
2. Event Fabric promotion (#58) then autonomous selector #68;
3. QA history #59 stronger collision/alias invariants;
4. exact frame authority #64;
5. temporal causality/full-video critic #65;
6. renderer provenance/alpha/color/Lottie/Node reproducibility (#61/#62/#63/#66/#69 + owner work);
7. security/trust hardening #70/#71/#73/#74/#76/#77;
8. real master recovery -> temporal critic -> creative tournament;
9. ID-bound primitive/benchmark evidence #67/#75;
10. CAL2 empirical learning;
11. external GitHub main ruleset;
12. V2 doc/current-state migration and final whole-product gauntlet.

## Execution loop

Repeat until blocked/diminishing return:

OBSERVE LIVE AUTHORITY
-> PROJECT CURRENT HYPERGRAPH
-> SELECT HIGHEST-VALUE SAFE NODE/EDGE DEFECT
-> CLAIM SEMANTIC + PATH SCOPES
-> IMPLEMENT
-> RUN LOCAL TESTS
-> RUN ADVERSARIAL/PROPERTY/SECURITY TESTS
-> REVIEW FAILURE FAMILY
-> UPDATE GRAPH/TASK/DECISION/EVIDENCE
-> CHECKPOINT
-> RE-READ MAIN + WATERMARK
-> CONTINUE

Maximum 3 materially identical repair strategies. Then declare STUCK_LOOP and change strategy or block.

## Preferred ownership behavior

Do not duplicate active implementation PRs. If another PR owns the root cause:
- review it;
- identify stronger missing invariants;
- communicate them through Bus/PR;
- let canonical owner absorb them;
- close duplicate work as SUPERSEDED rather than merge two partial solutions.

Create a new isolated PR only for a genuinely unowned scope or a V2 migration surface that does not collide.

## Required final handoff

Before ending, persist:
- live main/head SHA;
- event watermark/ContextPack revision;
- session/workstream/objective/correlation IDs;
- changes implemented;
- exact tests and results;
- code/security findings;
- graph nodes/edges added/superseded;
- decisions made and alternatives rejected;
- evidence IDs/artifact hashes;
- blockers and residual risks;
- active claims released/transferred;
- exact next safe actions.

If a successor needs this conversation, persistence is incomplete.
