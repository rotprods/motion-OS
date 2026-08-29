# MOTION.OS V2 — Decision Ledger

Authority: PROPOSED_V2_CANDIDATE
Each decision is reversible unless explicitly stated. Confidence is based on current evidence, not aesthetics.

## D-V2-001 — One semantic Event Fabric, multiple adapters

Problem: GitHub Bus, repo immutable events and Runtime EventStore can drift into separate truths.
Constraints: preserve historical evidence; support local/single-host today; future multi-host possible.
Alternatives: GitHub-only; filesystem-only; runtime-DB-only; semantic fabric with adapters.
Selected: semantic Event Fabric with adapter/storage projections.
Why: preserves history, dedupes logical events, allows future backend migration without semantic fork.
Rejected: making any transport the domain model.
Tradeoff: additional projector/adapter contracts.
Risk: consumers may reimplement weaker semantics.
Mitigation: one canonical conflict/event library + parity/property tests.
Trigger to reconsider: measured multi-host contention or transaction requirements.
Confidence: HIGH_CONFIDENCE.

## D-V2-002 — COS/graphs are derived reasoning planes, never write authority

Problem: graph richness makes it tempting to use the graph as canonical state.
Selected: event/domain state are authority; COS/unified graphs are deterministic projections.
Why: rebuildability, auditability, no hidden dual-write authority.
Alternative rejected: graph DB as primary authority now.
Trigger: only reconsider if product becomes fundamentally graph-native and transactional graph semantics are measured requirements; still requires migration proof.
Confidence: HIGH_CONFIDENCE.

## D-V2-003 — Preserve single-host authority until distributed need is measured

Problem: architecture could prematurely introduce Postgres/Redis/queues/Kubernetes.
Selected: keep SQLite/reference/local semantics where valid; design adapter interfaces now, deploy distributed backend only on trigger.
Measured triggers: concurrent multi-host writers, background jobs requiring durable distributed scheduling, HA/SaaS requirement, demonstrated single-host bottleneck.
Tradeoff: future migration work.
Risk mitigated: complexity/cost/failure-mode explosion.
Confidence: HIGH_CONFIDENCE.

## D-V2-004 — Current truth is projected, history is immutable

Problem: append-only events/docs inevitably contain obsolete facts.
Selected: never rewrite history; project current state using supersession + live GitHub reconciliation.
Rejected: treating latest-looking document/comment as truth; deleting old evidence.
Tests: stale lifecycle, reopened PR, merged PR still marked active, late event, duplicate event.
Confidence: HIGH_CONFIDENCE.

## D-V2-005 — EvidenceEnvelope as cross-domain promotion primitive

Problem: render, critic, benchmark, claim, provider and release evidence can be correct individually but attached to the wrong artifact/run/source.
Selected concept: all promotion-sensitive evidence chains bind stable identity + source/spec hashes + runtime/provider + run ID + artifact/media hash + evidence revision.
Alternative: domain-specific loose dictionaries only.
Tradeoff: stricter schemas and migrations.
Migration: do not replace active domain contracts blindly; introduce common envelope/adapter only after dependency impact review.
Confidence: HIGH_CONFIDENCE architecture; MEDIUM_CONFIDENCE exact schema until active PR contracts land.

## D-V2-006 — Frame count / time base is visual timing authority

Problem: mux/container duration and derived duration estimates caused false temporal claims.
Selected: decoded frame count + fps/time base for visual authority; mux/audio tails measured separately.
RECONSTRUCT_EXACT requires decoded authority. Approximate modes must name approximation.
Confidence: HIGH_CONFIDENCE based on historical escaped bug.

## D-V2-007 — Full-video semantic/creative evidence gates release

Problem: fixture/mechanical QA can be green while output is creatively weak.
Selected: real recoverable master -> full-video temporal evidence -> creative tournament -> release manifest.
Mechanical/contract evidence cannot self-promote creative authority.
Confidence: HIGH_CONFIDENCE.

## D-V2-008 — Separate product score from promotion-risk score

Problem: a single aggregate score can hide P0 blockers or encourage metric gaming.
Selected: Product North Star quality metrics are independent from Build/Assurance/Authority and risk gates; hard blockers override averages.
Confidence: HIGH_CONFIDENCE.

## D-V2-009 — Session is a first-class graph entity

Problem: cross-chat/cross-agent continuity and collision attribution require more than agent identity.
Selected chain: project -> agent -> session -> workstream -> objective -> correlation.
Every material event/handoff maps to a session.
Confidence: HIGH_CONFIDENCE.

## D-V2-010 — Semantic scope conflict detection outranks path-only conflict detection

Problem: two agents can modify different files while changing the same ADR, root cause, authority or contract.
Selected: path + semantic + authority + root-cause scopes; authority conflict has highest precedence.
Evidence: historical ADR and duplicate-PR collisions.
Confidence: HIGH_CONFIDENCE.

## D-V2-011 — Local-first developer loop; clean-runner promotion authority

Problem: CI cost/noise vs trustworthy merge evidence.
Selected: local verification profiles for iteration; GitHub clean runner and combined-head `MERGE_SAFE` for promotion.
Cancelled/skipped/not-run remain distinct states.
Confidence: HIGH_CONFIDENCE.

## D-V2-012 — GitHub-native main protection is required but external to code

Problem: protocol discipline cannot prevent an authorized direct push.
Selected target: PR-only, required MERGE_SAFE, current-main proof/merge group, no force push/delete, conversation/approval hardening where supported.
Current state: BLOCKED_EXTERNAL until admin API/UI applies it.
Confidence: HIGH_CONFIDENCE need; UNKNOWN exact plan-dependent settings until applied.

## D-V2-013 — Renderer diversity is capability; final master has one assembly authority

Problem: multiple render engines are useful, but audio/color/alpha/timing can diverge.
Selected: renderer adapters produce normalized evidence-bound artifacts; compositor owns one master timeline/audio/color policy.
Tradeoff: normalization work.
Confidence: HIGH_CONFIDENCE.

## D-V2-014 — No aggregate qualification authority without exact ID mapping

Problem: `15 verified primitives`, `25 benchmark briefs`, and similar counters can survive after underlying evidence disappears.
Selected: aggregate metrics are derived only from exact suite/ledger entries. Historical aggregates remain observations with `authority_effect=NONE`.
Confidence: HIGH_CONFIDENCE.

## D-V2-015 — Performance observation never becomes causal rule by score alone

Problem: learning loop can poison strategy from correlation.
Selected: observed performance -> correlation candidate; causal promotion requires controlled/repeated evidence and explicit rule approval.
Confidence: HIGH_CONFIDENCE.

## D-V2-016 — Documentation is a typed projection system

Problem: README/STATE/TASKS/HANDOFF/plan documents drift and acquire accidental authority.
Selected: every V2 canonical document declares authority/scope/owner/source revision/supersession; current human docs are validated against machine state where applicable.
Alternative: manual discipline only.
Confidence: HIGH_CONFIDENCE.

## D-V2-017 — V2 migration is incremental, not greenfield rewrite

Problem: ideal architecture differs from current but many current modules work and have evidence.
Selected: GREENFIELD IDEAL guides topology; migration classifies KEEP/REFINE/REFACTOR/MIGRATE/DEPRECATE/DELETE/DEFER. No rewrite for elegance.
Confidence: HIGH_CONFIDENCE.

## D-V2-018 — Autonomous execution stays disabled until authority fabric is promoted

Problem: a self-driving selector can amplify stale-context or collision defects.
Selected: #68 remains preproduction until #58/Event Fabric is promoted, barrier released and administrative/promotion safeguards are adequate.
Confidence: HIGH_CONFIDENCE.
