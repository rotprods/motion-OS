# NEXT_ITERATION_METAPROMPT — MOTION.OS / CGEV2 + PCE

Use this only as an acceleration packet. **VERIFY LIVE TRUTH BEFORE EXECUTION.**

You are a fresh zero-context senior agent entering `rotprods/motion-OS`. Assume the previous agent is dead and chat memory is unavailable/untrusted.

## Bootstrap

1. Resolve `/CGEV2` from the universal command registry and read the exact current protocol body. Resolve `/PROJECT-COMPLETION-ENGINE` as its companion. If command identity/authority is ambiguous, stop with `COMMAND_AUTHORITY_BLOCKED`.
2. Read live `main` SHA and protection state.
3. Read live `AGENTS.md` and `GOAL.md`.
4. Read newest Issue #39 event/comment and treat its latest watermark as fresher than this packet.
5. Read Issue #48. Do not infer barrier release from CI, Todoist, a merge, or a comment that is not an explicit authorized release.
6. Read Issue #93 and live PR topology. Compare each PR body to its current head; stale body claims have no current authority.
7. Inspect relevant immutable `state/agent_events/`, Drive evidence, and current task projections.
8. Read `state/cgev2/death_resilience_contextpack_2026-09-01.json` and `graph/cgev2/death_resilience_graph_2026-09-01.json` only after steps 1–7; they are derived snapshots, not current truth.

## Non-negotiable authority rules

- `LIVE_GITHUB > EVENT_FABRIC/EVENT_LEDGER > IDENTITY_BOUND_EVIDENCE > CURRENT_VALIDATED_MACHINE_STATE > COS/CONTEXTPACK > DOCS/TODOIST`.
- Never call fixture/sample/contact-sheet QA authoritative full-video semantic QA.
- Never infer artifact identity from name, dimensions, duration, or narrative; bind exact SHA.
- `IMPLEMENTED != EXECUTED != VERIFIED != PROMOTED != PRODUCT_QUALIFIED != PROJECT_DONE`.
- Any main/watermark/owned-PR-head drift invalidates the previous ContextPack frontier.
- Respect semantic scope, not merely file-path separation.

## State expected near the 2026-09-01 snapshot

The old snapshot expected main `d4e628a1...`, Issue #48 OPEN, PR #126 active T08, PR #119 P4 blocked on external full-video provider, PR #120 P7 security integration draft, PR #118 P3 physical master verified-unpromoted and PR #123 frame-count hardening open.

**Do not assume any of these are still true. Re-read them.**

## Required reconstruction output before coding

Produce machine/human state with:

- current main SHA + protection;
- newest Event Fabric watermark;
- barrier state;
- active PRs + exact heads + semantic ownership;
- verified-unpromoted capabilities;
- external blockers;
- P0/P1 risks;
- critical path to PROJECT_DONE;
- highest-value READY task;
- conflicts that prohibit work;
- ContextPack staleness verdict.

Then create a globally unique session identity and publish `WORK_STARTED`.

## Execution selection

Prefer the highest-value task that is READY and non-overlapping. At the historical snapshot:

- T08 qualification was owned by another active agent: do not edit its files.
- P4 was externally blocked on a real provider: do not fabricate evidence.
- P7 security/recovery work could progress independently with preflight.
- Promotion was blocked by Issue #48 and missing native main protection.

Recompute this frontier from live truth.

## Executable staleness gate

Before any mutation, serialize the freshly observed authority into an **ephemeral** JSON file (do not commit it) with this schema:

```json
{
  "schema": "motion-os.cgev2-live-truth-probe/v1",
  "main_sha": "<live-40-char-sha>",
  "main_protected": false,
  "event_bus_latest_comment_id": 0,
  "promotion_barrier_state": "OPEN",
  "promotion_release_event_observed": false,
  "program_heads": {
    "PCE": "<live-head>",
    "V2": "<live-head>",
    "P3": "<live-head>",
    "P3_FRAME": "<live-head>",
    "P4": "<live-head>",
    "P7": "<live-head>",
    "P7_SSRF": "<live-head>",
    "T08": "<live-head>"
  }
}
```

Then execute:

```bash
python scripts/verify_cgev2_death_resilience.py \
  --live-truth .artifacts/cgev2-live-truth.json \
  --require-live
```

Any `stale:*`, missing live field, packet-integrity error, command-resolution mismatch or non-zero exit invalidates the old frontier. Reconcile again before writing. Static packet validation without `--require-live` proves packet integrity only; it never grants mutation authority.

## Wave loop

`RECONCILE → CLAIM → IMPLEMENT → LOCAL TEST → ADVERSARIAL TEST → PHYSICAL PROOF → CODE/SECURITY REVIEW → PERSIST EVIDENCE → UPDATE GRAPH/TASKS/HANDOFF → RECONCILE AGAIN`.

Before irreversible merge/publish/spend/deploy/delete: re-read newest watermark + live GitHub immediately before action.

## Handoff law

Before this new session ends, persist:

- exact session/workstream/correlation IDs;
- main/base/head SHAs;
- PRs and owned scopes;
- tests and exact outcomes;
- evidence/artifact IDs and hashes;
- blockers and external dependencies;
- next safe action;
- a fresh successor packet.

If the next agent needs this conversation, the session failed.
