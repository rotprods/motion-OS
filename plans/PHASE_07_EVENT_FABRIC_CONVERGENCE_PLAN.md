# Phase07 — Post-Merge Event Fabric Convergence Plan

Status: IMPLEMENTING
Parent regression: #48
Canonical bus: #39
Base: `main@080dfd5c16bc06100edd716eadc770530dc47af2`

## Why this exists
Phase07 #44 merged while a regression freeze event was already posted to #39. The code merge itself was green, but the incident demonstrates that coordination is not reliable until every irreversible action consumes the newest event watermark + live GitHub state. This plan closes that systemic gap.

## Checkpoints
- EF0 freeze event exists on #39 and historical race documented.
- EF1 ADR-008 defines one semantic fabric across GitHub/repo/runtime surfaces.
- EF2 session identity + surface dedupe/conflict implemented.
- EF3 live GitHub lifecycle supersession implemented.
- EF4 deterministic session graph implemented.
- EF5 `/autoprompt` persisted.
- EF6 adapters ingest bootstrap/repo/runtime records into one logical event identity.
- EF7 current-state projector binds live main SHA + event watermark + session ContextPack.
- EF8 irreversible-action preflight requires fresh watermark/live GitHub reconciliation.
- EF9 session CLI supports hello/status/claim/checkpoint/handoff/release.
- EF10 historical escaped-bug matrix is permanent regression suite.
- EF11 local tests pass.
- EF12 exact PR MERGE_SAFE passes against current main.
- EF13 code/security review passes.
- EF14 merge one PR, post-merge main verify, emit immutable pr.merged/main.verified event.

## Hard invariants
No independent event schema; no required chat-memory fact; same logical event deduplicates; conflicting duplicate fails closed; session_id unique; stale lifecycle cannot override live GitHub; cancelled CI is not evidence; session/COS graph cannot write authority; Postgres remains deferred.

## Adversarial gate
Test stale bus vs merged PR, duplicate/conflicting events across surfaces, cross-session injection, duplicate event/parent IDs, event watermark staleness, concurrent main advancement after proof, malicious authority fields, stale lease resurrection, and irreversible action attempted from stale context.

## Exit
Issue #48 may consider Event Bus convergence closed when EF0–EF14 are backed by exact evidence and a zero-context agent can derive the same current state and next safe action without chat history.