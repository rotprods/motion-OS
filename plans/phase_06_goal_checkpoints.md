# Phase 06 — Define Goal + Checkpoints

## Goal
Build a production-grade upstream **Content Intelligence + Avatar Factory** that converts a raw idea/source into a validated 30–45s avatar-video package with predictable duration, simple language, strong retention architecture, correct TTS pronunciation, configurable avatar/voice routing, provenance, spend safety, idempotency, provider-state integrity and a graph-ready semantic handoff for downstream MOTION.OS editing.

## North-star acceptance
A new agent can take a raw idea and produce, without conversational context:
1. an isolated SourcePack marked `UNTRUSTED_SOURCE_DATA`,
2. explicit claim lineage and freshness,
3. an explicit ICP and primary viral driver (MONEY / LOVE / HEALTH / PERSONAL_GROWTH),
4. one core transformation,
5. a scored angle set and hook set,
6. semantic beats with stable IDs and ~3s attention-refresh cadence,
7. display/spoken/TTS scripts with protected-token integrity,
8. CTA + moral/payoff,
9. a duration estimate inside 30–45s (preferred 35–40s),
10. an explicit spend-authorized, idempotent avatar render intent,
11. validated provider telemetry,
12. a sealed, provenance-chained and replayable handoff manifest consumed downstream by editing/motion agents,
13. reconcilable persistence replicas,
14. transactional worker authority with stale-writer rejection,
15. performance observations that cannot become causal rules without repeated/controlled evidence.

## Hard boundaries
This phase owns content intelligence, narration, voice/avatar generation and upstream semantic metadata. It does not own motion graphics, overlays, B-roll placement, visual grammar, timeline compositing, grade or final export.

## Checkpoints
### CP0 — Collision-safe persistence
PASS when source, plan, goal/checkpoints and graph exist on an isolated branch and no downstream visual/render file is modified.

### CP1 — Contract authority
PASS when JSON Schemas validate real manifests and require provenance, stable beats, script separation, CTA, moral, avatar/render fields and explicit schema versions.

### CP2 — Source trust boundary
PASS when raw URL/repo/article content is classified as untrusted data, instruction-like source text is detected, obvious secrets/PII are redacted/quarantined, and raw source cannot directly control privileged execution.

### CP3 — Claim lineage
PASS when every factual semantic beat references known claim IDs; unsupported claims cannot be delivered as fact; time-sensitive claims expose freshness/reverification requirements.

### CP4 — Strategy contracts
PASS when the manifest can encode situational ICP, pain/pleasure/fear/aspiration, primary/secondary driver, angles/hooks/scores, core thesis and semantic retention beats.

### CP5 — Attention/cognitive QA
PASS when ~3s cadence is modeled as attention refresh rather than forced novelty and sustained cognitive overload is detected.

### CP6 — Duration calibration
PASS when estimator supports per-profile words/sec, punctuation pause cost and actual-render recalibration. Production target eventually reaches normalized error <=7%.

### CP7 — TTS semantic integrity
PASS when display and TTS text remain separate and protected tokens (years, numbers, percentages, currency, URLs, versions/proper tokens) cannot silently change.

### CP8 — Configurable production profile
PASS when avatar/voice/output defaults live in config rather than script logic and time-sensitive provider capability can be revalidated.

### CP9 — Spend authorization + idempotency
PASS when every paid render requires explicit authorization, a deterministic render intent ID, preflight success, budget/concurrency checks, bounded retry, reconcile-before-retry semantics and durable authority state that rejects duplicate submissions.

### CP10 — Provider request + telemetry integrity
PASS when provider payload values are allowlisted and provider result status/duration/job IDs/asset URLs are validated before canonical ingestion.

### CP11 — Downstream graph handoff integrity
PASS when every semantic beat has stable ID, intended function and optional edit cues; IDs become immutable anchors after render authorization; deterministic manifest seal/replay fingerprint + provenance root detect semantic mutation before downstream execution.

### CP12 — Performance causal hygiene
PASS when performance begins as observation/correlation, confounders are stored, automatic rule promotion is impossible, controlled-test evidence precedes explicit canonical-rule approval.

### CP13 — Schema/persistence resilience
PASS when Phase 06 records are explicitly versioned, migration steps are deterministic/fail-closed for future versions, and GitHub/Drive/Library replicas can be compared by revision/hash without automatically overwriting conflicts.

### CP14 — Test + fuzz gate
PASS when unit/contract/adversarial/resilience/authority tests pass in authoritative CI, malformed manifests/provider payloads are fuzzed, timeout-after-acceptance and concurrent render scenarios are simulated, and repo health stays green.

### CP15 — Empirical calibration
PASS after >=30 real productions, >=5 topic families, all four viral drivers represented, duration error <=7%, human clarity >=9, hook >=9, CTA >=8.5, claim violations=0 and pronunciation error <=1%.

### CP16 — Worker authority / fencing
PASS when concurrent workers coordinate through a transactional store, leases have bounded lifetime, each lease turnover increments a fencing token, stale writers are rejected, and worker-crash recovery is demonstrated. Single-host SQLite evidence may satisfy V1; multi-host production requires a real network transactional database adapter and concurrent-host proof.

### CP17 — End-to-end provenance
PASS when a deterministic root commits source identity → claims → semantic beats → scripts → avatar profile, `/heygen` emits it in dry-run/authorized flows, and downstream validates both provenance root and replay fingerprint before editing.

## Execution state
- CP0: IMPLEMENTED
- CP1: IMPLEMENTED_V2 — explicit schema version/migration registry added; schema files still need version assertions in latest green CI
- CP2: IMPLEMENTED_V1 — scanner/redaction/quarantine primitives added; privileged-prompt integration still needs runtime proof
- CP3: IMPLEMENTED_V1 — deterministic claim IDs + factual beat lineage gate
- CP4: IMPLEMENTED_CONTRACT
- CP5: IMPLEMENTED_V1 — attention refresh + cognitive-load warnings
- CP6: IMPLEMENTED_V1 — one real successful calibration render; corpus scale open
- CP7: IMPLEMENTED_V1 — protected-token gate; broader Spanish number/proper-noun coverage open
- CP8: IMPLEMENTED
- CP9: IMPLEMENTED_V3 — deterministic intent + spend gate + retry state machine + hash-chain ledger + transactional SQLite authority; multi-host DB adapter remains open
- CP10: IMPLEMENTED_V1 — provider telemetry/payload validation
- CP11: IMPLEMENTED_V3 — stable beats + manifest integrity seal + replay fingerprint + provenance root; downstream runtime verification remains open
- CP12: IMPLEMENTED_V1 — causal stages + explicit promotion approval
- CP13: IMPLEMENTED_V1 — migration registry + GitHub-canonical replica digest/reconciliation primitives; real Drive/Library revision automation remains open
- CP14: CI_EVIDENCE_PARTIAL — authoritative CI executed 108 tests on an earlier head: 106 passed, 1 failed, 1 skipped; failure was traced to a stale fixture-state assertion and corrected. New fuzz/authority tests added; latest-head green run still required.
- CP15: OPEN — requires production data
- CP16: IMPLEMENTED_V1_SINGLE_HOST — SQLite transactional store + leases/fencing/stale-writer rejection tests written; multi-host Postgres-class adapter and runtime proof open
- CP17: IMPLEMENTED_V1 — source-to-avatar provenance chain + `/heygen` integration + handoff contract implemented; downstream enforcement open

## CI incident resolved in code
Authoritative GitHub Actions run `32992848085` reached the full pytest step and reported exactly one Phase 06 failure: `test_render_telemetry_ingestion_is_non_destructive` assumed the real OpenMontage fixture still had `actual_duration_s=None`. The fixture had intentionally been calibrated to `42.6318`. The test now snapshots the original value and verifies non-destructive behavior without coupling to fixture history.

## Promotion rule
Do not mark Phase 06 VERIFIED until CP14 has a fresh authoritative green CI run for the latest head. Do not call CP16 multi-host production authority until a network transactional database implementation and concurrent-host evidence exist. Do not mark the system empirically calibrated until CP15 passes. Any P0 violation in source isolation, claim lineage, spend safety, TTS protected-token integrity, manifest/provenance integrity or provider-state reconciliation blocks promotion regardless of aggregate score.
