# `/heygen` — MOTION.OS Content → Avatar Pipeline

`/heygen` is the canonical command surface for Phase 06.

## Invocation
`/heygen <idea|url|repo|news|script>`

Optional parameters:
- `goal=reach|authority|conversion`
- `driver=MONEY|LOVE|HEALTH|PERSONAL_GROWTH`
- `duration=30|35|40|45`
- `cta=<keyword or CTA instruction>`
- `avatar_profile=<profile_id>`
- `render=true|false`
- `platform=reels|tiktok|shorts|linkedin|x|threads|youtube`

## Runtime behavior
1. Parse source and preserve provenance.
2. Build SourcePack and claim authority map.
3. Define situational ICP and pain/pleasure/fear/aspiration model.
4. Route primary viral driver + subdrivers.
5. Generate and score 5–12 angles.
6. Generate and score hooks across distinct hook families.
7. Build stable semantic beat graph with ~3s information cadence.
8. Compile semantic → spoken → TTS scripts.
9. Run factual, simplicity, duration, CTA and moral gates.
10. Compile provider request from configurable avatar profile.
11. If render is explicitly requested, send to provider through the active connector/runtime.
12. Poll/ingest provider telemetry and actual duration.
13. Emit avatar-content manifest for downstream editing.
14. After publication, attach performance metrics for learning.

## Default profile
`heygen_rot_canonical_v1`

Current capability metadata:
- look: `49327c09aed5418383ba330e0daf0304`
- voice: `3fbb6707e4414df28da39b6cda40a4e3`
- 1080p, 9:16, mp4
- speed 1.05
- expressiveness medium

These values are time-sensitive provider metadata, not permanent design laws.

## Output contract
Every successful run returns:
- chosen ICP
- primary/secondary driver
- pain/pleasure map
- winning angle + tournament scores
- winning hook + tournament scores
- semantic beat graph
- display/spoken/TTS scripts
- pronunciation overrides
- CTA placement
- moral/payoff
- duration estimate
- preflight QA report
- provider request or render metadata
- downstream edit cues
- provenance/claim notes

## Render rule
`/heygen` does not spend provider credits by default. Rendering requires either `render=true` or explicit natural-language intent such as “lanza”, “genera”, “renderiza” or equivalent.

## Quality rule
Do not render if:
- estimated duration is outside 30–45s;
- claim provenance is missing for factual claims;
- core transformation is unclear;
- hook is below the configured threshold;
- CTA/moral contract is missing;
- stable beat IDs fail validation.

## Downstream boundary
The output avatar video is an intermediate asset. Motion graphics, PNG overlays, B-roll, animated typography, compositing, final sound design, grade and export are owned by the downstream editing graph.
