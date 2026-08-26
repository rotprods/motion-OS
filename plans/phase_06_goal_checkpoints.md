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
- CP1: IMPLEMENTED_V2 — explicit schema version/migration registry added and exercised under latest-head CI
- CP2: IMPLEMENTED_V1 — scanner/redaction/quarantine primitives added; privileged-prompt integration still needs live runtime proof
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
- CP14: PASS_LATEST_HEAD — authoritative CI run `32993729448` on head `fe9633aaaf3d445c0e89ff19aed7e6737f173d22`: Python 3.11 PASS, Python 3.12 PASS, analysis-runtime PASS, compileall PASS, full pytest PASS, repo-health PASS. Dedicated Repo Health workflow also PASS.
- CP15: OPEN — requires production data
- CP16: IMPLEMENTED_V1_SINGLE_HOST_CI — SQLite transactional store + durable fencing generations + stale-writer rejection are covered by latest-head green CI; live worker-crash recovery and multi-host Postgres-class authority remain open
- CP17: IMPLEMENTED_V1_CI — source-to-avatar provenance chain + `/heygen` integration + handoff contract pass latest-head CI; downstream enforcement remains open

## CI incidents converted into invariants
### Incident 1 — fixture history coupling
Run `32992848085` exposed a stale test assumption: `test_render_telemetry_ingestion_is_non_destructive` assumed the calibrated OpenMontage fixture still had `actual_duration_s=None`, although real provider calibration correctly persisted `42.6318`. The test was corrected to snapshot the fixture's original value and verify non-destructive behavior independent of fixture history.

### Incident 2 — fencing token reset
Run `32993357902` executed 114 tests and caught a real authority bug: after lease release, the implementation deleted the only persisted fencing token, so the next owner received token `1` again. This broke the monotonic fencing invariant and could allow a stale worker to become indistinguishable from a later generation. The fix separates durable `lease_generations` from active `leases`; release removes ownership but never generation history. Latest-head run `32993729448` proves the regression test now passes on Python 3.11 and 3.12.

## Promotion rule
CP14 now has authoritative latest-head green evidence. Phase 06 as a whole is still not empirically VERIFIED/production-complete: do not call CP16 multi-host production authority until a network transactional database implementation and concurrent-host evidence exist, do not call CP17 downstream-enforced until the editing runtime verifies provenance/seal before execution, and do not mark the system empirically calibrated until CP15 passes. Any P0 violation in source isolation, claim lineage, spend safety, TTS protected-token integrity, manifest/provenance integrity or provider-state reconciliation blocks promotion regardless of aggregate score.
