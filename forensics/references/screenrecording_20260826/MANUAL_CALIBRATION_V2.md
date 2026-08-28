# ScreenRecording 2026-08-26 — Manual Calibration v2

Mission: `motion://mission/ultra-deep-video-reverse-engineering-v2`

Source SHA-256: `9b3076cb542e358386942a0fb6b160f1345564d4326738f9a340e2b5b38e199d`

Authority: manual visual calibration against the measured 30 fps / 835-frame timeline. This is a reconstruction specification, not recovery of the original After Effects project.

## Main conclusion

The editing identity is not “talking head + captions”. The primary retention mechanism is **representation-mode switching** while one visual language remains coherent: red/black editorial field, off-white contrast, large semantic keywords, classical symbols, devices, spatial 2.5D scenes, progressive UI and foreground proof inserts.

The sequence moves through: social-proof composite → dark kinetic question → flash → isolated title → talking-head hero caption → phone frame-within-frame → glitch → editorial phone/columns → crowd 2.5D → single-figure 2.5D → low-entropy reset → progressive UI → human bridge → waveform prelude → audio/visual/text carousel → layered examples → Factor X foreground payoff → end card.

## Caption calibration — P0

- 12 caption groups.
- 47 independently timed word/phrase units.
- 15 hero/emphasis units (~31.9%).
- ~1.69 caption-unit starts per second across the whole reel.
- Median interval between caption-unit starts: ~267 ms.
- P90 interval: ~1.37 s; dense word builds are deliberately alternated with longer hero holds.
- Captions must be reconstructed as independent geometry, not as one subtitle track.

Key caption grammars:
1. progressive words → hero keyword (`así es como puedes REDACTAR`);
2. small setup + large red keyword + small tail (`que sea CIENTÍFICAMENTE imposible`);
3. words distributed around a 3D/2.5D body (`contenido`, `INTERÉS`);
4. boxed semantic hero (`absolutamente`);
5. heading bound to carousel state (`audio → visual → texto`);
6. top-line accumulation + large numeral `3`;
7. foreground final lockup (`Factor X`).

## Depth / compositing calibration — P0

Canonical relative stack:

`IG_UI (+6) > CAPTIONS (+3.5) > FOREGROUND_OBJECT (+3) > FOREGROUND_CARDS (+2.5) > DEVICE (+2) > MIDGRAPHICS (+1.7) > SUBJECT (+1) > BACKGROUND (-3)`

Important relationships:
- proof/example cards intentionally occlude the subject;
- phone mockups contain footage rather than merely sitting beside it;
- spatial captions occupy negative space around 2.5D figures;
- classical column and question mark sit in foreground during the final payoff;
- apparent depth comes from scale, blur, rim light, overlap and parallax; true 3D must not be claimed unless evidence requires it.

## Motion calibration

High-value motion families:
- iris/mask reveal;
- count-up + card stagger;
- word-by-word build;
- hero caption punch/settle;
- apparent crop/camera push and release;
- phone scale/reframe;
- 4-frame glitch/flash;
- slow 2.5D stage push;
- panel expansion;
- progressive row stagger;
- horizontal carousel snap;
- foreground-object rise;
- hard-cut payoff punch.

Measured/evidence-bound anchors already captured in the bundle include:
- talking-head face width grows from roughly 0.51 to 0.64 frame-width in the 4.9–7.2 s segment, then releases toward ~0.41 before the phone transition; this proves reframing but not a physical camera dolly;
- phone-scroll median adjacent scale delta ~1.70%, p95 ~3.56%;
- carousel p95 translation ~11.93 px on the 256×554 analysis copy;
- Factor-X payoff has comparatively low transform volatility after assembly (p95 scale delta ~0.64%).

## SFX / audio synchronization — P0

22 strong mixed-track onsets were measured (~0.79/s). SFX class names remain inferred because stems are unavailable.

High-confidence semantic pairings include:
- 3.965 s: strongest `whoosh_flash`, aligned with the major flash transition;
- 5.120 s: impact approximately 80 ms before the visible start of `CIENTÍFICAMENTE`;
- 14.315 s: UI hit on status-bar activation;
- 19.267 s: slide hit exactly on `visual` carousel state;
- 20.805 s: slide hit around transition to `texto`;
- 24.218 s: impact almost exactly on the hard cut into Factor X;
- 27.533 s: impact ~33 ms after `la caga` becomes visible.

Current measured association: 10/22 strong onset events have a caption-unit relationship within the configured local window; 4/22 have an explicitly linked major transition. Do not infer that unlinked onsets are irrelevant — mixed music/voice/SFX stems are not separated.

## Scene-level After Effects architecture

Recommended master:

```text
MASTER_512x1108_30
├── PRECOMP_BACKGROUND
├── PRECOMP_SUBJECT
├── PRECOMP_GRAPHICS
├── PRECOMP_CAPTIONS
├── PRECOMP_UI
├── PRECOMP_FOREGROUND
├── PRECOMP_GRADE
└── IG_UI_SOURCE_LOCK
```

Each designed scene should be a dedicated scene precomp. Talking-head segments remain replaceable footage plates. Hero words, distributed spatial words, foreground cards, device mockups, columns/question marks and UI rows must remain independent layers when visually evidenced.

Representative keyframe contracts:
- `CIENTÍFICAMENTE`: frame 156 scale 0.84 / opacity 0 → frame 160 scale 1.12 / opacity 1 → frame 165 scale 1.00 / opacity 1; `expoOut`-like short overshoot, evidence-bound estimate.
- status bar: frame 405 scaleX 0.15 / opacity 0 → frame 414 scaleX 1.0 / opacity 1.
- UI rows: X 487→493, diamond 495→501, megaphone 504→510, each y +35→0 and opacity 0→1 estimate.
- carousel states: audio frame 562 → visual frame 578 → texto frame 615; X translation is the dominant channel.
- Factor X foreground: column rises roughly frames 735→756; title frames 747/752/758 uses 0.90→1.06→1.00 inferred scale settle.

## Renderer parity

After Effects, Remotion and HyperFrames are executors of one canonical editing model, not three creative interpretations.

Shared authority:
`FrameTimeline + EditingGraph + CaptionGraph + DepthGraph + TransitionMap + AudioEventMap`.

Frame index is authoritative. Renderer adapters may change implementation primitives but may not alter source-bound timing, z-order, semantic hero hierarchy or transition type.

For `HARD_CUT`, exact reconstruction preserves the cut. If a renderer has a house-rule requiring a transition, implement the nearest deterministic zero/one-frame transition without shifting the source-visible state.

## Retention calibration

Existing conservative annotation:
- 64 high-salience stimulus clusters;
- lower-bound ~2.30 salient visual events/s;
- median annotated stimulus interval ~254 ms;
- P90 ~939 ms;
- max annotated high-salience gap ~2.3 s.

The important rule is not “add an effect every 250 ms”. Ordinary facial/body movement is excluded and the system deliberately uses low-entropy resets. Retention comes from **controlled changes in representation and attention target**, not indiscriminate object density.

## Promotion state

- DRAFT_EXTRACTED: PASS
- EVIDENCE_VALIDATED: PARTIAL
- LAYER_MODEL_VALIDATED: manual visual v2
- MOTION_VALIDATED: PARTIAL
- AUDIO_SYNC_VALIDATED: PARTIAL
- AE_RECONSTRUCTION_VALIDATED: NOT YET
- REMOTION_RENDER_VALIDATED: NOT YET
- HYPERFRAMES_RENDER_VALIDATED: NOT YET
- FIDELITY_VALIDATED: NOT YET
- GENERALIZATION_VALIDATED: NOT YET
- CANONICAL_TEMPLATE: NO

Next empirical gate: reconstruct representative high-value scenes (caption punch, progressive UI, carousel, Factor X) from the canonical model in at least one physical renderer, compare against source, then generalize the same template with substituted content.