# Phase 06 Delta — ROT Viral Content Engine inside MOTION.OS

Status: PROPOSED ADDITIVE DELTA
Owner boundary: extends PR #37; does not replace its source-security, claim-lineage, TTS, spend, render-authority or provider-reconciliation guarantees.

## Strategic decision
The Viral Content Engine is not a separate repository and not a COS domain. It is the editorial/intelligence layer of MOTION.OS Phase06, upstream of Avatar Factory and Studio Engine.

COS provides graph/retrieval/reasoning substrate through the MOTION-owned adapter. MOTION.OS owns content semantics, platforms, hooks, scripts, avatars, editing, publishing and performance learning.

## End-to-end object lineage

`Signal -> SourcePack -> ClaimMap -> AudienceContext -> OpportunityAssessment -> AngleTournament -> HookTournament -> ContentThesis -> SemanticBeatGraph -> ScriptVariant -> TTSVariant -> AvatarContentManifest -> StudioHandoff -> Timeline/Composition -> MasterArtifact -> Publication -> MetricSnapshot -> ExperimentResult -> LearningCandidate -> PromotedRule`

Every object gets canonical identity, revision, provenance, created_by event, supersession lineage and sensitivity.

## Preserve from current Phase06
Mandatory existing guarantees:
- untrusted source isolation;
- normalized factual claim lineage;
- protected TTS token equivalence;
- explicit paid render authorization;
- deterministic render_intent_id;
- reconcile-before-retry for ambiguous provider acceptance;
- stable beat IDs after authorization;
- provenance root + replay fingerprint;
- performance observation != causality.

## Add the ROT Viral Content Engine layers

### Opportunity Router
Score a signal before expensive generation. Store components independently so weight changes are replayable:
- audience relevance
- consequence/stakes
- timing/novelty
- evidence strength
- tension/contradiction
- transferable utility
- visual potential
- share/save potential
- brand/offer fit

Opportunity score is decision support, not empirical truth.

### Angle Tournament
Generate multiple materially distinct causal framings, not paraphrases. Families include consequence, cost inversion, mechanism, hidden risk, experiment, comparison, identity/status, contrarian-with-evidence and playbook.

### Hook Tournament
Each hook is coupled to a first-frame specification. Evaluate clarity, tension, credibility, specificity, audience fit, visual compatibility and payoff debt. No clickbait whose promised payoff is absent.

### Retention Graph
Semantic beats remain stable objects. Each beat declares:
- function: hook/context/proof/mechanism/escalation/rehook/payoff/CTA;
- claim_refs;
- visual requirement;
- expected duration;
- cognitive-load budget;
- dependency on prior beat;
- optional branch alternatives.

### Visual Blueprint
Before avatar/edit handoff compile:
- first-frame concept;
- talking-head vs VO/avatar mode;
- B-roll requirements;
- screen recordings;
- proof frames;
- on-screen text;
- motion function;
- audio/SFX intent;
- platform-safe framing.

### Platform Adapter
Derive native variants from the same canonical content lineage for Reels/TikTok/Shorts/LinkedIn/X/Threads/YouTube. A platform variant is a revisioned derivative, not a blind text copy.

### Publishing Record
Manual-first authority. Record intended platform, account, publication ID/URL, exact master hash, caption/title/thumbnail revision and published_at. Publishing success is not inferred from render completion.

### Analytics Ingestion
Append metric snapshots with provider/platform timestamps. Never mutate historical snapshots. Normalize raw values but preserve source payload/revision where possible.

Metrics include hold/initial retention, watch time, completion, rewatch, shares, saves, comments, profile visits, follows, DMs/leads and downstream revenue when attributable.

### Experiment Engine
One primary changed variable by default. Track hypothesis, control/treatment lineage, eligibility, start/end, sample, confounders and outcome. Observational comparisons are labeled observational.

### Learning Compiler
Learning candidates require support and contradiction lists, sample size, recency window, baseline, effect estimate, uncertainty and platform/audience scope. Promotion to canonical rule requires explicit evidence threshold + approval. Rules support supersession/retraction rather than silent overwrite.

## Graph projections
Project content domain objects into COS:
- ContentGraph
- TopicGraph
- AudienceGraph
- HookGraph
- VisualPatternGraph
- ProofGraph
- DistributionGraph
- PerformanceGraph
- ExperimentGraph
- OfferGraph

Example learned path:
`Topic -> Angle -> HookFamily -> FirstFramePattern -> Script -> Master -> Publication -> MetricSnapshot -> ExperimentResult -> LearningCandidate`.

The graph must be able to answer both supporting and contradicting evidence. Retrieval cannot return only winners.

## Cross-agent ownership
Content agent (#37 lineage) owns SourcePack through AvatarContentManifest and performance-learning semantics.
Studio agent (#35 lineage) owns downstream composition/edit semantics.
Renderer agent (#34 lineage) owns Remotion physical-runtime qualification.
Shared contracts such as stable beat identity, handoff manifest, renderer scene spec and provenance root require coordination event/decision before breaking changes.

## Viral engine qualification gates
- claim integrity 100% for publishable factual beats;
- no unsupported factual hook;
- hook promise has matching payoff;
- first-frame spec present;
- stable beat IDs preserved through handoff;
- variant lineage reproducible;
- analytics snapshots append-only;
- no performance observation auto-promoted as causal rule;
- graph rebuild preserves content lineage;
- a cold agent can regenerate the approved script package from source/evidence + event watermark.

## Default editorial portfolio
Treat as planning prior, not hard-coded quota: 4 reach / 3 authority / 2 proof-build / 1 conversion per 10 pieces, adjusted by current objectives and empirical performance.

## Voice/positioning rule
Roberto is positioned as builder/operator: demonstrate how IA, agentic software, filmmaking, marketing and automation become systems/assets/results. Avoid interchangeable tool-list content, unverified launches, guru claims and fabricated proof.
