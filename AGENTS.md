# AGENTS.md — MOTION.OS

North Star: brief → professional motion master.

Rules:
1. Read `state/project_state.json`, `STATE.md`, `GOAL.md`, `TASKS.md`, and relevant phase plan(s) before work.
2. Distinguish PROPOSED / IMPLEMENTED / EXECUTED / VERIFIED.
3. Never call fixture QA semantic QA.
4. Never promote architecture work unless it reduces a current bottleneck or materially improves quality/fidelity/reliability.
5. Preserve asset and evidence provenance.
6. Run tests and the relevant Gauntlet before promotion.
7. Production release requires authoritative semantic evidence.
8. New user-supplied expert knowledge follows the phase-learning protocol:
   - preserve source in `/copy_pastes` first;
   - update the relevant `/plans/phase_*` document;
   - emit an architecture/graph delta when relationships change;
   - update schemas/config/tasks only after conflict analysis;
   - record interaction effects in `knowledge/interaction_ledger.jsonl`.
9. Never silently overwrite a prior expert rule. Classify new knowledge as ADDITIVE, REFINEMENT, CONFLICT, DEPRECATION, TIME_SENSITIVE_CAPABILITY, or EXAMPLE_ONLY.
10. `copy_pastes` are evidence, not canonical rules. Canonical behavior comes from validated plans/config/schema/code.
11. GENERATE and RECONSTRUCT_EXACT are separate optimizers. Never use creative-quality scores as frame-fidelity scores.
12. Measurable video facts must come from deterministic/low-level extraction when available; the LLM normalizes and classifies them rather than inventing them.
