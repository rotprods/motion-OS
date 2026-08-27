# Phase 06 — Avatar Script & Voice Engine

Status: PROPOSED
Interaction: ROT-2026-08-26-AVATAR-SCRIPT-VOICE-01
Owner lane: upstream content intelligence + avatar generation
Downstream owner lane: MOTION.OS visual/motion editing agent

## Mission
Convert a raw idea, link, repository, news item or user thought into a validated, short-form avatar video asset plus a structured handoff manifest that downstream MOTION.OS editing agents can transform into the final master without re-solving audience strategy, narration, voice or avatar generation.

## Boundary contract
Phase 06 OWNS:
- source understanding / fact framing
- ICP definition
- psychographics relevant to message framing
- pain/pleasure model
- viral-driver routing
- thesis extraction
- hook generation/ranking
- retention pacing
- script writing
- simplicity transformation
- CTA strategy
- payoff/moral
- duration budget
- pronunciation/TTS normalization
- voice config
- avatar selection/routing
- avatar render request metadata
- render duration/status/result capture
- semantic beat manifest
- performance-learning inputs

Phase 06 DOES NOT OWN by default:
- motion-graphics design
- overlay systems
- PNG assets
- animated typography
- visual style grammar
- B-roll selection/placement
- timeline compositing
- final sound design
- final grade/export

Those remain downstream and should consume Phase 06's handoff contract.

## Design principles
1. ONE VIDEO = ONE CORE TRANSFORMATION.
2. Simplicity is a hard gate. A child and an older non-technical viewer should understand the main point.
3. Hook before context.
4. New meaningful information approximately every 3 seconds.
5. Every beat must do at least one job: increase curiosity, deliver proof, intensify pain, expose pleasure, reduce confusion, invite interaction, or land the transformation.
6. At least one primary human driver is selected: MONEY, LOVE, HEALTH, PERSONAL_GROWTH.
7. ICP is explicit, never implied generically.
8. Pain and pleasure are both mapped; scripts may lead with either depending on audience and topic.
9. CTA position is strategic. Mid-roll CTA is allowed if curiosity or value has already been earned.
10. End on a memorable moral/payoff, not on a loose CTA alone.
11. Factual intensity may not exceed evidence strength.
12. Avatar generation is an intermediate production stage.
13. Actual render duration overrides estimates and feeds calibration memory.

## Graph
```text
SOURCE
  ↓
SOURCE NORMALIZATION / CLAIM MAP
  ↓
ICP MODEL
  ├─ pains
  ├─ pleasures
  ├─ objections
  ├─ sophistication
  └─ psychographic fit
  ↓
VIRAL DRIVER ROUTER
  ├─ MONEY
  ├─ LOVE
  ├─ HEALTH
  └─ PERSONAL_GROWTH
  ↓
CORE TRANSFORMATION THESIS
  ↓
HOOK TOURNAMENT
  ↓
RETENTION BEAT GRAPH (~3s cadence)
  ├─ hook
  ├─ promise / intro
  ├─ proof / mechanism
  ├─ escalation / contrast
  ├─ CTA opportunity
  ├─ payoff
  └─ moral / close
  ↓
SCRIPT DRAFT
  ↓
SIMPLICITY + CLAIM + DURATION GATES
  ↓
TTS NORMALIZATION
  ├─ punctuation/prosody
  ├─ pronunciation overrides
  └─ phonetic rewrite when needed
  ↓
VOICE ROUTER
  ↓
AVATAR ROUTER
  ↓
AVATAR RENDER
  ↓
RENDER TELEMETRY
  ├─ actual duration
  ├─ provider status
  ├─ asset ref
  └─ cost/credits when available
  ↓
AVATAR HANDOFF MANIFEST
  ↓
DOWNSTREAM EDIT / MOTION / OVERLAYS / MASTER
  ↓
PERFORMANCE METRICS
  ↺ learning/calibration
```

## Script contract
Target duration:
- hard range: 30–45 s
- preferred: 35–40 s

The engine MUST NOT rely only on a fixed word count. It should use:
1. historical words/sec for the selected voice,
2. punctuation/pause density,
3. phonetic expansion cost,
4. real rendered duration feedback.

Initial calibration evidence:
- API test: 82.8343 s — reject for target format.
- complex systems test: 62.8245 s — reject for target format.

## Retention-beat model
For a 36-second target, design ~12 information beats.
Each beat should be addressable by stable ID, e.g.:
- B00_HOOK
- B01_PROMISE
- B02_PROBLEM
- B03_MECHANISM
- B04_PROOF
- B05_CONTRAST
- B06_ESCALATION
- B07_CTA
- B08_SECONDARY_PROOF
- B09_REFRAME
- B10_MORAL
- B11_CLOSE

Beat count is adaptive, but long stretches with no new semantic payload are a QA defect.

## Hook tournament
Generate multiple hooks across distinct mechanisms:
- loss/risk
- gain/opportunity
- contradiction
- forbidden/hidden mechanism
- extreme simplicity
- social proof / scale
- future shock
- identity/status

Score for:
- immediate comprehension
- emotional relevance to ICP
- specificity
- novelty
- credibility
- open-loop strength
- fit with selected viral driver

## ICP schema
Minimum fields:
- audience_label
- domain_sophistication: novice/intermediate/expert/mixed
- age_band if relevant
- jobs_to_be_done
- pains[]
- pleasures[]
- fears[]
- aspirations[]
- objections[]
- identity/status concerns[]
- psychographic patterns[]
- preferred proof style
- language complexity ceiling

Psychographic use must remain practical and non-diagnostic.

## CTA strategy
CTA types:
- comment keyword for resource delivery
- save/bookmark
- follow for continuation
- question for discussion
- share/tag

Placement modes:
- MID_VALUE: after first substantial proof
- PRE_PAYOFF: before final transformation
- END: after moral

Default for lead-magnet/resource videos: MID_VALUE or PRE_PAYOFF, not necessarily final sentence.

## Moral/payoff rule
Final beat should answer one of:
- what changes in how the viewer should think?
- what should they do differently?
- what identity shift matters?
- what is the simplest truth to remember?

## TTS / pronunciation layer
Maintain separate fields:
- `script_display_text`: correct human-readable Spanish.
- `script_tts_text`: provider-optimized speech text.
- `pronunciation_overrides`: structured mapping.

Example:
```json
{
  "API": "éi-pi-ái",
  "REST": "réest",
  "WebSockets": "uéb-sókets"
}
```
Do not contaminate canonical displayed captions with phonetic spellings.

## Current HeyGen production profile
Provider: HeyGen
Canonical avatar look: `49327c09aed5418383ba330e0daf0304`
Canonical voice: `3fbb6707e4414df28da39b6cda40a4e3`
Voice name: Avatar IV Video - Voice
Output: 1080p, 9:16, mp4
Current speed: 1.05x
Expressiveness: medium unless topic requires another mode

This profile is TIME_SENSITIVE_CAPABILITY metadata and may change after testing.

## Handoff schema draft
```json
{
  "content_id": "...",
  "source_refs": [],
  "core_thesis": "...",
  "viral_driver": "MONEY",
  "secondary_driver": "PERSONAL_GROWTH",
  "icp": {},
  "pain_points": [],
  "pleasure_points": [],
  "hook": "...",
  "script_display_text": "...",
  "script_tts_text": "...",
  "pronunciation_overrides": {},
  "semantic_beats": [],
  "cta": {"text":"...","placement":"MID_VALUE","target_beat_id":"B07_CTA"},
  "moral": "...",
  "duration_target_s": 38,
  "duration_estimate_s": null,
  "avatar": {
    "provider": "heygen",
    "look_id": "49327c09aed5418383ba330e0daf0304",
    "voice_id": "3fbb6707e4414df28da39b6cda40a4e3",
    "resolution": "1080p",
    "aspect_ratio": "9:16",
    "speed": 1.05
  },
  "render": {
    "provider_job_id": null,
    "status": null,
    "actual_duration_s": null,
    "asset_ref": null
  },
  "claim_notes": [],
  "downstream_edit_cues": []
}
```

## Agent-collision protocol
This phase is developed on a dedicated branch/PR.
Do not modify downstream visual/motion modules owned by the active Studio Engine agent unless a shared contract change is required.
Shared changes must be minimal and contract-only.

Recommended ownership:
- Phase 06 changes: `copy_pastes/phase_06_*`, `plans/phase_06_*`, future `schemas/avatar_content_manifest.schema.json`, future `src/content/*`, future `src/avatar/*`, future `config/avatar_profiles.yaml`, future `tests/test_phase06_*`.
- Existing motion/render/visual code remains untouched in the first implementation wave.

## Implementation waves
### Wave A — persistence and contracts
- preserve source
- plan
- graph
- schema
- config profile
- fixtures from real scripts/renders

### Wave B — deterministic script QA
- word/pause estimator
- simplicity heuristics
- required-beat validator
- CTA/payoff validator
- claim/provenance hooks

### Wave C — planning intelligence
- ICP model contract
- viral-driver router
- hook tournament contract
- retention beat planner

### Wave D — speech adapter
- display/TTS separation
- pronunciation dictionary
- provider-specific TTS normalization

### Wave E — avatar provider adapter
- HeyGen request builder
- render status/result ingestion
- duration telemetry
- cost telemetry where available

### Wave F — downstream handoff
- manifest serialization
- import into editing graph as upstream semantic source
- beat IDs become stable anchors for overlays/motion/B-roll

### Wave G — learning loop
- ingest actual duration
- ingest final content performance when available
- calibrate hook families, CTA position and voice duration model

## Validation gates
P0 for this phase before promotion:
- no collision with downstream agent-owned files
- schema validates real example manifests
- target-duration validator catches known 62s/82s failures
- display text and TTS text remain separate
- stable beat IDs survive serialization
- avatar provider profile is configurable, not hard-coded in script logic
- factual/claim provenance field cannot be silently dropped

P1:
- >=10 scripts across at least 4 topic families
- >=5 actual avatar renders with duration telemetry
- mean duration error <=10% after calibration
- human review: hook, clarity, cadence, CTA, payoff each >=8.5/10

## Plan delta
```yaml
interaction_id: ROT-2026-08-26-AVATAR-SCRIPT-VOICE-01
source_paths:
  - copy_pastes/phase_06_avatar_script_voice_engine_2026-08-26.md
phase: phase_06
changes:
  assumptions:
    - avatar-led content is an upstream intermediate asset, not the final master
    - scripts target 30-45s, preferably 35-40s
    - audience/driver/retention modeling must precede copy generation
  graph:
    - add content-strategy-to-avatar-render upstream subgraph
    - hand off stable semantic beat IDs to downstream editing graph
  tasks:
    - add Phase 06 schema/config/validators/provider adapter
  gates:
    - duration calibration
    - simplicity
    - beat cadence
    - CTA/payoff
    - claim provenance
  schemas:
    - proposed avatar_content_manifest.schema.json
  configs:
    - proposed avatar_profiles.yaml
expected_impact: higher retention, predictable avatar duration, reusable upstream/downstream contract, less agent collision
evidence_required: real script fixtures, real HeyGen durations, human creative scoring, downstream manifest consumption
rollback_condition: if Phase 06 duplicates existing Studio Engine ownership or materially increases coordination cost without improving content metrics
```
