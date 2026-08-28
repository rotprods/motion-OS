# MOTION.OS — Ultra-Deep Reference Video Reverse Engineering Template

Status: **CANONICAL WORKING TEMPLATE / PROMOTION REQUIRES EMPIRICAL FIDELITY**  
Mission: `motion://mission/ultra-deep-video-reverse-engineering-v2`

## 0. Purpose

Use this template for every reference video that MOTION.OS must convert from **flattened pixels + audio** into an evidence-bound editing system that can be executed by After Effects, Remotion, HyperFrames/GSAP, or a generative-video adapter.

The deliverable is not a style description. It is a reconstruction contract:

`VIDEO → FRAME STATE → LAYER STATE → MOTION STATE → DEPTH STATE → AUDIO STATE → ATTENTION STATE → ATOMIC OPERATIONS → EDITING GRAPH → RENDERER ADAPTERS → FIDELITY QA → REUSABLE TEMPLATE`

## 1. Authority model

Order of authority:

1. `MEASURED` — physical decode/provider evidence.
2. `MEASURED_HEURISTIC` — deterministic calculation from measured evidence.
3. `EVIDENCE_BOUND_INFERENCE` — visual/semantic inference citing frames or measured events.
4. `ASSUMPTION` — explicit production assumption.
5. `UNKNOWN` — source internals cannot be recovered from flattened media.

Never promote an internal implementation detail from appearance alone. Exact font files, original AE effect/plugin names, hidden masks/mattes, audio stems and physical camera intrinsics remain `UNKNOWN` unless separately supplied.

## 2. Definition of “100% extracted”

MOTION.OS must never claim that a flattened MP4 reveals 100% of the original editor's hidden project operations.

The only valid closure claim is **100% OBSERVABLE REPLICABLE ACTION COVERAGE**:

- every decoded frame belongs to a scene/shot;
- every high-salience visible change is represented by an atomic operation or an explicit `SOURCE_LOCK/UNKNOWN`;
- every measured P90 frame-change peak is covered by one or more operations;
- every measured P90 motion peak is covered by one or more operations;
- every observable caption, transition, foreground/depth event, UI/device insert and major audio/visual synchronization event is mapped;
- every atomic operation has an implementation path for AE, Remotion and HyperFrames;
- no unresolved high-salience event is left as “looks cool” / “some effect”.

Closure does **not** imply physical reconstruction fidelity. That is a later gate.

## 3. Canonical per-video directory

```text
forensics/references/<video_id>/
  README.md
  analysis_manifest.json
  editing_signature.json
  action_inventory.json
  coverage_matrix.json
  decision_operation_graph.json
  structural_template.json
  ae_reconstruction_spec.json
  cross_renderer_mapping_v1.json
  gauntlet/
    gauntlet_report.json
    G01_TEMPORAL_CENSUS.md
    G02_CAPTION_DEPTH.md
    G03_MOTION_TRANSITIONS.md
    G04_AUDIO_RETENTION.md
    G05_RENDERER_PARITY.md
    G06_ADVERSARIAL_MISSING_ACTION.md
    G07_COVERAGE_CLOSURE.md
  golden_scenes/
    <scene_id>/
      reconstruction_spec.json
      render_evidence.json
      diff_metrics.json
```

Heavy frame-level evidence remains in the artifact/evidence plane, not Git history.

## 4. Frame contract

Every decoded frame MUST have a record carrying: frame/PTS/timecode, scene/shot/beat, visible entities, caption/graphic entities, camera/depth/lighting/color/FX/audio/attention/transition state, motion vectors, occlusions, evidence refs, inferred properties and explicit unknowns.

Missing measurements remain empty/null. Never interpolate evidence silently.

## 5. Atomic operation contract

Every observable edit action becomes an atomic operation with:

```yaml
action_id:
scene_id:
start_frame:
impact_frame:
end_frame:
domain:
verb:
target:
function:
parameters: {}
audio_link:
z_role:
authority:
confidence:
evidence_refs: []
renderer_mapping:
  after_effects:
  remotion:
  hyperframes:
```

A renderer mapping is mandatory before observable-action closure.

## 6. Domains that MUST be inspected

### Temporal
Cuts, micro-cuts, holds, freeze frames, ramps, edit-density changes, resets, pattern-interrupt spacing.

### Captions / typography — P0
Chunking, line breaks, timing, hero words, color, weight class, width class, tracking, leading, spatial placement, scale punches, mask reveals, word replacement, boxed emphasis, 3D/spatial words, tail copy and caption/SFX sync.

### Subject / object layers
Subject, face/hands, phones, screens, cards, icons, photos, classical objects, 3D figures, source UI and foreground inserts.

### Depth / compositing — P0
Z order, occlusion, subject masks, device masks, foreground/midground/background, parallax, scale depth, blur hierarchy and contact-shadow relationships.

### Motion / camera
Position, scale, rotation, velocity, acceleration, overshoot, settle, easing class, global vs local motion, apparent crop/reframe vs physical camera.

### Transitions
Hard cut, graphic/object match, mask/shape/occlusion wipe, whip, push, slide, zoom, depth tunnel, morph, dissolve, flash, blur, glitch, frame-within-frame, text-driven and compound transitions.

### FX / materials
Color grade, blur, glow, bloom, grain/noise, vignette, motion blur, shadow, stroke, distortion, chromatic effects, mattes, light sweeps and displacement. Describe visible behavior; do not invent plugin identity.

### Audio / SFX — P0
Strong onsets, impacts, clicks, whooshes, reverse effects, risers, sub hits, UI ticks, foley, silence/reduction windows and their linked visual events. Mixed-track timing may be measured; semantic SFX class is inference unless stems exist.

### Retention / stimulus — P0
Caption replacements, hero keyword changes, camera punches, graphic inserts/exits, phones, 3D objects, background changes, hard cuts, layout changes, depth changes, SFX hits, pattern interrupts and low-entropy breathing windows.

## 7. Canonical action verbs

`cut`, `mask_reveal`, `count_up`, `stagger`, `scale_punch`, `reframe`, `frame_within_frame`, `glitch_flash`, `phone_scale`, `spatial_type`, `row_stagger`, `carousel_snap`, `foreground_rise`, `hard_cut_punch`, `grid_reveal`, `line_draw`, `light_sweep`, `opacity_reveal`, `slide`, `flash`, `hold`, `text_build`, `icon_pop`, `object_insert`, `depth_push`, `occlusion`, `waveform`, `source_lock`.

Add a new verb only when existing semantics cannot describe the behavior without loss.

## 8. Layer reconstruction model

Think as an After Effects compositor. Candidate primitives:

`COMP`, `PRECOMP`, `FOOTAGE_LAYER`, `TEXT_LAYER`, `SHAPE_LAYER`, `NULL`, `CAMERA`, `LIGHT`, `ADJUSTMENT_LAYER`, `MATTE`, `MASK`, `EFFECT`.

For each visible layer record identity/continuity, in/out frames, parent/matte, blend when observable, z order, anchor, transforms, opacity, motion blur if evidenced, masks/effect categories, keyframes/interpolation, occlusions, confidence and evidence.

## 9. Renderer parity

AE, Remotion and HyperFrames are three executors of one canonical editing graph, not three creative interpretations.

- After Effects: comp/precomp/layer/keyframe/matte/effect-category plan.
- Remotion: frame-driven `<Sequence>`/transform/mask/audio events.
- HyperFrames: layout end-state first, deterministic GSAP/SVG/CSS timelines.

Renderer adapters must not own timing, hierarchy, z-order or transition semantics.

## 10. Decision-operation graph

`decision_operation_graph.json` is a **derived projection**, never a second graph authority.

Required relations:

- `Scene CONTAINS OperationProjection`
- `OperationProjection COMPILES_TO Renderer`
- explicit scene temporal sequence
- renderer mappings carry implementation semantics only
- canonical semantic/editing truth remains MOTION.OS `TypedEditingGraph` + evidence bundles.

## 11. Gauntlet loop

Every reference MUST pass these loops:

1. `G01_TEMPORAL_CENSUS` — all scenes/cuts/measured high-change peaks covered.
2. `G02_CAPTION_DEPTH` — captions, layers, z-order, occlusion, devices/foreground.
3. `G03_MOTION_TRANSITIONS` — motion, reframe, easing classes, transitions, FX families.
4. `G04_AUDIO_RETENTION` — mixed-audio onsets, SFX relationships, stimulus/retention grammar.
5. `G05_RENDERER_PARITY` — each atomic operation has AE/Remotion/HyperFrames mapping.
6. `G06_ADVERSARIAL_MISSING_ACTION` — deliberately search for unmapped micro-events/high-salience changes.
7. `G07_COVERAGE_CLOSURE` — no observable high-salience gap; unknown source internals explicit.

A loop may only pass with evidence. “Looks complete” is not evidence.

## 12. Physical validation loop

Observable-action closure is followed by empirical reconstruction:

1. select golden scenes covering typography, UI, carousel, depth/occlusion and payoff;
2. render without re-consulting the source for new creative decisions;
3. compare reference vs render using timing, SSIM/PSNR/perceptual metrics, edge/color differences, OCR geometry, optical-flow differences and human review;
4. convert every mismatch into a Defect / repair candidate;
5. repair the canonical operation/template, not only one renderer;
6. repeat until thresholds pass or a declared source limitation blocks improvement.

## 13. Generalization

A `STRUCTURAL_TEMPLATE` requires at least three content substitutions. It passes only if edit identity survives and literal source assets/copy do not leak.

## 14. Promotion states

`DRAFT_EXTRACTED → EVIDENCE_VALIDATED → LAYER_MODEL_VALIDATED → MOTION_VALIDATED → AUDIO_SYNC_VALIDATED → AE_RECONSTRUCTION_VALIDATED → REMOTION_RENDER_VALIDATED → HYPERFRAMES_RENDER_VALIDATED → FIDELITY_VALIDATED → GENERALIZATION_VALIDATED → CANONICAL_TEMPLATE`

No code test alone can grant `FIDELITY_VALIDATED` or `CANONICAL_TEMPLATE`.

## 15. Local operator commands

```bash
python scripts/reverse_engineer_video.py <video> --out <run-dir> --mode structural --flow-stride 1 --keep-frames
python scripts/reverse_engineering_gauntlet.py --inventory <action_inventory.json> --frame-metrics <frame_metrics.json> --out <gauntlet_report.json>
python scripts/local_verify.py quick
python scripts/agent_event.py validate
```

## 16. Handoff rule

A zero-context agent must be able to continue from the repository + event bus + per-video canonical files without this chat. If it needs the original conversation to understand how to reproduce the edit, extraction is incomplete.
