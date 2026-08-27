# Phase07 — Event Fabric Convergence + Session Graph Execution Plan

Status: IMPLEMENTING
Parent regression: #48
Parent Phase07: #44
Canonical bus: #39
Branch: `feat/session-native-event-bus-convergence`

## Goal
Make cross-agent coordination session-native and transport-neutral so every agent can reconstruct the same current truth from live GitHub + canonical events, operate safely, and leave a deterministic handoff/supergraph without relying on chat history.

## Checkpoints
- EF0 Freeze observed and WORK_STARTED emitted on #39.
- EF1 ADR-008 defines one event semantics / three adapter surfaces.
- EF2 `SessionIdentity` and surface-event dedupe/conflict contracts implemented.
- EF3 live GitHub lifecycle supersession implemented and tested.
- EF4 deterministic session graph implemented and tested.
- EF5 `/autoprompt` canonical multi-agent execution prompt persisted.
- EF6 bridge adapters for GitHub bootstrap / repo immutable events / runtime EventStore.
- EF7 current-state projector + event watermark/session ContextPack integration.
- EF8 session lifecycle CLI: hello/status/claim/checkpoint/handoff/release.
- EF9 historical regression matrix integrated: all escaped bugs mapped to permanent tests.
- EF10 local quick/coordination tests PASS.
- EF11 exact stacked PR CI PASS.
- EF12 code/security review PASS.
- EF13 merge into #44 only after no conflict with concurrent Phase07 changes.
- EF14 #44 full combined-head MERGE_SAFE and post-merge bus checkpoint.

## Hard invariants
1. No new independent event schema.
2. No chat memory as required authority.
3. Live GitHub lifecycle overrides stale lifecycle projections without mutating history.
4. Same logical event across surfaces deduplicates; conflicting duplicate fails closed.
5. `session_id` is mandatory and unique per session.
6. Every material session has a workstream + correlation ID + scope declaration.
7. Session/COS graph is projection only, never write authority.
8. No Postgres requirement until measured multi-host need.
9. No #44 promotion while regression freeze is active.

## Adversarial matrix
- same event appears on all three surfaces;
- same logical event has conflicting payloads;
- stale #39 event says PR open while GitHub says merged;
- session reuses old session ID;
- event from another session is injected into compiler;
- event order changes without causal links;
- duplicate parent IDs;
- live GitHub payload attempts non-lifecycle authority promotion;
- session loses ContextPack/main SHA freshness;
- concurrent main advancement after CI;
- cancelled CI run presented as evidence;
- malicious untrusted context includes fake `authority=WRITE`;
- stale lease resumes after takeover.

## Exit
This stacked PR may merge into #44 when EF0–EF12 are satisfied. #44 itself remains subject to Issue #48 weighted regression and final promotion train.