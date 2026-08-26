# Phase 06 — Define Goal + Checkpoints

## Goal
Build a production-grade upstream **Avatar Script & Voice Engine** that converts a raw idea/source into a validated 30–45s avatar-video package with predictable duration, simple language, strong retention architecture, correct TTS pronunciation, configurable avatar/voice routing, provenance, and a graph-ready semantic handoff for downstream MOTION.OS editing.

## North-star acceptance
A new agent can take a raw idea and produce, without conversational context:
1. an explicit ICP and primary viral driver (MONEY / LOVE / HEALTH / PERSONAL_GROWTH),
2. one core transformation,
3. a scored hook set and selected hook,
4. semantic beats with stable IDs and ~3s information cadence,
5. display script + provider-safe TTS script,
6. CTA + moral/payoff,
7. a duration estimate inside 30–45s (preferred 35–40s),
8. a configurable avatar render request,
9. render telemetry ingestion,
10. a validated handoff manifest consumed downstream by editing/motion agents.

## Hard boundaries
This phase owns content intelligence, narration, voice/avatar generation and upstream semantic metadata. It does not own motion graphics, overlays, B-roll placement, visual grammar, timeline compositing, grade or final export.

## Checkpoints

### CP0 — Collision-safe persistence
PASS when source, plan, goal/checkpoints and graph exist on an isolated branch and no downstream visual/render file is modified.

### CP1 — Contract authority
PASS when a JSON Schema validates a real manifest and requires source refs, claim notes, semantic beat IDs, display/TTS separation, CTA, moral, avatar profile and render telemetry fields.

### CP2 — Configurable production profile
PASS when HeyGen avatar/voice/output defaults live in config rather than script logic.

### CP3 — Deterministic script QA
PASS when code rejects:
- target duration outside 30–45s,
- estimated duration outside 30–45s,
- duplicate/malformed beat IDs,
- missing CTA,
- missing moral/payoff,
- missing provenance/claim notes,
- display/TTS contamination rules where applicable.

### CP4 — Duration calibration
PASS when estimator supports per-profile words/sec, punctuation pause cost and phonetic expansion; known 62.8245s and 82.8343s renders are retained as negative calibration evidence.

### CP5 — TTS normalization
PASS when pronunciation overrides produce provider-safe speech text without changing canonical display text.

### CP6 — Strategy contracts
PASS when the manifest can encode ICP, pain/pleasure, primary/secondary viral driver, hook candidates/scores, core thesis and semantic retention beats.

### CP7 — Avatar request + telemetry
PASS when code can build a provider request from profile + manifest and ingest provider job/status/actual duration/asset ref without coupling to the downstream renderer.

### CP8 — Downstream graph handoff
PASS when each semantic beat has stable ID, intended function and optional downstream edit cues; serialized round-trip preserves IDs.

### CP9 — Test gate
PASS when Phase 06 unit/contract tests pass locally/CI and repository health remains green.

### CP10 — Empirical calibration
PASS after >=10 scripts / >=4 topic families / >=5 actual avatar renders, mean duration prediction error <=10%, and human scores >=8.5 for hook, clarity, cadence, CTA and payoff.

## Execution state
- CP0: IMPLEMENTED
- CP1: IMPLEMENTED
- CP2: IMPLEMENTED
- CP3: IMPLEMENTED
- CP4: IMPLEMENTED_V1; empirical recalibration open
- CP5: IMPLEMENTED
- CP6: IMPLEMENTED_CONTRACT
- CP7: IMPLEMENTED_ADAPTER_CONTRACT; live provider transport remains external
- CP8: IMPLEMENTED
- CP9: CODE_READY; CI evidence pending branch run
- CP10: OPEN — requires production data

## Promotion rule
Do not mark Phase 06 VERIFIED until CP9 has authoritative CI evidence. Do not mark it empirically calibrated until CP10 passes with real render/performance data.
