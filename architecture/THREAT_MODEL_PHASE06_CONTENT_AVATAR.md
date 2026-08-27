# Phase 06 — Content + Avatar Threat Model

Status: HARDENING BASELINE
Date: 2026-08-26
Scope: `/heygen` upstream content intelligence, TTS, avatar render, telemetry, persistence and learning loop.

## Security properties
1. Untrusted source content can inform facts but cannot alter system instructions, tools, spend policy, persistence rules or provider credentials.
2. Every publishable factual proposition must be traceable to one or more normalized claim IDs with evidence strength and freshness.
3. Rendering is fail-closed: no provider spend without explicit authorization, a passing preflight and an idempotency key.
4. Retry behavior cannot silently create duplicate paid renders.
5. Display text and TTS text may differ phonetically but must remain semantically equivalent for protected tokens: numbers, dates, percentages, currencies, model names, URLs and proper nouns.
6. Provider responses are untrusted external state and must be validated before mutating canonical manifests.
7. Performance data creates hypotheses, never immediate causal rules.
8. Stable semantic beat IDs are immutable downstream anchors once a render intent is authorized.
9. PII, secrets and auth material must not enter source packs, scripts, telemetry or learning datasets unless explicitly required and separately controlled.
10. The system must support ABSTAIN/QUARANTINE, not only PASS/FAIL.

## Assets
- provider credits and billing limits
- private avatar identity / voice clone IDs
- brand reputation and factual trust
- source provenance and claim lineage
- scripts and rendered assets
- GitHub/Drive/Library persistence
- performance-learning memory
- downstream edit contracts

## Trust boundaries
```text
WEB / REPO / USER SOURCE (UNTRUSTED)
        ↓
SOURCE ISOLATION
        ↓
NORMALIZED CLAIMS + EVIDENCE
        ↓
CONTENT PLANNER / SCRIPT COMPILER
        ↓
PREFLIGHT + SPEND GATE
        ↓
HEYGEN (EXTERNAL PROVIDER)
        ↓
TELEMETRY VALIDATION
        ↓
DOWNSTREAM EDIT GRAPH
        ↓
PUBLISHED PERFORMANCE DATA (UNTRUSTED/CONFOUNDED)
        ↓
HYPOTHESIS LEARNING
```

## Principal threats
### T1 Prompt injection in source
Attack: README/article tells agent to ignore policy, reveal secrets, alter CTA or render.
Control: source is data-only; detect instruction-like strings; never concatenate raw source into privileged prompts; planner consumes normalized claim objects.

### T2 Evidence laundering
Attack: unsupported inference becomes a confident spoken fact.
Control: proposition→claim lineage; publishable factual beats require claim IDs; evidence strength may cap wording intensity; stale claims require revalidation.

### T3 Duplicate provider spend
Attack: timeout after provider acceptance causes retry and duplicate paid render.
Control: deterministic render intent ID + state machine + reconcile-before-retry.

### T4 Spend amplification
Attack: loop or concurrent agents exhaust monthly credits.
Control: per-render, daily and concurrent budget limits; explicit authorization; bounded retries.

### T5 TTS semantic corruption
Attack: phonetic rewrite changes 1.8 to 18, 2029 to 2019, or a proper noun to another entity.
Control: protected-token extraction and equivalence gate.

### T6 Malformed provider telemetry
Attack: impossible status/duration/URL mutates canonical record.
Control: validate allowed states, IDs, duration bounds and URL schemes.

### T7 Concurrent content identity collision
Attack: two agents create same content ID/render intent.
Control: content fingerprint + render intent fingerprint + canonical lock/ledger in execution environment.

### T8 Learning-loop confounding
Attack: topic virality/time/platform distribution is learned as hook causality.
Control: observations become candidate hypotheses; promotion requires repeated evidence or controlled tests.

### T9 Persistence divergence
Attack: GitHub, Drive and Library disagree on command semantics.
Control: GitHub software/control truth; replicas include authority/version metadata and are reconciled, not merged blindly.

### T10 PII/secrets propagation
Attack: source contains tokens, emails, keys, private identifiers; script or logs reproduce them.
Control: secret/PII scan before SourcePack persistence and before script/render.

## Required gates
G0 schema
G1 source isolation
G2 claim lineage
G3 strategy/driver
G4 hook credibility
G5 attention cadence + cognitive load
G6 simplicity
G7 TTS semantic integrity
G8 duration
G9 spend authorization + idempotency
G10 provider payload
G11 telemetry integrity
G12 render quality
G13 downstream beat integrity
G14 human creative critic
G15 learning causal hygiene

Each gate returns `PASS | WARN | FAIL | ABSTAIN | QUARANTINE` plus evidence.

## Promotion blockers
- raw source can directly influence privileged instructions
- factual spoken propositions without claim lineage
- provider submission without explicit spend authorization
- retries without idempotency/reconciliation
- protected TTS token mutation
- unbounded retries/concurrency
- performance observations automatically promoted to canonical rules
- authoritative CI absent
