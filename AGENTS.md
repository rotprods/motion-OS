# AGENTS.md — MOTION.OS

North Star: brief → professional motion master.

Rules:
1. Read `state/project_state.json`, `STATE.md`, `GOAL.md`, `TASKS.md`, relevant phase plan(s), and `docs/MERGE_SAFE_TRAIN.md` before work.
2. Inspect recent `state/agent_events/` entries relevant to the paths/workstream before substantial edits; use one branch per active workstream and do not overwrite another agent's active branch.
3. Emit an immutable `work.started` event before substantial work and a `work.completed` or `work.blocked` event at handoff. Emit PR lifecycle events (`pr.opened`, `pr.ready`, `pr.merged`) and `main.verified` when applicable. Use `scripts/agent_event.py`; do not invent a parallel event format.
4. For any task that generates, edits, directs, critiques, repairs, reconstructs for presentation, or promotes motion graphics, read `director.md` before changing the timeline. `director.md` is the creative-direction authority; schemas/config/code remain execution authorities.
5. Distinguish PROPOSED / IMPLEMENTED / EXECUTED / VERIFIED.
6. Never call fixture QA semantic QA.
7. Never promote architecture work unless it reduces a current bottleneck or materially improves quality/fidelity/reliability.
8. Preserve asset and evidence provenance.
9. **Local-first verification is mandatory.** Run the relevant `scripts/local_verify.py` profile before pushing. GitHub Actions is clean-runner merge authority, not an interactive debugger. Do not burn CI minutes iterating on failures reproducible locally.
10. Before marking a risky PR ready, run `python scripts/local_verify.py merge` when the required local runtimes are available. If a required local runtime is unavailable, record that limitation explicitly and let `MERGE_SAFE` provide clean-runner evidence.
11. Promotion to `main` follows the merge-safe train in `docs/MERGE_SAFE_TRAIN.md`. Never batch blind merges; every candidate must be validated against current `main` / merge-group state.
12. Production release requires authoritative semantic evidence.
13. New user-supplied expert knowledge follows the phase-learning protocol:
   - preserve source in `/copy_pastes` first;
   - update the relevant `/plans/phase_*` document;
   - emit an architecture/graph delta when relationships change;
   - update schemas/config/tasks only after conflict analysis;
   - record interaction effects in `knowledge/interaction_ledger.jsonl`.
14. Never silently overwrite a prior expert rule. Classify new knowledge as ADDITIVE, REFINEMENT, CONFLICT, DEPRECATION, TIME_SENSITIVE_CAPABILITY, or EXAMPLE_ONLY.
15. `copy_pastes` are evidence, not canonical rules. Canonical behavior comes from validated plans/config/schema/code.
16. GENERATE and RECONSTRUCT_EXACT are separate optimizers. Never use creative-quality scores as frame-fidelity scores.
17. Measurable video facts must come from deterministic/low-level extraction when available; the LLM normalizes and classifies them rather than inventing them.
18. Master motion rule: nothing moves without a function. Every movement must direct attention, communicate information, generate emotion, or connect states. Otherwise remove it.

## Cross-agent / cross-session constitution
19. Before any authoritative mutation, read `coordination/AGENT_PROTOCOL.md` and `coordination/ACTIVE_AGENTS.yaml`, then inspect the current Coordination Bus/checkpoint and relevant immutable `state/agent_events/`. Chat context alone is never sufficient shared state.
20. Every concurrent agent must have canonical `agent_id` + `session_id`, declare intended write scopes and record the ContextPack/projection revision it is working from.
21. Never silently write through an overlapping active WRITE/EXCLUSIVE_WRITE claim. Split scope, hand off, or resolve the conflict first. Branch names are not ownership locks.
22. Shared contracts (schemas, manifests, entrypoints, provenance/replay identities, renderer interfaces) require an explicit contract claim and dependency-impact check before breaking changes.
23. Postgres/Supabase durable state and event log are an optional future multi-host coordination authority. SQLite remains valid for single-host operational state but MUST NOT be promoted to multi-host authority without executed distributed qualification.
24. COS Graph Engine is a deterministic derived projection/query/reasoning plane. It must be rebuildable from authoritative event/state history and must not become a hidden second source of truth.
25. State mutation + event publication must converge on transactional-outbox semantics when a durable multi-host backend is promoted; consumers must be idempotent and recover from durable offsets. Websocket/realtime delivery is notification, not truth.
26. Session end, blocker, contract change, PR-ready state and ownership transfer require a structured CHECKPOINT plus the canonical immutable agent-event lifecycle where applicable. A future agent must be able to resume without this conversation.
