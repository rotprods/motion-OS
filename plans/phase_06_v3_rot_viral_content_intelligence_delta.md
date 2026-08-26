# Phase 06 V3 — ROT Viral Content Intelligence Delta

Status: ADDITIVE DELTA / IMPLEMENTATION PLAN
Date: 2026-08-26
Base: Phase 06 V2 Content Intelligence + Avatar Factory
Purpose: absorb the ROT Viral Content Engine into MOTION.OS without replacing or forking the already-hardened Phase06 source/claim/avatar pipeline.

## 0. Decision

V2 remains canonical for:
SourcePack/ClaimMap → ICP → viral driver → angle/hook tournament → retention graph → script/TTS → avatar → provider telemetry → sealed downstream handoff → performance learning.

V3 adds the missing strategic/distribution/experiment layers around that pipeline.

Do not create a separate Content OS repository.
Do not move content logic into COS Graph Engine.
Do not duplicate V2 engines.

## 1. Positioning invariant

The personal-brand content engine should optimize for this identity:

> Roberto does not merely comment on tools. He demonstrates how AI, software agents, filmmaking, marketing and automation become systems, assets and measurable outcomes.

Generic tool-list content, unsupported hype, AI-slop aesthetics, guru claims and evidence-free result claims are penalized.

## 2. New upstream stage — Signal Scout

Input may be:
- user idea/thought
- URL/article/news
- repo/release
- screenshot/video/transcript
- project change/build
- client case
- performance anomaly
- product/offer
- prior post for repurpose

SignalScout emits:
- signal_id
- topic_family
- detected_at
- freshness class
- source/evidence refs
- affected audience
- business relevance
- potential consequence
- proof availability
- time sensitivity
- rumor/confirmed/inference classification

News/current claims must continue through V2 SourcePack/ClaimMap and cannot bypass claim authority.

## 3. Opportunity Score (0–100)

Before Angle Tournament, score whether the signal deserves production.

Default weights:
- audience relevance 18
- consequence/stakes 14
- novelty/timing 12
- evidence/proof availability 12
- tension/contradiction 10
- transferable utility 10
- visual potential 8
- share/save potential 8
- brand/offer fit 8

Thresholds:
- >=70 PRODUCE
- 60–69 REFRAME_OR_BACKLOG
- <60 DROP unless explicit user override

Every score must preserve feature-level rationale. Do not expose one opaque LLM number as evidence.

## 4. Brand / Account Router

Add explicit routing before strategy compilation.

Canonical first-class route:
- Roberto / rot.prods = personal authority layer

Other projects are proof/case sources unless a task explicitly targets their own account.

Router fields:
- account_id
- brand_voice_id
- primary_audience
- goal
- offer_id optional
- CTA policy
- proof bank scopes
- visual system ID
- platform targets

Goal enum:
`REACH | AUTHORITY | PROOF | CONVERSION`

Default when unspecified:
- account: Roberto/rot.prods
- goal: REACH + AUTHORITY blend
- vertical-video duration target: 45s
- primary distribution: Reels/TikTok/Shorts
- derivative distribution: LinkedIn/X/Threads where useful
- no hard-sell CTA unless offer fit is explicit

## 5. Editorial Portfolio Controller

For rolling blocks of 10 personal-brand pieces, target:
- 4 Reach
- 3 Authority
- 2 Proof / Build-in-public
- 1 Conversion

This is a portfolio prior, not a hard quota. The controller should detect skew and recommend the next content class.

## 6. Angle Tournament V3

Preserve V2 scoring and add optional angle features:
- consequence_hidden
- cost_roi
- mechanism
- market_mistake
- own_experiment
- comparison
- identity_status
- playbook
- risk
- opportunity
- paradigm_shift

Preferred structure:
SIGNAL + AUDIENCE AFFECTED + NON-OBVIOUS CONSEQUENCE + PROOF + DECISION

Proof-first angles receive a boost when the proof asset exists. Never invent proof to satisfy the pattern.

## 7. Hook Tournament V3

Preserve existing V2 hook families and add aliases/categories for analytics:
- BREAKING_CONSEQUENCE
- COST_INVERSION
- PROOF_FIRST
- WARNING
- EXPERIMENT
- BEFORE_AFTER
- PREDICTION_CONDITIONAL

Every top hook candidate must be paired with a `first_frame_contract`:
- first-frame asset/ref
- on-screen text 3–7 words target
- evidence/proof status
- visual tension/contrast
- spoken hook alignment

Score hook + first-frame combination, not copy in isolation.

## 8. Dual Scorecard

Separate predicted viral potential from strategic value.

ViralPotential features:
- scroll stop / hook
- first frame
- retention structure
- novelty
- tension
- visuality
- predicted shares/saves

StrategicValue features:
- audience quality
- proof
- utility
- authority
- positioning
- offer fit
- factual robustness

Goal weights:
- REACH: viral .70 / strategic .30
- AUTHORITY: .45 / .55
- CONVERSION: .35 / .65
- default blend: .60 / .40

Model scores are prioritization signals, never empirical performance evidence.

## 9. Visual / Edit Intent Contract

V2 semantic beats already support edit cues. V3 formalizes an upstream intent package for Studio Engine:
- first_frame_contract
- proof_visuals
- required screen recordings
- B-roll intents
- on-screen text per beat
- rehook points
- visual payoff beats
- chart/diagram needs
- protected proof frames
- CTA visual treatment

Rule: result/proof before explanation when truthful and available.

Studio Engine owns final visual execution and may improve composition, but must preserve protected semantic/proof identity.

## 10. Native Platform Adapters

After one canonical semantic content object exists, compile platform-native derivatives rather than copy/paste.

### Reels/TikTok/Shorts
- 9:16
- fast proof/visual hook
- caption supplements video rather than transcribing it
- platform-specific safe-area/title constraints

### LinkedIn
- thesis-first
- evidence/case
- framework
- business implication
- authority close

### X
- compressed claim
- mechanism
- evidence
- implication
- optional compact thread

### Threads
- conversational observation
- tension
- concise consequence
- interaction-friendly close

### Carousel
Adapter calls the existing `/vibecarrusel` contract when appropriate; do not duplicate the visual system inside Phase06.

## 11. Publishing Package

A completed strategy package may contain:
- strategic reading
- audience/account/goal
- opportunity score
- prioritized angles
- hooks A/B/C + first frames
- timed spoken script
- text overlays
- storyboard/edit intent
- rehooks
- caption
- title/thumbnail where relevant
- native platform variants
- CTA
- dual scorecard
- experiment hypothesis
- repurpose tree

Avatar rendering may consume only the canonical video branch of this package.

## 12. Experiment Engine

Add explicit experiment objects rather than loose A/B notes.

Each experiment declares:
- experiment_id
- hypothesis
- primary metric
- guardrail metrics
- baseline cohort/query
- one primary manipulated variable
- variants
- audience/platform constraints
- start/end or sample target
- confounders
- analysis state
- result/effect estimate
- confidence/uncertainty
- decision

Default rule: change one primary variable per controlled content experiment where feasible.

Candidate variables:
- hook family/copy
- first frame
- duration
- proof ordering
- CTA placement
- visual treatment

## 13. Performance Model V3

Extend current Phase06 PerformanceRecord with business/identity signals where available:
- profile_visits
- follows
- saves
- shares
- comments
- DMs
- qualified_leads
- CTA clicks/conversions
- revenue attribution optional
- hold/retention checkpoints platform-specific

Compare content against the creator's own platform/topic/format baseline, not generic benchmarks alone.

Diagnostic rules may produce hypotheses such as:
- high initial hold + low completion → payoff/rhythm/context issue
- high completion + low share/save → weak utility/social currency
- high views + low follows → positioning/identity transfer weak
- high saves + low leads → CTA/offer bridge weak

These remain observations/hypotheses until promoted through the existing causal hygiene stages.

## 14. Repurpose Graph

Every published content object can generate derived nodes:
- short variants
- LinkedIn post
- X post/thread
- Threads adaptation
- carousel
- newsletter/longform seed
- follow-up answering comments
- update when claim changes

Edges retain `DERIVED_FROM`, semantic source revision, platform and transformation policy.

## 15. Personal Knowledge / Proof Bank

The engine may retrieve from domain-scoped evidence such as:
- MOTION.OS build progress
- COS Graph Engine architecture work
- visual AI/filmmaking experiments
- marketing/ads cases
- client/project outcomes
- product/automation builds

A proof asset can support a claim only when provenance/evidence gates permit it. Project membership alone does not prove a performance claim.

## 16. New graph projections

Phase06/07 should expose or derive:
- ContentGraph
- SignalGraph
- TopicGraph
- AudienceGraph
- HookGraph
- VisualPatternGraph
- ProofGraph
- PerformanceGraph
- ExperimentGraph
- DistributionGraph
- OfferGraph

These are MOTION.OS domain projections loaded into COS through the versioned projection boundary; they are not authored directly inside COS.

## 17. Learning queries

The system should eventually answer evidence-backed queries like:
- For AI-video topics on Instagram, which hook+first-frame combinations outperform Roberto's baseline?
- Which angle families generate saves vs follows vs qualified leads?
- Which proof ordering improves completion without reducing hold?
- Which topics attract reach but transfer little authority?
- Which platform derivatives preserve or destroy the original thesis?

Each answer should include sample size, baseline, effect estimate, uncertainty, date window, supporting IDs and contradictory evidence when available.

## 18. Additional gates

V3 blockers:
- no OpportunityScore rationale
- brand/account/goal unresolved
- top hook without first-frame contract for video
- proof-first claim with missing proof
- predicted model score represented as actual performance evidence
- platform variant produced by raw copy/paste when native adapter exists
- experiment changes multiple uncontrolled primary variables while claiming causality
- performance rule promoted from correlation alone
- business metric claimed without provenance

## 19. Implementation sequence

V3.0 schemas only:
- viral opportunity
- content experiment
- publishing package delta

V3.1 SignalScout + OpportunityScorer
V3.2 Account/Goal Router + editorial portfolio state
V3.3 first-frame + dual-score extensions to tournaments
V3.4 publishing package + Studio edit intent
V3.5 platform adapters
V3.6 experiment engine + own-baseline analytics
V3.7 performance/repurpose graph projections
V3.8 30+ real-content calibration and controlled experiments

## 20. Definition of Done

V3 is VERIFIED only when an input signal can be fact-checked, scored for opportunity, routed to the right account/audience/goal, transformed through existing V2 strategy/script/avatar contracts, handed to Studio with first-frame/proof/edit intent, distributed into native platform variants, linked to a controlled experiment/performance record, and later used as evidence in a versioned learning graph without converting correlation into causality.
