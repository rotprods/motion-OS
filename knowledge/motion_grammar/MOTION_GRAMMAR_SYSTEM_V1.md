# MOTION.OS — Motion Grammar System v1

## Purpose
Convert supplied expert motion-design knowledge into reusable, brand-aware planning constraints. These are not fixed templates. They are grammar families that the Creative Director, Style Synthesizer, Primitive Router and QA stack must interpret per brief.

## 1. Universal production principles

### Hierarchy
- One dominant idea per beat/screen.
- Every secondary element must support the hero focus.
- Text remains readable during motion; motion never justifies illegibility.
- Use contrast beats: high energy should be followed by controlled holds when useful.
- Final frame must settle and remain stable long enough to encode memory.

### Layout / spatial design
- Layout is a motion primitive, not a static container.
- Preserve consistent spacing, radius and alignment systems inside one visual family.
- Use depth only when it communicates hierarchy or transition intent.
- Avoid visual noise, arbitrary decoration and generic dashboard density.
- UI must obey plausible desktop/mobile proportions for the product being represented.

### Motion
- Every entrance and transition must have intent: reveal, focus, reward, continuity, escalation, compression or resolution.
- No random movement. No chaos without hierarchy.
- Fast commercial grammar may change hero focus approximately every 0.7–1.2 s; premium calm grammar may hold substantially longer.
- Prefer structural operators: morph, slide, card stack, condense, expand, count, draw, trim path, controlled burst, match motion, foreground occlusion, Z push, whip pan.
- Repeated scale+opacity entrances are a template failure.
- 2.5D layering is preferred over fake cinematic DOF for UI-heavy work.

### Typography
- Text integrity is a hard invariant.
- No kerning drift, text warp, morphing letters, raster softness or motion blur that harms reading.
- Use typography as a hero primitive when appropriate, not as labels pasted after composition.
- Numbers used as scoreboards/counters should be tabular and mechanically stable.

### Materials
- Material behavior must match the family: matte UI, restrained glass, brushed metal, cream editorial paper, product-grade dark cards, etc.
- Shadows/reflections exist only to explain depth/material.
- Excessive glass, neon, glow and generic gradient decoration are anti-patterns.

### Camera
- UI/product motion defaults to orthographic-leaning 2.5D space.
- Camera behavior is chosen by grammar: X/Y whip, micro-Z push, parallax, orbit, static editorial hold.
- Avoid handheld/lens distortion/DOF when they damage UI proof or typography.

### Audio
- Audio cues are graph-native and linked to visual events.
- UI clicks, counters, badge unlocks, save toggles, whooshes, impacts and final logo hits must reinforce the motion grammar.
- Sound design must share the brand maturity level; premium commercial does not mean childish or noisy.

## 2. Grammar family: APPLE_PREMIUM_DESKTOP

### Intent
Calm power, native desktop productivity, presentation-ready polish, premium material restraint.

### Visual tokens
- off-white / graphite / soft silver / deep black
- restrained cool blue/cyan only when justified
- SF Pro / Google Sans-like modern sans hierarchy
- consistent rounded radius system
- soft shadows, brushed aluminum environment, matte cards, selective frosted glass
- generous whitespace and realistic desktop proportions

### Composition
- one dominant idea per screen
- strong negative space
- precise toolbars/sidebars/window balance
- native-feeling cursor zones, scroll areas, toggles, pills and segmented controls

### Preferred motion primitives
panel_expand, modal_seed_to_full_card, cursor_typing, smooth_ui_zoom, card_unfold, desktop_to_workspace, parallax_push, mask_reveal, foreground_pass

### Required screen archetypes
Hero Desktop; Neo AI Workspace; Creative Multitasking; Focus Mode; Presentation/Export; Widgets/Intelligence Overview.

### Negative constraints
No generic SaaS, startup landing-page tropes, crypto dashboard, gaming aesthetic, cartoon icons, excessive glass blur, cheap 3D, cramped layouts or illegible labels.

## 3. Grammar family: HYPER_COMMERCIAL_GAMIFIED

Derived from the supplied Duolingo commercial grammar, but generalized so the engine can apply it without copying one brand.

### Intent
Fast, addictive, playful, reward-driven product proof. Energy changes roughly every second while retaining one hero focus per beat.

### Motion vocabulary
spring_snap, card_pop, count_up, icon_burst, badge_unlock, trim_paths, leaderboard_ascent, controlled_confetti, mascot_cross, reward_condense, hold_readability

### Camera
Orthographic 2.5D, fast X/Y whip pans, micro-Z pushes on reward moments, layered cards, no cinematic DOF on UI.

### QA
Reward logic must be authentic to the product; mascot/logo anatomy exact; text absolute; chaos always subordinated to hierarchy.

## 4. Grammar family: HYPER_COMMERCIAL_AUDIO

Derived from supplied Spotify grammar and generalized for music/audio products.

### Intent
Fast, cultural, emotional, rhythm-driven product motion. UI, pulse and sound behave as one system.

### Motion vocabulary
player_expand, playlist_stack, save_toggle, lyric_reveal, waveform_draw, audio_pulse, cover_wall, stats_count, multi_device_flow, collect_to_logo

### Camera
Orthographic 2.5D with X/Y whips and micro-Z hero pushes. Card depth is structural, not decorative.

### QA
Player logic believable; controls/icons exact; waveform synchronized rather than random; lyrics/stats readable; calm emotional hold before final acceleration when appropriate.

## 5. Brand grammar overlays
A brand overlay adds exact palette, iconography, logo constraints, UI semantics, mascot/product rules and copy. It must never replace the universal grammar contract.

Current supplied overlays:
- DUOLINGO_FLUID_GAME_UI
- SPOTIFY_FLUID_AUDIO_UI

These overlays are reference knowledge, not authorization to invent official assets or claim exact product fidelity without verified references.

## 6. Planner contract
For every generated piece output:
1. `base_grammar`
2. `brand_overlay` or null
3. `energy_curve`
4. `beat_duration_policy`
5. `hero_focus_per_beat`
6. `layout_topology`
7. `motion_primitive_sequence`
8. `camera_grammar`
9. `typography_contract`
10. `material_contract`
11. `audio_event_contract`
12. `negative_constraints`
13. `final_hold_duration`

## 7. QA additions
Score independently:
- hierarchy_under_motion
- text_integrity
- beat_focus
- motion_intent
- transition_motivation
- camera_consistency
- material_consistency
- product_ui_authenticity
- audio_visual_sync
- final_hold_stability

A technically valid render fails creative QA when motion is random, hierarchy collapses, UI becomes implausible, or the result feels like a generic template.