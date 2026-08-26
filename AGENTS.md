# AGENTS.md — MOTION.OS

North Star: brief → professional motion master.

Rules:
1. Read `state/project_state.json`, `STATE.md`, `GOAL.md`, `TASKS.md`, and relevant phase plan(s) before work.
2. For any task that generates, edits, directs, critiques, repairs, reconstructs for presentation, or promotes motion graphics, read `director.md` before changing the timeline. `director.md` is the creative-direction authority; schemas/config/code remain execution authorities.
3. Distinguish PROPOSED / IMPLEMENTED / EXECUTED / VERIFIED.
4. Never call fixture QA semantic QA.
5. Never promote architecture work unless it reduces a current bottleneck or materially improves quality/fidelity/reliability.
6. Preserve asset and evidence provenance.
7. Run tests and the relevant Gauntlet before promotion.
8. Production release requires authoritative semantic evidence.
9. New user-supplied expert knowledge follows the phase-learning protocol:
   - preserve source in `/copy_pastes` first;
   - update the relevant `/plans/phase_*` document;
   - emit an architecture/graph delta when relationships change;
   - update schemas/config/tasks only after conflict analysis;
   - record interaction effects in `knowledge/interaction_ledger.jsonl`.
10. Never silently overwrite a prior expert rule. Classify new knowledge as ADDITIVE, REFINEMENT, CONFLICT, DEPRECATION, TIME_SENSITIVE_CAPABILITY, or EXAMPLE_ONLY.
11. `copy_pastes` are evidence, not canonical rules. Canonical behavior comes from validated plans/config/schema/code.
12. GENERATE and RECONSTRUCT_EXACT are separate optimizers. Never use creative-quality scores as frame-fidelity scores.
13. Measurable video facts must come from deterministic/low-level extraction when available; the LLM normalizes and classifies them rather than inventing them.
14. Master motion rule: nothing moves without a function. Every movement must direct attention, communicate information, generate emotion, or connect states. Otherwise remove it.

## Cross-agent / cross-session constitution
15. Before any authoritative mutation, read `coordination/AGENT_PROTOCOL.md` and `coordination/ACTIVE_AGENTS.yaml`, then inspect the current Coordination Bus/checkpoint. Chat context alone is never sufficient shared state.
16. Every concurrent agent must have canonical `agent_id` + `session_id`, declare intended write scopes and record the ContextPack/projection revision it is working from.
17. Never silently write through an overlapping active WRITE/EXCLUSIVE_WRITE claim. Split scope, hand off, or resolve the conflict first. Branch names are not ownership locks.
18. Shared contracts (schemas, manifests, entrypoints, provenance/replay identities, renderer interfaces) require an explicit contract claim and dependency-impact check before breaking changes.
19. Postgres/Supabase durable state and event log are the target multi-host coordination authority. SQLite remains valid for single-host operational state but MUST NOT be promoted to multi-host authority.
20. COS Graph Engine is a deterministic derived projection/query/reasoning plane. It must be rebuildable from authoritative event/state history and must not become a hidden second source of truth.
21. State mutation + event publication must converge on transactional-outbox semantics; consumers must be idempotent and recover from durable offsets. Websocket/realtime delivery is notification, not truth.
22. Session end, blocker, contract change, PR-ready state and ownership transfer require a structured CHECKPOINT. A future agent must be able to resume without this conversation.
