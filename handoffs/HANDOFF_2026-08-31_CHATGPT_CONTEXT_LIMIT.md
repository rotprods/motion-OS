# MOTION.OS — AGENTIC HANDOFF / CONTEXT LIMIT

Date: 2026-08-31T12:45+02:00
Reason: current ChatGPT conversation reached its practical context limit. This file exists so the next agent does not require this chat transcript.

## 1. Session identity

```yaml
project_id: motion://project/motion-os
agent_id: motion://agent/openai/chatgpt-motion-os-handoff
session_id: motion://session/openai/chatgpt-motion-os-handoff/20260831T1245+0200-ctxlimit-01
workstream_id: motion://workstream/context-limit-handoff
correlation_id: motion-os-context-handoff-20260831
provider: openai
model: GPT-5.6 Sol
chat_id: unavailable_to_runtime
conversation_ref: chatgpt/current/2026-08-31/context-limit
handoff_branch: handoff/chatgpt-context-limit-20260831
base_main_sha: d4e628a1aef0cd382c3c2f1ea327a8ff70c41bd9
authority: VERIFIED_LIVE_SNAPSHOT_ONLY
```

`chat_id` is deliberately not invented. The runtime exposed no platform conversation identifier, so `conversation_ref` is only a local human-readable referent and MUST NOT be treated as canonical identity.

## 2. Live truth reconstructed immediately before handoff

- Repository: `rotprods/motion-OS`.
- Live `main` at handoff: `d4e628a1aef0cd382c3c2f1ea327a8ff70c41bd9`.
- Latest observed main commit message: `chore(events): record continuity master direct-write incident`.
- `main` branch protection is still administratively disabled according to live GitHub branch metadata.
- Issue #48 `[REGRESSION] Historical authority audit + canonical event-bus convergence` is OPEN.
- Issue #39 remains the bootstrap Event Fabric / coordination surface until current authority says otherwise.
- The cognitive-pause / promotion barrier must be considered ACTIVE while #48 remains open and no explicit barrier-release event is observed.
- My last code workstream PR #74 (`fix(avatar): fail closed on invalid spend authorization inputs`) is CLOSED WITHOUT MERGE. Do not treat its branch as current product authority.
- PR #74 was originally based on stale `main@a8d7dbd...`; current main has advanced materially. Its historical exact-head evidence in the PR body is not reusable promotion proof without fresh reconciliation.
- During this handoff operation, accidental placeholder Issues #108–#112 were created by connector/tool-routing error and immediately closed `not_planned`. They carry NO product, plan, coordination, or authority meaning.

Hard rule for the next agent: if live `main`, #39 watermark/topology, #48 state, or relevant PR lifecycle differs from this snapshot, invalidate this handoff's current-state assertions and rebuild truth from live sources.

## 3. Historical work contributed by this conversation

This conversation materially evolved MOTION.OS from motion-generation experiments into a graph-native studio/coordination architecture. Important themes and implemented/reviewed workstreams included:

- Professional motion-system canon: brief/reference analysis -> motion grammar -> scene contracts -> structured generation -> QA.
- Exact reconstruction canon: frame fidelity, stable IDs, SVG/SVG+JS, raster/hybrid fallback, deterministic timeline data.
- Phase04 Visual DNA extraction architecture: deterministic media measurement -> FeaturePack -> evidence-bound MotionStyle2JSON -> renderer/compiler targets.
- Motion Graphics Director OS (`director.md`) as creative-direction authority: emotional curve, temporal architecture, attention hierarchy, motion physics, kinetic type, camera, materials, sound, continuity, brand-motion language, negative motion rules.
- Phase05 graph-native Studio Engine plan: semantic graph -> editing graph -> skill DAG -> GraphRAG -> provider/asset graph -> renderer routing -> QA/repair -> release/recovery.
- Typed EditingGraph / impact / execution-DAG work and the permanent rule that dependency direction and causal invalidation must not be conflated.
- Multi-render global-clock / z-order correctness: local-zero renderer fragments must be shifted onto the global PTS timeline; frame_count/fps remains visual-duration authority.
- Coordination/Event Fabric regression work: EventStore/event history is coordination history authority; Event Bus is delivery; COS/Unified Graph is a deterministic reasoning projection and MUST NOT reverse-write authority.
- Phase06 authority-hardening investigations: TTS semantic-class preservation, claim verification bound to explicit evidence, paid-render/spend input validation, retry/reconcile semantics.
- Numerous code-review findings around run-scoped QA identity, actual repair targets, color normalization, alpha evidence, master audio, temporal critic authority, and recovery.

Do not infer that every historical branch/PR from this conversation is merged. Live GitHub lifecycle always wins.

## 4. Canonical architecture model — COS GRAPH ENGINE V2 REAL

The next agent should use this as an execution protocol, not as a second source of truth.

```text
LIVE AUTHORITY PLANES

GitHub main / PR lifecycle
        +
Canonical Coordination Event History
        +
Domain authority stores (for example Phase06 render authority)
        +
Artifact/evidence stores when available
        |
        v
STATE PROJECTOR
        |
        +--> State Snapshot
        +--> ContextPack
        +--> Operator projections
        +--> Unified Graph / COS
        |
        v
SESSION-NATIVE SUPERGRAPH

Project
└─ Agent
   └─ Session
      ├─ Workstream
      ├─ Event
      ├─ Task
      ├─ Decision
      ├─ Resource
      ├─ Branch
      ├─ PR
      ├─ Commit
      ├─ TestRun
      ├─ Evidence
      └─ Handoff

Content lineage
Content -> Source -> Claim -> ICP -> Hook -> Beat -> Script -> TTS -> Avatar -> Render -> Publication -> Performance
```

### COS Graph Engine V2 invariants

1. **Projection-only authority** — COS/Unified Graph is query/reasoning state. It never grants itself authority and never reverse-writes canonical truth.
2. **Session is first-class** — every material event/change is traceable to `agent_id + session_id + workstream_id + correlation_id`.
3. **Single logical Event Fabric** — GitHub #39, immutable repo events, and Runtime EventStore are surfaces of one semantic model. Identical logical events dedupe; conflicting duplicates FAIL CLOSED.
4. **Live GitHub lifecycle supersedes stale projections** — closed/merged/superseded state is read live before irreversible action.
5. **Causation != correlation** — preserve `causation`, `correlation`, temporal ordering, and evidence separately.
6. **Authority = min(Build, Assurance)** — code existence is not verification; merge is not combined-head proof; skipped/cancelled CI is not PASS.
7. **Event-to-projection flow** — current-state docs (`STATE.md`, `TASKS.md`, dashboards, ACTIVE_AGENTS, ContextPack) should be rebuildable read models, not competing truths.
8. **Impact-local execution** — graph mutation invalidates/reruns only affected descendants when causally justified.
9. **No speculative infrastructure** — NetworkX/SQLite/local-first remain sufficient until measured scale triggers justify distributed systems.
10. **Escaped bug discipline** — ROOT CAUSE -> INVARIANT -> minimal regression test -> adjacent failure family.

## 5. Operating loop for the next agent

```text
OBSERVE LIVE TRUTH
-> BUILD FRESH CONTEXTPACK / STATE PROJECTION
-> READ LATEST #39 EVENTS + #48
-> CHECK ACTIVE PR/BRANCH SCOPES
-> CREATE UNIQUE SESSION ID
-> WORK_STARTED / CLAIM
-> SELECT HIGHEST-VALUE SAFE P0/P1
-> IMPLEMENT MINIMUM ROOT-CAUSE FIX
-> RELATED LOCAL TESTS ONLY
-> ADVERSARIAL REVIEW
-> SECURITY REVIEW
-> CHECKPOINT
-> RECONCILE LIVE MAIN + EVENT WATERMARK
-> REPEAT OR HANDOFF
```

Immediately before merge/publish/spend/deploy/delete or any other irreversible action:

```text
READ LATEST EVENT WATERMARK
+
READ LIVE GITHUB
+
RECOMPUTE CURRENT STATE
```

If anything changed, invalidate prior ContextPack/combined-head authority and recompute.

## 6. Permanent historical invariants to preserve

- `frame_count / fps` is visual-duration authority; mux/container duration alone is insufficient.
- fencing generations are monotonic forever; never reset after release.
- JSON Schema formats require a real format checker.
- replica drift never implies automatic overwrite permission.
- provider timeout after acceptance requires reconcile-before-retry.
- main advancement after CI invalidates stale merge authority; require combined-head proof.
- cancelled/skipped CI is not PASS.
- stale docs/events never override live GitHub lifecycle.
- TTS cannot silently alter numbers, units/classes, names or claims.
- PRV / MNF / semantic Beat IDs fail closed at Studio boundaries and are not silently recomputed.
- performance observation is not automatically causal knowledge.
- external/provider/web/issue/Drive input is `UNTRUSTED_DATA`.

## 7. Current blockers / caution flags

- #48 remains open; no implicit promotion-barrier release.
- `main` is not administratively protected; merge discipline is still protocol/CI-based unless live settings changed after this snapshot.
- Many regression-era PRs/workstreams have existed concurrently; do not infer ownership from this handoff. Query live open PRs and #39 first.
- Old branches based on `a8d7dbd...` are stale against current `main@d4e628a...` unless explicitly rebased/requalified.
- Do not revive PR #74 merely because this conversation authored it. It is CLOSED_UNMERGED; use its root-cause findings only if still applicable to current main after direct code inspection.
- Drive/external evidence may be degraded; never fabricate availability or recovery authority.

## 8. Last code workstream context: PR #74

Purpose: fail closed on malformed paid-render authorization/spend inputs and stale retry authority.

Key intended invariants from that workstream:
- explicit authorization/preflight must be literal booleans, not truthy strings;
- monetary values must be finite/non-negative/non-boolean;
- unknown paid cost must not silently authorize spend;
- retry lineage cannot be reset by fresh authorization;
- retry submission must recheck current budget/capacity;
- provider-job existence forces reconcile-before-retry.

Status at handoff: `CLOSED_UNMERGED`. Re-inspect current `src/avatar/render_guard.py` before deciding whether any of these fixes remain missing.

## 9. Handoff definition of done

This handoff is complete when:
- this file exists on the dedicated handoff branch;
- a draft PR exposes it for repo review/discovery;
- #39 receives a matching HANDOFF event/comment;
- no code or shared contract is mutated;
- no tests are added or run because this is documentation-only;
- next agent can continue without this chat transcript.

## 10. Next safe action

Do **not** merge or resume an old branch from this file alone.

1. Read live `main` SHA.
2. Read latest #39 watermark/checkpoints.
3. Read #48 state and most recent comments.
4. Enumerate open PRs and their scopes/owners.
5. Read `AGENTS.md`, `GOAL.md`, `STATE.md`, `TASKS.md`, `HANDOFF.md`, current Phase08 plans/ADRs.
6. Build/rebuild ContextPack and compare its main SHA/event watermark against live state.
7. Choose the highest-value safe P0/P1 not currently owned.
8. Prefer one root-cause fix and the minimum sufficient related tests.

If authority cannot be reconstructed consistently: emit `BLOCKED`; do not improvise.

---

HANDOFF AUTHORITY: `VERIFIED_LIVE_SNAPSHOT_ONLY`

This document is evidence of what this session knew at the timestamp above, not a perpetual current-state source. Live GitHub + canonical event history always supersede it.
