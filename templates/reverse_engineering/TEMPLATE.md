# MOTION.OS — Ultra-Deep Reference Video Reverse Engineering Template

Status: **CANONICAL WORKING TEMPLATE / PROMOTION REQUIRES EMPIRICAL FIDELITY**  
Mission: `motion://mission/ultra-deep-video-reverse-engineering-v2`

## 0. Purpose

Use this template for every reference video that MOTION.OS must convert from **flattened pixels + audio** into an evidence-bound editing system executable by After Effects, Remotion, HyperFrames/GSAP, or a generative-video adapter.

The deliverable is not a style description. It is a reconstruction contract:

`VIDEO → FRAME STATE → LAYER STATE → MOTION STATE → DEPTH STATE → AUDIO STATE → ATTENTION STATE → ATOMIC OPERATIONS/SUBEVENTS → EDITING GRAPH → RENDERER ADAPTERS → FIDELITY QA → REUSABLE TEMPLATE`

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
- every high-salience visible change is represented by an atomic operation/subevent or explicit `SOURCE_LOCK/UNKNOWN`;
- every measured P90 frame-change and motion peak is covered;
- lower-threshold P80/P75 residuals are adjudicated as `anchored`, `continuous`, `source_native`, or remain an explicit failure;
- every observable caption, transition, foreground/depth event, UI/device insert and major audio/visual synchronization event is mapped;
- every staggered operation exposes its child events instead of hiding them in one broad time window;
- continuous operations are represented as continuous behavior instead of fabricated point keyframes;
- source-native plate motion is not falsely promoted to editorial motion;
- every observable operation has an implementation path for AE, Remotion and HyperFrames;
- no unresolved high-salience event remains described merely as “some effect”.

Closure does **not** imply physical reconstruction fidelity. That is a later gate.

## 3. Canonical per-video directory

```text
forensics/references/<video_id>/
  README.md
  analysis_manifest.json
  editing_signature.json
  action_inventory_index_v2.json
  coverage_matrix.json
  deep_residual_review_v2.json
  decision_operation_graph.json
  structural_template.json
  ae_reconstruction_spec.json
  cross_renderer_mapping_v1.json
  drive_mirror_manifest.json
  gauntlet/
    gauntlet_report.json
    G01_TEMPORAL_CENSUS.md
    G02_CAPTION_DEPTH.md
    G03_MOTION_TRANSITIONS.md
    G04_AUDIO_RETENTION.md
    G05_RENDERER_PARITY.md
    G06_ADVERSARIAL_MISSING_ACTION.md
    G07_COVERAGE_CLOSURE.md
    G08_SUBACTION_GRANULARITY.md
    G09_LOW_THRESHOLD_RESIDUAL_REVIEW.md
  golden_scenes/
    <scene_id>/
      reconstruction_spec.json
      render_evidence.json
      diff_metrics.json
```

Heavy frame-level evidence and the full action inventory live in the Drive/artifact evidence plane, not Git history.

## 4. Frame contract

Every decoded frame MUST carry frame/PTS/timecode, scene/shot/beat, visible entities, caption/graphic entities, camera/depth/lighting/color/FX/audio/attention/transition state, motion vectors, occlusions, evidence refs, inferred properties and explicit unknowns.

Missing measurements remain empty/null. Never interpolate evidence silently.

## 5. Atomic operation contract

Every observable edit action becomes an operation with:

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
temporal_mode: discrete|continuous|staggered|hold|compound|source_native
motion_origin: editorial|source_native|mixed|unknown
authority:
confidence:
evidence_refs: []
subevents: []
renderer_mapping:
  after_effects:
  remotion:
  hyperframes:
```

### Temporal semantics

- `discrete`: one bounded action with meaningful entrance/impact/settle anchors.
- `continuous`: deterministic behavior spans the window; internal metric peaks do not require invented keyframes.
- `staggered`: parent groups a semantic sequence but MUST expose child `subevents` for each independently timed element.
- `hold`: deliberately stable editorial state; source-native movement may continue underneath.
- `compound`: several inseparable visual mechanisms form one transition/action cluster.
- `source_native`: visible motion belongs to the footage/plate, not an editing decision.

### Motion origin

- `editorial`: caused by editing/compositing/motion design.
- `source_native`: subject/plate motion already present in source footage.
- `mixed`: both are visibly present and cannot be cleanly separated from the flattened source.
- `unknown`: evidence insufficient.

A renderer mapping is mandatory before observable-action closure.

## 6. Domains that MUST be inspected

### Temporal
Cuts, micro-cuts, holds, freeze frames, ramps, edit-density changes, resets, pattern-interrupt spacing.

### Captions / typography — P0
Chunking, line breaks, timing, hero words, color, weight/width class, tracking, leading, spatial placement, scale punches, masks, word replacement, boxed emphasis, spatial words, tail copy and caption/SFX sync.

### Subject / object layers
Subject, face/hands, phones, screens, cards, icons, photos, classical objects, 3D figures, source UI and foreground inserts.

### Depth / compositing — P0
Z order, occlusion, subject/device masks, foreground/midground/background, parallax, scale depth, blur hierarchy and contact-shadow relationships.

### Motion / camera
Position, scale, rotation, velocity, acceleration, overshoot, settle, easing class, global vs local motion, crop/reframe vs physical camera, editorial vs source-native motion.

### Transitions
Hard cut, graphic/object match, mask/shape/occlusion wipe, whip, push, slide, zoom, depth tunnel, morph, dissolve, flash, blur, glitch, frame-within-frame, text-driven and compound transitions.

### FX / materials
Color grade, blur, glow, bloom, grain/noise, vignette, motion blur, shadow, stroke, distortion, chromatic effects, mattes, light sweeps and displacement. Describe visible behavior; do not invent plugin identity.

### Audio / SFX — P0
Strong onsets, impacts, clicks, whooshes, reverse effects, risers, sub hits, UI ticks, foley, silence/reduction windows and linked visual events. Mixed-track timing may be measured; semantic SFX class is inference unless stems exist.

### Retention / stimulus — P0
Caption replacements, hero keyword changes, camera punches, graphic inserts/exits, phones, 3D objects, background changes, hard cuts, layout/depth changes, SFX hits, pattern interrupts and low-entropy breathing windows.

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
- Remotion: frame-driven `<Sequence>`/transform/mask/audio events; normal captions may use `@remotion/captions`, hero words remain independent geometry.
- HyperFrames: hero-layout first, deterministic synchronous GSAP/SVG/CSS timelines, authoritative `data-duration`.

Renderer adapters must not own timing, hierarchy, z-order or transition semantics.

## 10. Decision-operation graph

`decision_operation_graph.json` is a **derived projection**, never a second graph authority.

Required relations:
- `Scene CONTAINS OperationProjection`
- `OperationProjection COMPILES_TO Renderer`
- explicit scene temporal sequence
- renderer mappings carry implementation semantics only
- canonical semantic/editing truth remains MOTION.OS `TypedEditingGraph` + evidence bundles.

## 11. Nine-loop gauntlet

Every reference MUST pass:

1. `G01_TEMPORAL_CENSUS` — all scenes/cuts/P90 high-change peaks covered.
2. `G02_CAPTION_DEPTH` — caption geometry, layer topology, z-order, occlusion, devices/foreground.
3. `G03_MOTION_TRANSITIONS` — motion, reframe, easing classes, transitions, FX families.
4. `G04_AUDIO_RETENTION` — mixed-audio onsets, SFX relationships, stimulus/retention grammar.
5. `G05_RENDERER_PARITY` — every operation has AE/Remotion/HyperFrames mapping.
6. `G06_ADVERSARIAL_MISSING_ACTION` — search unmapped 3–10 frame/high-salience events.
7. `G07_COVERAGE_CLOSURE` — first observable closure at P90.
8. `G08_SUBACTION_GRANULARITY` — split broad `stagger`/progressive actions into explicit child subevents; classify continuous and source-native motion.
9. `G09_LOW_THRESHOLD_RESIDUAL_REVIEW` — attack P80/P75 (and optionally lower) measured peaks; unexplained residuals fail closure.

A loop passes only with evidence. “Looks complete” is not evidence.

## 12. Physical validation loop

Observable-action closure is followed by empirical reconstruction:

1. select golden scenes covering typography, UI, carousel, depth/occlusion and payoff;
2. freeze the action graph;
3. render without re-consulting the source for new creative decisions;
4. compare reference vs render using timing, SSIM/PSNR/perceptual metrics, edge/color differences, OCR geometry, optical-flow differences and human review;
5. convert every mismatch into a Defect / repair candidate;
6. repair the canonical operation/template, not only one renderer;
7. repeat until thresholds pass or an explicit source limitation blocks improvement.

## 13. Generalization

A `STRUCTURAL_TEMPLATE` requires at least three content substitutions. It passes only if edit identity survives and literal source assets/copy do not leak.

## 14. Promotion states

`DRAFT_EXTRACTED → EVIDENCE_VALIDATED → LAYER_MODEL_VALIDATED → MOTION_VALIDATED → AUDIO_SYNC_VALIDATED → OBSERVABLE_ACTION_CLOSED → AE_RECONSTRUCTION_VALIDATED → REMOTION_RENDER_VALIDATED → HYPERFRAMES_RENDER_VALIDATED → FIDELITY_VALIDATED → GENERALIZATION_VALIDATED → CANONICAL_TEMPLATE`

No code test alone can grant `FIDELITY_VALIDATED` or `CANONICAL_TEMPLATE`.

## 15. Local operator commands

```bash
python scripts/reverse_engineer_video.py <video> --out <run-dir> --mode structural --flow-stride 1 --keep-frames
python scripts/reverse_engineering_gauntlet.py --inventory <action_inventory.json> --frame-metrics <frame_metrics.json> --out <gauntlet_report.json>
python scripts/local_verify.py quick
python scripts/agent_event.py validate
```

## 16. Handoff rule

A zero-context agent must be able to continue from repository + Event Bus + Drive specimen evidence without this chat. If it needs the originating conversation to know how to reproduce the edit, extraction is incomplete.
