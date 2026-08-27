# Phase 06 V2 — Content Intelligence + Avatar Factory Masterplan

Status: IMPLEMENTING
Owner lane: upstream content strategy, script, speech, avatar generation, telemetry
Downstream boundary: visual/motion editing, overlays, B-roll, sound design, final master
Command surface: `/heygen`

## North Star
Any valid source or idea becomes a 30–45s vertical avatar-led video asset that is understandable by a child and an older non-technical viewer, aligned to a concrete ICP and one primary human driver, engineered for retention, fact-safe, correctly pronounced, reproducibly rendered, and handed to downstream MOTION.OS with stable semantic beat IDs and edit cues. Published performance then calibrates future decisions.

## Full pipeline
SOURCE → SourcePack/ClaimMap → ICP → Pain/Pleasure/Fear/Aspiration → Viral Driver Router → Angle Tournament → Core Transformation Thesis → Hook Tournament → Retention Graph → Script Compiler → Simplicity/Claim/Duration QA → TTS/Pronunciation → Voice Router → Avatar Router → Provider Render → Render Telemetry → Avatar Handoff Manifest → Downstream Edit Graph → Publish → Performance Ingestion → Learning Loop.

## Hard invariants
1. One video = one core transformation.
2. Hook precedes context.
3. New semantic or emotional payload approximately every 3s; >3.5s dead-span is a defect.
4. Primary driver is one of MONEY, LOVE, HEALTH, PERSONAL_GROWTH; secondary drivers are optional.
5. Factual intensity cannot exceed evidence strength.
6. `script_display_text`, `script_spoken_text`, and `script_tts_text` are separate artifacts.
7. Avatar render is an intermediate asset, not the final master.
8. Stable beat IDs survive serialization and downstream editing.
9. Provider capability/config is data, not hard-coded creative logic.
10. Actual render duration and social performance override assumptions.
11. Do not touch downstream motion/renderer ownership without an explicit shared-contract change.

## Internal engines
### E1 Source Intelligence
Build `SourcePack`: source refs, facts, claims, uncertainty, freshness, contradictions, usable angles. Claim authority: VERIFIED, HIGH_CONFIDENCE, INFERRED, OPINION, TIME_SENSITIVE, UNSUPPORTED.

### E2 Audience Intelligence
Explicit situational ICP: sophistication, awareness, jobs-to-be-done, pains, pleasures, fears, aspirations, objections, identity/status pressure, proof preference, language ceiling, novelty tolerance, skepticism, urgency, cost of inaction.

### E3 Viral Driver Router
Primary roots: MONEY, LOVE, HEALTH, PERSONAL_GROWTH. Subdrivers include save_time, make_more, avoid_loss, career_security, mastery, freedom, competence, status, future_proofing, belonging, attraction, safety, energy, longevity.

### E4 Angle Tournament
Generate 5–12 distinct angles and score: ICP relevance, pain intensity, pleasure intensity, novelty, credibility, shareability, visualizability, CTA compatibility, brand fit. No hook generation until an angle wins.

### E5 Hook Tournament
Families: LOSS, GAIN, CONTRADICTION, FUTURE_SHOCK, SOCIAL_PROOF, STATUS, HIDDEN_MECHANISM, EXTREME_SIMPLICITY, CURIOSITY_GAP, DIRECT_CHALLENGE, IDENTITY_THREAT. Score comprehension, emotional fit, specificity, novelty, credibility, open-loop strength, driver fit.

### E6 Retention Graph
Plan semantic beats before prose. Typical 36s structure: 0–3 hook, 3–6 promise, 6–9 mechanism, 9–12 proof, 12–15 escalation, 15–18 contrast, 18–21 CTA/open loop, 21–24 secondary proof, 24–27 consequence, 27–30 reframe, 30–33 moral, 33–36 close. Beat count adapts to content.

### E7 Script Compiler
Compile from graph to three layers: `semantic_script` → `script_spoken_text` → `script_tts_text`. Optimize sentence length, breathing rhythm, emphasis, pause density, vocabulary, clarity and phonetic overrides.

### E8 Avatar Production + Telemetry
Provider-neutral adapter contract. HeyGen is canonical V1 backend. Capture request profile, provider job ID, render status, actual duration, latency, credits when exposed, lip-sync/voice/gesture review, asset reference.

### E9 Downstream Handoff
Emit one manifest containing semantic beats, edit cues, CTA, moral, source provenance, avatar metadata and render telemetry. Downstream visual agent consumes this contract; it must not re-solve audience strategy.

### E10 Performance Learning
Ingest views, 3s/5s retention, average watch time, completion, rewatches, saves, shares, comments, CTA conversion, follows. Attribute to driver, angle, hook family, CTA position, duration, beat density, voice/avatar profile, topic family.

## `/heygen` command contract
Input examples:
- `/heygen <idea>`
- `/heygen <url>`
- `/heygen source=<url> goal=reach`
- `/heygen idea="..." driver=MONEY cta="EDITAR" render=true`

Default behavior:
1. resolve/normalize source;
2. build claim map;
3. infer situational ICP;
4. route primary driver;
5. run angle tournament;
6. run hook tournament;
7. build ~3s retention graph;
8. compile display/spoken/TTS script;
9. validate simplicity, claims, CTA, moral, duration;
10. use canonical HeyGen profile unless overridden;
11. render only when `render=true` or user explicitly says launch/generate;
12. ingest actual duration/status;
13. emit downstream manifest and recovery record.

## Checkpoints
CP00 ownership/collision safety
CP01 source+claim authority
CP02 audience intelligence
CP03 driver/subdriver routing
CP04 angle tournament
CP05 hook tournament
CP06 retention graph
CP07 script compiler
CP08 simplicity/factual QA
CP09 duration model
CP10 speech/TTS normalization
CP11 voice/avatar routing
CP12 provider render
CP13 telemetry ingestion
CP14 downstream handoff
CP15 performance ingestion
CP16 learning/calibration
CP17 batch production
CP18 autonomous content factory

## Promotion gates
V2 structural gate: all contracts serialize; no overlap with downstream-owned code; fixture manifests validate; deterministic QA rejects known long scripts; provider request compilation works; real render telemetry can be ingested.

Production calibration gate: >=30 real productions, >=5 topic families, >=4 viral drivers represented, >=10 scripts across at least 4 families, >=5 real renders for duration calibration, duration MAE <=7%, human clarity >=9, hook >=9, CTA >=8.5, claim violations=0, pronunciation error <=1%, recoverable provider failures, stable beat IDs preserved downstream, performance attribution available.

## Failure policy
If source evidence is insufficient, lower factual intensity or ask for evidence. If duration is outside hard range, rewrite before paid render. If hook/clarity is below threshold, rerun tournament. If provider fails, preserve job metadata and retry only within cost policy. If downstream contract is incompatible, stop at manifest boundary and open a shared-contract delta rather than editing downstream code.
