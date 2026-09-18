# Golden Scene Reconstruction / Renderer Validation Plan v1

Mission: `motion://mission/ultra-deep-video-reverse-engineering-v2`

Source: `ScreenRecording_08-26-2026 17-32-51_1.mp4`

Source SHA-256: `9b3076cb542e358386942a0fb6b160f1345564d4326738f9a340e2b5b38e199d`

## Why four golden scenes

Do not begin by reconstructing all 835 frames. First qualify the canonical graph against four scenes that collectively exercise the hard parts of the reference:

1. `S04_TALKING_CAPTION` — kinetic captions, hero-word overshoot, speech/SFX relationship, subject reframe.
2. `S11_UI_LIST` — vector UI, panel expansion, progressive row stagger, boxed caption hierarchy.
3. `S14_AUDIO_VISUAL_TEXT` — horizontal carousel, heading/state synchronization, technical grid, annotation overlays.
4. `S16_FACTOR_X` — foreground depth, occlusion, classical object, semantic payoff and deliberate calm hold.

If these four cannot be reconstructed from the canonical model without fresh creative decisions, the model is incomplete.

## Canonical truth consumed by every renderer

```text
FrameTimeline
+ EditingGraph
+ CaptionGraph
+ DepthGraph
+ TransitionMap
+ AudioEventMap
+ golden_scenes_reconstruction_v1.json
```

Renderer adapters do not own timing or creative hierarchy.

## Phase A — reference freeze

For each golden scene persist:
- exact source frame interval;
- visual reference keyframes at entrance / peak / settle / exit where available;
- source-bound text visibility windows;
- measured mixed-audio onsets;
- layer/depth graph;
- transform/easing estimates with confidence;
- all unknowns.

No keyframe is promoted from inferred to measured merely because it looks plausible.

## Phase B — After Effects reconstruction

Target comps:

```text
GOLD_S04_TALKING_CAPTION
GOLD_S11_UI_LIST
GOLD_S14_CAROUSEL
GOLD_S16_FACTOR_X
```

Required AE tests:
- scene duration exact at 30 fps;
- layer in/out frames exact;
- text layers independent by semantic unit;
- parent/null logic matches reconstruction spec;
- z-order and mattes produce the expected occlusion;
- Graph Editor curve approximations preserve peak and settle frames;
- motion blur enabled only on evidenced fast events;
- mixed audio onset markers placed on exact measured timestamps;
- effect/plugin identity may remain implementation-specific if the visible category matches the canonical effect stack.

AE PASS does **not** mean original `.aep` recovered. It means the canonical reconstruction specification is executable without material creative gaps.

## Phase C — Remotion reconstruction

Each golden scene becomes a deterministic component driven by source frame index.

Rules:
- use `<Sequence>` for exact in/out windows;
- captions use JSON compatible with `@remotion/captions` but hero words remain independently animated geometry;
- use common transform/easing adapters instead of scene-local magic numbers when a canonical motion verb exists;
- no browser time / random state;
- z-index reflects DepthGraph;
- audio events are frame-derived;
- hard cuts remain hard cuts in exact mode.

Physical render outputs must record:
- rendered frame count;
- fps;
- duration;
- artifact SHA;
- renderer/runtime revision.

## Phase D — HyperFrames reconstruction

Use one explicit DESIGN identity derived from the reference: dark red/black editorial system, off-white contrast, red hero emphasis, restrained grid/line system.

Rules:
- layout hero frame first;
- GSAP timeline synchronous and paused;
- register in `window.__timelines`;
- `data-duration` remains source authority;
- CSS z-index follows DepthGraph;
- no infinite repeats;
- captions/SFX use canonical source timing;
- for house-style transition requirements, source `HARD_CUT` may map only to a deterministic ~1-frame transition that does not shift visible source state boundaries.

## Phase E — frame-level comparison

At minimum compare entrance / peak / settle / exit frames for each golden scene.

Report separately:

### Temporal
- frame-count error;
- source event offset in frames.

### Typography
- visible text correctness;
- bbox displacement;
- relative hero/setup/tail scale;
- emphasis-start error.

### Motion
- transform extrema;
- peak/settle frame offset;
- motion-vector direction agreement.

### Depth
- z-order violations;
- occlusion mismatches.

### Visual
- SSIM / PSNR / perceptual metric where useful;
- edge-map similarity;
- palette/luminance difference.

### Audio
- visual-to-onset offset.

Metrics are diagnostic. Human visual review remains required.

## Phase F — structural generalization

After golden-scene fidelity is acceptable, replace all source-specific content:
- new speaker/subject;
- new copy of comparable semantic length;
- new UI content;
- new cards/assets;
- new foreground metaphor for Factor X;
- source Instagram UI removed.

Run three distinct content packs.

Generalization passes only if:
- beat/scene roles survive;
- source literal leakage = 0;
- required slots satisfiable = 100%;
- z-order/attention hierarchy violations = 0;
- caption refresh and visual stimulus envelope remain within template tolerance;
- no renderer-specific creative patch is necessary.

## Promotion gates

`AE_RECONSTRUCTION_VALIDATED`: four AE scenes executable + reviewed.

`REMOTION_RENDER_VALIDATED`: four physical Remotion scenes rendered with exact frame authority.

`HYPERFRAMES_RENDER_VALIDATED`: four physical HyperFrames scenes rendered with exact timing authority.

`FIDELITY_VALIDATED`: cross-renderer comparison passes declared per-domain thresholds.

`GENERALIZATION_VALIDATED`: three substituted content packs pass.

Only then may the structural template become a candidate `CANONICAL_TEMPLATE`.

## Current state

This plan is specified. None of the physical renderer/fidelity/generalization gates are claimed yet.
