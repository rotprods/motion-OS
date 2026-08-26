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
