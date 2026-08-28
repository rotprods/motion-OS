# MOTION.OS — Video Reverse Engineering Canon v1

This document is the durable operating canon for turning a supplied reference video into evidence-bound editing knowledge and reusable templates.

## 1. Prime directive

A reference video is not a prompt aesthetic. It is a timed system of observable states.

Reverse engineering therefore asks, in order:

1. **What physically happened?**
2. **When did it happen?**
3. **What persisted across states?**
4. **What changed and through which motion/transition?**
5. **Which observations are content-specific?**
6. **Which rules are stable enough to reuse?**
7. **Which facts remain unknown?**

Do not jump directly from video → style adjectives.

## 2. Authority hierarchy

`physical measurement > declared source metadata > evidence-bound inference > explicit assumption`.

A model may help classify a transition or style family, but it may not invent a cut, motion vector, text string, frame event or audio onset that the evidence layer did not support.

Unknown is better than fabricated precision.

## 3. Frame-first, shot-aware

The system retains two simultaneous views:

### Frame timeline
A complete index of every decoded frame and the observations that are directly bound to it.

### Shot/beat graph
A semantic compression of contiguous frames into meaningful editing units.

Never use the shot abstraction to erase frame evidence. Never use frame noise to ignore the editorial structure.

## 4. Editing DNA dimensions

Every analyzed reference should be explainable across these dimensions:

### Temporal DNA
- cut locations;
- shot durations;
- rhythm regularity/volatility;
- hold windows;
- acceleration/deceleration of edit density;
- recurrence patterns;
- payoff spacing.

### Motion DNA
- global camera motion;
- local object motion;
- motion energy;
- dominant direction;
- acceleration/easing evidence;
- settle/overshoot behavior;
- primary/secondary/micro motion hierarchy.

### Transition DNA
- hard cut;
- graphic match;
- object match;
- mask/shape wipe;
- whip-pan;
- push/slide;
- zoom/depth transition;
- morph;
- opacity/dissolve;
- occlusion transition;
- compound transition;
- unknown.

Transition identity must be evidence-bound. Do not classify every high-change boundary as a named effect.

### Camera DNA
- static / micro drift;
- pan/tilt-like global vector behavior;
- dolly/push/pull-like scale/depth behavior where supported;
- orthographic/pseudo-orthographic UI behavior;
- framing distribution;
- parallax/depth relationship;
- focus behavior where observable.

### Composition DNA
- anchor distribution;
- grid behavior;
- negative space;
- symmetry/asymmetry;
- hero occupancy;
- layering/z-order;
- repetition density;
- foreground/midground/background relationships.

### Typography DNA
- visible text density;
- line/block location;
- hierarchy role;
- duration on screen;
- entrance/exit behavior when evidence supports it;
- kinetic relationship to other layers;
- typography-to-beat timing.

Exact font family is never asserted from appearance alone.

### Visual/material DNA
- measured palette;
- gradient evidence;
- contrast/highlight/blur proxies;
- grain/noise evidence;
- material candidates;
- accent-frequency behavior;
- background logic.

### Audio/edit DNA
- onset candidates;
- transient density;
- cut/onset distances;
- synchronization ratio;
- silence/hold behavior;
- voice/music/SFX semantics only when provider evidence exists.

### Narrative/attention DNA
This is an inferred layer:
- hook;
- setup;
- escalation;
- proof;
- contrast;
- payoff;
- resolve;
- attention target per beat.

It must cite the measured states from which it was inferred.

## 5. The invariant test

A property becomes a reusable invariant only if removing or materially changing it would alter the reference's editing identity.

Ask:

> If I replace every noun, logo, image and brand color but keep this behavior, does the sequence still feel edited the same way?

If yes, it is likely structural/style DNA.
If no, it is likely source content or a brand-specific lock.

## 6. Replication modes

### RECONSTRUCT_EXACT
Source-bound. Preserve literal timing/content when supported and permitted.

### STRUCTURAL_TEMPLATE
Preserve timing, hierarchy, transition, camera, motion and audio relationships. Replace literal source content with typed slots.

### STYLE_TRANSFER
Preserve distributions/tendencies rather than the same scene graph. New narrative structures are allowed.

A caller must choose a mode before compilation; the compiler must not silently blend them.

## 7. Template slot ontology

Prefer semantic roles rather than arbitrary names:

- `PRIMARY_HERO`
- `SECONDARY_HERO`
- `PRIMARY_COPY`
- `SECONDARY_COPY`
- `STAT_VALUE`
- `BRAND_MARK`
- `UI_STATE`
- `BROLL`
- `BACKGROUND_PLATE`
- `VOICE_LINE`
- `MUSIC_BED`
- `SFX_ACCENT`
- `TRANSITION_DRIVER`

Slots declare required/optional, media type, duration/geometry constraints and evidence-derived reason.

## 8. Canonical motion rule

Nothing moves without function.

When reconstructing, the function may simply be `source_evidenced`.
When templating, every motion must additionally have a transferable function such as:

- direct attention;
- disclose information;
- create hierarchy;
- connect states;
- preserve continuity;
- synchronize audio;
- convey physical/system behavior;
- create a deliberate emotional beat.

## 9. Micro-choreography

When enough evidence exists, normalize atomic motion events as:

```text
at_ms
at_frame
target
action
channels
from
to
duration_ms
ease
authority
evidence_refs
```

Do not generate an arbitrary minimum number of choreography events. Sparse evidence produces sparse choreography.

## 10. Template promotion levels

- `DRAFT_EXTRACTED`: compiler output exists.
- `EVIDENCE_VALIDATED`: frame/shot/evidence gates pass.
- `RENDER_VALIDATED`: at least one target renderer executes it.
- `GENERALIZATION_VALIDATED`: structural/style template succeeds with substituted content.
- `CANONICAL_TEMPLATE`: corpus-tested, deduplicated, named and approved for retrieval.

No template enters the canonical library merely because it looks plausible.

## 11. Naming templates

Names describe behavior, not brands, unless the template is explicitly brand-locked.

Good:
- `hyper_reward_800ms_snap_grid`
- `premium_orbit_center_altar`
- `editorial_mask_push_3beat`
- `ui_proof_state_morph`

Avoid:
- `spotify_like_v2`
- `apple_clone`
- `cool_edit_03`

Brand examples may remain provenance/evidence but should not become generic semantics.

## 12. Similarity is multidimensional

Never reduce reconstruction/template fidelity to one opaque score.

Report separately:
- temporal fidelity;
- transition fidelity;
- motion fidelity;
- typography/layout fidelity;
- color/material fidelity;
- audio alignment;
- narrative structure;
- content independence.

A weighted score may be displayed only after the individual dimensions remain visible.

## 13. Fail-closed rules

Reject or downgrade authority when:

- decoded frame coverage is inconsistent;
- shot timeline has gaps/overlap;
- source SHA is absent;
- source literals leak into structural/style mode;
- a HARD_INVARIANT has no evidence ref;
- template expects an unavailable capability without declaring it;
- a renderer silently changes duration/beat boundaries;
- a template depends on a third-party source asset without provenance;
- exact reconstruction is evaluated using a creative-style score instead of fidelity metrics.

## 14. User-video operating loop

For each future supplied video:

1. hash/probe/decode;
2. run physical extraction;
3. produce frame timeline;
4. normalize MotionStyle2JSON;
5. compute editing signature;
6. manually/adversarially inspect ambiguous transition/type/layout claims where needed;
7. choose replication mode;
8. compile template;
9. generate renderer/prompt targets;
10. test with original or substituted content according to mode;
11. persist evidence + template + QA;
12. compare against existing template corpus;
13. merge/cluster only after evidence says the template is meaningfully reusable.

This is the default reverse-engineering loop for MOTION.OS.
