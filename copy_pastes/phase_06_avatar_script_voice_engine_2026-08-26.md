# Source Archive — Avatar Script & Voice Engine

Interaction date: 2026-08-26
Interaction ID: ROT-2026-08-26-AVATAR-SCRIPT-VOICE-01
Classification: ADDITIVE + REFINEMENT

## Scope
This source defines the upstream content-intelligence layer that generates avatar-led short-form videos before MOTION.OS applies visual editing, motion graphics, overlays, PNG systems, compositing and final master assembly.

## Explicit operating constraints from the user
- Keep this work isolated from the visual/motion-graphics editing agent so agents do not overwrite each other.
- This lane owns script strategy, audience/ICP reasoning, hook architecture, pacing, CTA placement, moral/payoff, voice/TTS preparation, avatar selection and avatar video generation contracts.
- Downstream visual layers remain owned by the editing/motion agent.
- Preferred short-form duration: 30–45 seconds, ideal 35–40 seconds.
- Script language must be extremely simple: understandable by a five-year-old and a 90-year-old.
- Strong hook immediately.
- Introduce meaningful new information roughly every 3 seconds.
- After the hook, quickly establish what the viewer will learn or why they should stay.
- CTA may appear mid-video when strategically useful, not only at the end.
- End with a takeaway/moral and a clear closing beat.
- Route each idea through at least one of four primary viral human drivers: MONEY, LOVE, HEALTH, PERSONAL_GROWTH.
- Identify the specific ICP, pain points, pleasure points, relevant personality/psychographic patterns and desired behavior before writing.
- Script structure must be conditioned by that audience model rather than using a generic template.
- One main idea per video. Complex source material should be compressed into one transformation or one memorable mental model.
- Canonical avatar preference from current HeyGen tests: avatar look `49327c09aed5418383ba330e0daf0304`.
- Canonical private Spanish voice used in tests: `3fbb6707e4414df28da39b6cda40a4e3` (Avatar IV Video - Voice).
- Canonical output target for current avatar line: 1080p, 9:16.
- Current voice speed used in tests: 1.05x.
- English technical terms may require phonetic Spanish spellings in the TTS script when pronunciation quality requires it.
- Generated avatar video is an intermediate asset, not the final edited master.

## Measured test evidence from current conversation
- An earlier API-learning script rendered at ~82.83 s and was too long.
- A systems-complexity script rendered at ~62.82 s and was too long.
- The resulting planning rule is to budget scripts substantially shorter before generation and validate real durations from TTS/render output rather than estimating from prose length alone.

## Proposed upstream pipeline
IDEA / LINK / NEWS / REPO / USER THOUGHT
→ source verification / research as needed
→ ICP + psychographic model
→ viral-driver routing (money/love/health/personal growth)
→ pain/pleasure map
→ one-sentence transformation thesis
→ hook tournament
→ retention-beat plan (~3 s information cadence)
→ script draft
→ simplicity pass
→ claim/risk/fact pass
→ CTA placement strategy
→ moral/payoff close
→ target-duration estimator
→ TTS pronunciation normalization / phonetic rewrite
→ voice configuration
→ avatar/look routing
→ avatar render request
→ duration/status/asset capture
→ handoff manifest to downstream MOTION.OS editor
→ post-performance learning loop.

## Non-goals for this lane
- Motion-graphics design.
- PNG overlay generation.
- Typography animation.
- Visual-system composition.
- B-roll placement.
- Final timeline edit.
- Final color/sound/mastering.
These belong downstream unless explicitly reassigned.

## Required downstream handoff fields
- content_id
- source/provenance
- core_thesis
- viral_driver
- ICP summary
- pain_points
- pleasure_points
- hook
- script_display_text
- script_tts_text
- pronunciation_overrides
- CTA text + timestamp intent
- moral/payoff
- expected_duration_s
- actual_avatar_duration_s
- avatar provider / model / look ID / voice ID
- aspect ratio / resolution
- avatar video asset reference
- semantic beats with approximate timestamps
- edit opportunities / visual cue suggestions (advisory only)
- confidence / claim notes

## Safety / epistemic rule
Do not turn uncertain, spiritual, financial, scientific or news claims into stronger factual claims merely for virality. Separate rhetorical framing from verified fact and preserve provenance when factual accuracy matters.
