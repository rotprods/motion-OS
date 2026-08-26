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
15. Before material work, read GitHub coordination issue `#39` and `coordination/agent_registry.json`; inspect active PRs touching the requested path or semantic contract.
16. Every concurrent session must publish `WORK_STARTED` to #39 before modifying a shared workstream, including branch, base SHA, intended `resource_scope`, dependencies and PR when known.
17. A resource is not only a file. Schemas, APIs, identity rules, handoff manifests, event contracts, render authority and stable semantic IDs are leaseable semantic resources even when implementations live in different files.
18. If an active workstream overlaps the intended path or semantic resource, do not silently proceed. Emit `CONFLICT_DETECTED`, isolate the change, or obtain an accepted cross-workstream decision.
19. Breaking cross-workstream contract changes require `DECISION_PROPOSED` before implementation and an explicit accepted/superseding decision before promotion.
20. Publish `CHECKPOINT` after material architecture/state changes and `HANDOFF` before the session ends. A handoff must include evidence, unresolved risks and exact next action.
21. GitHub issue #39 is the bootstrap developer coordination bus. The target authority is the durable Agentic Event Kernel in `architecture/AGENTIC_COORDINATION_OS.md`; never mistake GitHub comments for final runtime transactional authority.
22. Agent/session/project/work/task identities use canonical `motion://...` URIs; display names are metadata only.
23. Commands and outcomes are distinct facts. REQUESTED/STARTED/COMPLETED/FAILED/VERIFIED must never be collapsed.
24. Any protected multi-agent write must eventually carry expected state revision + lease generation/fencing token. Stale writers fail closed.
25. The COS graph is a rebuildable projection of canonical event/state truth. No agent may mutate the graph as a backdoor to change authoritative project state.
26. Context used for autonomous work must be generated at a declared event watermark/projection hash once the Context Pack Compiler is active. Until then, record the Git base SHA and coordination event IDs used for the session.
27. PR closed != PR merged != CI green != deployed != verified. Emit and reason about each lifecycle state independently.
28. No agent may repurpose an unrelated Supabase/database project for MOTION.OS coordination. Network authority requires an explicitly designated project and migration/evidence trail.
29. Preserve existing Phase06 render-safety guarantees while converging shared coordination primitives. Never weaken idempotency, reconcile-before-retry, claim lineage, stable beat identity, provenance roots or replay fingerprints for architectural convenience.
