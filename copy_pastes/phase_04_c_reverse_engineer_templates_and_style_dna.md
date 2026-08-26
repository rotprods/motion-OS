# Phase 04C — User Copy-Paste: Universal Reverse Engineer + Style DNA Examples

> Source: user-supplied knowledge, captured 2026-08-26. Formatting normalized; technical content preserved.

## Universal Reverse-Engineer Template — Remotion + Framer Motion
Purpose: fill-later template that converts a briefing/evidence pack into a complete Remotion project specification with minimal ambiguity.

### Evidence layer
Separate:
- Observed: directly visible/provided facts.
- Inferred: high-confidence assumptions such as FPS, shutter style, stabilization, editing signature.
- Confidence percentage.

### Temporal layer
Master timeline with exact duration, frames and FPS. Every meaningful layout/content/camera change is a scene boundary. Montage cuts of 0.5–1.5s become distinct scenes.

### Spatial / visual layer
Global Z-order:
1. UI layer
2. Subject / product / hands / surfaces
3. Background / void / gradient / studio

Describe hero subject, materials, surface behavior, secondary subject constraints, UI motifs, text policy, composition archetype, symmetry, depth and contrast.

### Camera intelligence
Rig A — overhead / God's eye:
- cinema-camera class
- lens equivalent
- aperture / ISO / shutter angle when known
- locked tripod / micro drift

Rig B — macro slider:
- 50–100mm macro equivalent when supported
- narrow DOF
- motorized linear slider
- micro focus pull

Rig C — UI plate:
- vector/SVG UI
- scale drift + opacity choreography
- no distortion

Non-negotiable camera physics:
- zero shake by default
- no impossible angles
- no zoom unless specified
- macro feel through Z drift, not fake warp

### Lighting logic
Describe background base, key, fill, accent and reflection discipline. Use approximated colors only when evidence supports them.

### Motion / editing DNA
Capture editing signature chain, volatility, rhythm model, camera ramps and UI easing.

### Style fingerprint
Quantized dimensions:
- symmetry
- contrast
- saturation
- depth
- background logic

### Scene graph
Narrative subject, driver A/B, and energy curve.

### Design tokens for TypeScript
Color tokens, typography, radii, shadows, filters should be directly copyable into `tokens.ts`.

---

# Example DNA A — Minimal Orbit Ident System

## Narrative findings
1. Warm-light-gray neutral stage with subtle radial vignette.
2. Center acts as altar; generous negative space.
3. Circular grammar dominates: rings, orbits, arcs, rotations.
4. Motion breathes: calm easing, no aggressive cuts.
5. Low visual weight: fine strokes and simple forms.
6. Soft shadows + AO create restrained 3D.
7. Icons assemble; they do not simply pop into existence.
8. UI-like gestures resemble loading / scanning / pairing.
9. Color is an event, not a constant base.
10. Soft plastic / polycarbonate / ceramic material cues.
11. Controlled contrast; few pure blacks.
12. Modular rhythm: same camera/set logic across shots.
13. Fixed camera or micro-parallax only.
14. Mostly symmetric with micro-asymmetry.
15. Ecosystem gestalt through orbit/alignment.
16. Typography mostly absent until final lockup.
17. Neuromarketing target: calm + control + precision = premium trust.
18. Accessibility risk: gray-on-gray contrast.

## Non-negotiables
- Warm gray background, never pure white.
- Center anchor in ~80% of planes.
- At least one circular/orbit element per scene.
- Calm easing, no cartoon bounce or strong overshoot.
- Soft shadows + micro highlight, no noisy textures.

## Tokens
Background base: `#F2F2F1 → #E9E9E7`.
Radial vignette: center +4% luminance, edge -6%.
Neutral strokes/objects: `#BFC0C2`, `#A9AAAD`; deep gray `#2B2C2E` sparingly.
Accents:
- scan pink range `#FF2D55–#FF4D6D`
- activity green `#27C842–#32D74B`
- product ring: 4–8 medium-saturation hues, no extreme neon

Stroke: 4–10px at 1080p, round cap/join.
Drop shadow: blur 0–18px, opacity 8–18%.
AO: blur 0–10px, opacity 6–12%.
Safe area: 8–12%.
Motif scale: 18–35% of frame height.

## Tension map
- monochrome soft-3D vs accent line art
- literal product objects vs abstract symbols
- 3D shadows vs flat stroke

Resolution rule: neutral base + one mode per scene (`object_3d` OR `accent_line`), do not mix 50/50 without hierarchy.

## Canonical concepts
Archetypes: Premium Calm, Tech Human, Editorial Minimal.
Keywords: orbit, breath, assemble, soft-3D, neutral-field, single-accent.
Shape primitives: circle, arc, capsule, dot, ring, soft-cylinder.
Motion principles: assemble_not_pop, orbit_then_resolve, breathing_pace, single_focus.
Scene length guideline: 2–5s.
Easing: ease-in-out cubic; overshoot none/micro.
Transition: fade or match cut, background constant, primary shape morph drives transition.

## Production / QA
Formats: 16:9, 9:16, 1:1.
Work vector-first where possible; shadows are shared presets; background reusable plate.
Failure modes:
- background drifts to pure white
- shadows become too strong / cheap 3D
- too many accents
- flat stroke + 3D object mixed without hierarchy

Mitigations:
- locked background range
- shadow caps
- one-accent rule
- one rendering mode per scene

Suggested quality gates:
- background deltaE <=3
- accent count <=1
- shadow opacity <=18%
- stroke-width variation <=15%
- centered composition / high negative space
- circular grammar present
- no harsh snaps
- clean centered final lockup

---

# Example DNA B — Portal Glass UI Launch System

## New narrative layers
- Black spatial stage instead of clinical gray.
- Atmospheric blurred gradients: moss, sunset, violet/cool dawn.
- Glass UI panels with restrained blur, border and long soft shadow.
- Hero-card hierarchy: one main card, 1–3 secondary cards.
- Real UI content: maps, dashboards, sliders.
- Typography becomes protagonist with one colored keyword.
- Defocused photo/CG backgrounds can create micro-DOF behind glass.
- Subtle Z float / parallax → digital museum feeling.
- Rhythm shifts from assembly to reveal: soft zoom + cards landing.
- Elements can begin small in black space and grow intentionally.
- Warm/cool accent gradients change between scenes but are controlled.
- Scrims/dimming protect UI/text contrast.
- Product naming and tangible UI increase self-efficacy / credibility.
- Fine cinematic grain may be used to prevent gradient banding.
- Interaction cues: text fields, cursor, sliders → live-tool feel.
- Transitions: shape/color match cuts and simulated rack-focus.
- Final beat: CTA/lockup with breathing hold.

## Tensions
A. Minimal orbit/gray ident vs black-stage glass product demo.
B. Abstract symbols vs real UI.
C. One accent vs protagonist gradient.

Recommended resolution:
- circular/orbital grammar remains transition motif.
- body becomes Portal Glass UI on black stage.
- maximum one gradient per scene + one emphasized word.

## Tokens
Black stage base: `#050506 → #0A0A0C`; edge vignette -10%; grain 1–2% only for banding.
Warm-gray secondary mode: `#F2F2F1 → #E9E9E7`.
Atmospheric gradients, one per scene:
- sunset `#FF8A3D → #F4C66A → #7A5CFF`
- moss `#1E2D22 → #6FA36B → #0B1510`
- cool dawn `#7AC8FF → #B7E3FF → #FFB48A`

Glass card:
- white fill 8–14%
- blur 18–36px
- white border 12–18%, 1px
- shadow y=18–32, blur=40–80, black opacity 18–30%
- corner radius 18–28

Typography:
- 1–2 lines max
- regular/medium weight
- one hero word in restrained cyan/indigo/coral
- tracking +0 to +20 depending on family

## Prompt-pack example from source
Base generation language: minimal premium ident on warm gray radial plate; centered negative-space composition; circles/rings/capsules; soft-3D shadows and restrained highlight; orbital/assembly motion; one accent color or controlled product palette; clean editorial technology; text only at final lockup.

Negative concepts: strong noise/grain, pure-white backgrounds, hard shadows, neon glow, excessive detail, dramatic perspective, decorative typography, complex backgrounds, aggressive contrast, glitch.

Shadow preset example:
- Drop: y=6, blur=14, opacity=12% black
- AO: y=2, blur=6, opacity=8% black
