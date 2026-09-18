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

## Recovery and capability archaeology
27. **Do not treat `main` as the complete capability frontier.** When recovering what MOTION.OS already knows or can do, inspect live open PRs, exact branch heads, stacked bases, supersession notes and durable evidence before declaring a capability missing. `main` remains canonical software truth for promoted code; open PRs are candidate capability/evidence, not production authority.
28. Before recreating a system, search for the existing implementation across `main`, open PR heads, Drive recovery artifacts and the interaction ledger. Prefer recovery/convergence over reimplementation.
29. A PR description, historical green CI or conversation memory never grants current authority. Bind every capability claim to exact SHA + executable evidence + current lifecycle state.
30. Stacked/overlapping PRs are a dependency graph, not a merge checklist. Never merge every open PR independently. Identify terminal/converged candidates, repairs, superseded donors and historical-only branches first.
31. A later repair that demonstrates a defect in an earlier green candidate supersedes that earlier promotion evidence until the repair is incorporated and the combined candidate is requalified.

## Professional-edit production law
32. During an active video edit, pixel/audio/text/timeline-changing work has priority over system-building work. No new architecture unless a demonstrated blocker prevents delivery.
33. Reference videos are timed evidence, not aesthetic prompts. For reference-conditioned editing use physical extraction / Editing DNA / structural template evidence before inventing visual language.
34. A technical PASS is not a professional creative PASS. Resolution, loudness, codec, no-black-frame and similar checks can prove integrity but cannot promote creative quality.
35. Human visual rejection immediately blocks creative promotion. Do not relabel rejected work as Gold, Master, professional or approved because technical QA passed.
36. Do not substitute ad-hoc FFmpeg/Pillow overlays for the canonical editor/motion system when the task is to exercise MOTION.OS/AVE. If a required execution path is unavailable, surface the capability gap or render bounded inserts through a qualified renderer and ingest them with explicit provenance.
37. For editing/reference work, recover and obey `knowledge/reconstruction/VIDEO_REVERSE_ENGINEERING_CANON.md` and the relevant EditingTemplate/forensic evidence when present on the candidate frontier.

## PR convergence / promotion law
38. Promotion starts with a **live promotion graph**: current `main`, Issue #48, latest Issue #39 watermark, branch protection, all open PR heads, base/head ancestry, overlaps, supersessions, repairs and external blockers.
39. Every promotion candidate must pass, on the exact candidate or exact synthetic merge being promoted: `/codereview`, `/securityreview`, `/QAreview`, relevant local verification, clean-runner `MERGE_SAFE`, and any domain-specific physical gate. Review findings P0/P1 must be zero before promotion.
40. Reviews are evidence-producing gates, not prose rituals. Findings must bind file/path/line or contract, severity, exploit/failure mode where relevant, test/reproduction, repair and re-verification status.
41. Merge serially. After each merge: re-read live `main`, invalidate stale candidate evidence, run post-merge/combined-head verification, emit `pr.merged` + `main.verified`, then rebase/reconcile the next candidate. Never batch blind merges.
42. Superseded PRs should be closed unmerged only after proving all unique valid deltas are represented in the converged candidate or intentionally rejected with evidence.
43. Branch protection is a hard governance prerequisite for a production-safe train. Until GitHub enforces it, protocol discipline is not equivalent to administrative protection.
44. Do not close Issue #48 by optimism. Its exit criteria require no unresolved P0/P1, exact merge-candidate gates, current truth convergence, recovery/E2E evidence and verified `main` after merge.
45. The current convergence plan is `docs/PR_CONVERGENCE_MASTERPLAN_2026-09-16.md`; refresh it from live provider truth before any irreversible promotion action.

## Memory / skills authority
46. Do not create duplicate `MEMORY.md`, progress, tools or graph continuity files when existing canonical surfaces already own that responsibility. Durable learning belongs in `knowledge/interaction_ledger.jsonl`, canonical plans/contracts, immutable events and validated state projections.
47. The executable skill authority is `src/skills/registry.py` + `src/skills/runtime.py` and their tests/candidate repairs. A prose `SKILLS.md` must never outrank executable registry/runtime truth.
48. Before declaring a skill absent or broken, inspect the current `src/skills` implementation and relevant live skill PRs (including failure-trace semantics) at exact heads.

## Ponytail minimalism law
49. **Be lazy like a senior engineer: efficient, never careless.** After understanding the task and tracing the real flow end to end, stop at the first rung that holds:
   1. Does this need to exist at all? If not, skip it (YAGNI).
   2. Does it already exist in this codebase? Reuse it; do not rewrite it.
   3. Does the standard library already solve it? Use it.
   4. Does a native platform feature solve it? Use it.
   5. Does an already-installed dependency solve it? Use it.
   6. Can the correct solution be one line? Make it one line.
   7. Only then write the minimum new code that works.
50. The ladder comes **after understanding**, never instead of it. Read the touched code and trace the real flow before choosing the smallest solution. A tiny diff in the wrong place is not minimalism; it is another bug.
51. Bug fixes target the **root cause**, not the named symptom. Inspect every caller/consumer of the function or contract being changed and prefer one shared repair over duplicated path-specific guards.
52. Prefer deletion over addition, boring over clever and the fewest files possible. Do not add abstractions, dependencies or boilerplate that the task does not require.
53. Minimalism never removes trust-boundary validation, data-loss protection, security controls, accessibility, required hardware calibration or explicitly requested behavior. Safety/assurance invariants outrank line-count reduction.
54. Non-trivial new logic must leave behind one runnable regression check: the smallest test or self-check that would fail if the logic breaks. Trivial one-liners do not require ceremonial tests.
55. If a deliberate simplification introduces a known ceiling, mark it with a `ponytail:` comment that states the ceiling and the concrete upgrade path. Do not hide intentional technical debt.
56. Source principle: `DietrichGebert/ponytail`. Treat this section as an efficiency/minimalism operating law; it never overrides MOTION.OS authority, security, QA, provenance, creative-quality or promotion gates.
