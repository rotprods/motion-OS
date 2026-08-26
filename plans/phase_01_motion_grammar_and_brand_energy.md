# Phase 01 Plan — Motion Grammar + Brand Energy

## Goal
Separate visual style, product semantics, motion grammar and brand overlay so MOTION.OS does not apply one generic animation language to every brief.

## Canonical model
```text
brief
→ product_semantics
→ brand_energy
→ motion_grammar
→ visual_style
→ brand_overlay
→ beat_architecture
→ primitive_route
→ audio/camera/material grammar
→ render
→ grammar QA
```

## Current families
- APPLE_PREMIUM_DESKTOP
- HYPER_COMMERCIAL_GAMIFIED
- HYPER_COMMERCIAL_AUDIO
- DUOLINGO_FLUID_GAME_UI overlay
- SPOTIFY_FLUID_AUDIO_UI overlay

## Checkpoints
### P1.1 Grammar registry
- machine-readable grammar IDs
- permitted/forbidden primitives
- pacing envelope
- camera grammar
- material grammar
- hierarchy constraints

### P1.2 Semantic primitive routing
Product verbs must map to motion behavior before effects are selected.
Examples: save→toggle confirmation; streak→mechanical accumulation; focus→noise collapse; autonomy→controller node.

### P1.3 Brand-energy pacing
Pacing is derived from brand/product energy, not a global default.

### P1.4 Grammar critic
Score:
- hierarchy_under_motion
- beat_focus
- motion_intent
- transition_motivation
- product_ui_authenticity
- material_consistency
- AV sync
- final_hold_stability

## Definition of Done
- same brief rendered under >=3 grammars yields structurally distinct motion, not recolors
- grammar critic rejects visually attractive but semantically wrong candidates
- primitive router cannot violate hard grammar constraints without explicit override
- text integrity preserved across all grammars

## Learning delta from Phase 04
Phase 04 adds measured Visual DNA. Grammar selection should eventually use evidence-derived motion statistics rather than description-only labels.
