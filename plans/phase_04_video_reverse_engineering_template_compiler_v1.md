# Phase 04 Extension — Frame-Accurate Video Reverse Engineering + Editing Template Compiler v1

Status: **IMPLEMENTATION WAVE / MERGE-BLOCKED BY #39/#48**  
Owner session: `motion://session/video-reverse-engineer/20260828T095100Z`  
Workstream: `motion://work/video-reverse-engineering-templates-v1`  
Base: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`

## 0. Why this exists

Phase04 already measures physical video facts and normalizes them into MotionStyle2JSON. The missing product layer is **replicability**: given a reference video supplied by the user, MOTION.OS must be able to distinguish what is source-specific from what is transferable, reconstruct the temporal/editing behavior at frame granularity, and emit reusable editing templates.

This extension deliberately **reuses** rather than replaces:

`FFprobe/FFmpeg decode → shots/keyframes → OCR/color/layout/optical-flow/FX/audio → FeaturePack → MotionStyle2JSON → compiler targets`.

The new chain is:

```text
USER REFERENCE VIDEO
  ↓
Phase04 physical analysis / FeaturePack
  ↓
MotionStyle2JSON
  ↓
FRAME TIMELINE COMPILER
  ├─ shot boundaries
  ├─ measured per-frame/pair motion
  ├─ observed text events
  ├─ audio onset candidates
  └─ evidence authority
  ↓
EDITING SIGNATURE
  ├─ cadence / cut density
  ├─ transition grammar
  ├─ camera grammar
  ├─ motion-energy curve
  ├─ typography rhythm
  ├─ layout behavior
  ├─ audio/edit synchronization
  └─ palette/material/style evidence
  ↓
INVARIANT / VARIABLE SEPARATOR
  ↓
EDITING TEMPLATE v1
  ├─ RECONSTRUCT_EXACT
  ├─ STRUCTURAL_TEMPLATE
  └─ STYLE_TRANSFER
  ↓
COMPILER TARGETS / GRAPH / TEMPLATE LIBRARY
```

## 1. Three optimizers — never collapse them

### A. `RECONSTRUCT_EXACT`
Goal: reproduce the supplied reference as closely as source rights/assets/evidence permit.

Preserves:
- exact shot timing;
- observed copy where explicitly measured;
- exact palette/layout measurements;
- frame/pair motion observations;
- transition timing;
- audio onset timing;
- source-specific asset slots/provenance.

Primary QA: temporal/frame fidelity.

### B. `STRUCTURAL_TEMPLATE`
Goal: preserve editing logic while replacing source content.

Preserves:
- beat durations and relative cadence;
- hierarchy of shots;
- transition grammar;
- camera/motion grammar;
- text geometry/rhythm but not literal source copy;
- audio/edit synchronization rules;
- spatial/layout invariants;
- density and energy envelope.

Generalizes:
- literal text → semantic slots;
- source images/video → role slots;
- brand-specific colors/logos → replaceable tokens unless explicitly requested as a branded template.

Primary QA: structure retention + content independence.

### C. `STYLE_TRANSFER`
Goal: transfer the motion/editing DNA without recreating the source sequence.

Preserves only stable higher-order priors:
- pacing distribution;
- dominant transition families;
- motion/camera behavior;
- typography behavior class;
- composition tendencies;
- audio-response behavior;
- color/material style only when intended.

Primary QA: recognizable style without scene-copy dependence.

## 2. Evidence authority model

Every extracted field is one of:

- `measured`: physical provider result;
- `measured_heuristic`: deterministic measured proxy/heuristic;
- `inferred`: normalized from evidence with confidence;
- `assumption`: explicit unsupported production assumption;
- `unavailable`: provider or evidence absent.

Hard rules:
1. Never synthesize a measured frame observation because a neighboring frame suggests it.
2. OCR observations only claim the frames actually sampled unless continuity has an explicitly named inference method.
3. Audio onsets are onset candidates, not semantic beats unless a semantic music provider proves them.
4. Camera attribution from optical flow is a likelihood, not ground-truth camera telemetry.
5. Exact font identity requires evidence.
6. Literal source content must not leak into a generalizable template by default.

## 3. Frame timeline contract

For every decoded source frame `f`:

```text
frame
at_ms
shot_id
shot_boundary: start|end|null
motion_observation:
  measured pair source/target frames
  global_dx/global_dy
  global_magnitude
  local_residual_median
  motion_median
  camera_likelihood
text_observations[]
audio_events[]
keyframe_refs[]
authority{}
```

A frame with no direct optical-flow/OCR/audio observation is still represented, but unavailable fields remain null/empty rather than invented.

This timeline is the canonical bridge from physical measurements to frame-accurate reverse engineering.

## 4. Editing Signature v1

The compiler derives a deterministic, inspectable signature from FeaturePack + MotionStyle2JSON.

### Temporal
- total shots;
- mean / median / min / max shot duration;
- cut rate per second / minute;
- shot-duration coefficient of variation;
- cadence class;
- temporal energy curve.

### Motion
- mean/peak motion energy;
- global vs local residual motion;
- camera-dominance likelihood;
- dominant movement directions where evidence exists;
- settle/acceleration behavior where MotionStyle micro-choreography supports it.

### Transition grammar
- transition family histogram;
- timing distribution;
- supporting FX;
- transition-to-transition continuity rules.

### Camera grammar
- camera motion histogram;
- rig frequency;
- no-shake behavior;
- macro/wide/medium framing distribution;
- depth/parallax behavior.

### Typography/edit rhythm
- OCR observations / second;
- unique continuity IDs;
- approximate text occupancy/position classes;
- appearance/disappearance rhythm;
- kinetic-type motion events from MotionStyle when evidenced.

### Audio relationship
- onset rate;
- cut→nearest-onset distances;
- cut/onset sync ratio under explicit tolerance;
- transcript availability;
- sound semantics remain separate from raw onset evidence.

### Visual
- measured palette;
- gradient evidence;
- grid/anchor evidence;
- safe margins;
- material/FX measured proxies;
- style-family inference with confidence/evidence refs.

## 5. Invariants vs variables

The compiler must classify template knowledge into:

### HARD_INVARIANT
Breaking it materially changes the editing identity.
Examples: 700–900 ms hyper-commercial reward cadence; center-anchor altar composition; match-geometry transitions; persistent one-way motion vector.

### SOFT_INVARIANT
Preferred tendency that can bend to content.
Examples: palette temperature, safe margin, secondary card count, average blur proxy.

### VARIABLE_SLOT
Intentionally replaceable content.
Examples:
- `PRIMARY_HERO`
- `PRIMARY_COPY`
- `SECONDARY_COPY`
- `BRAND_LOGO`
- `UI_SCREEN`
- `BROLL_01`
- `DATA_METRIC_01`
- `SFX_ACCENT_01`

### SOURCE_LOCK
Only for exact reconstruction or explicitly branded templates.
Literal logo, exact copy, copyrighted artwork, exact UI screenshot, licensed music cue, etc.

## 6. Template anatomy

`editing_template.schema.json` is the additive contract. It stores:

- source identity and source SHA;
- replication mode;
- frame contract;
- editing signature;
- invariants;
- variable slots;
- timeline/beat skeleton;
- motion grammar;
- visual grammar;
- audio grammar;
- evidence/provenance;
- compiler targets;
- QA/generalization metrics;
- reference to `frame_timeline.json`.

The template itself is content-addressable through canonical JSON SHA-256.

## 7. Agentic operating model

The capability should be decomposable into specialist agents without separate truth stores.

### 1. Ingest / Forensics Agent
Authority: measurable media metadata and physical decode.
Consumes the source video, computes SHA, probes fps/duration/resolution and creates retained evidence frames.

### 2. Shot & Temporal Agent
Authority: deterministic segmentation/cadence facts.
Finds cut boundaries, keyframes, shot length distribution and timeline continuity.

### 3. Motion Kinematics Agent
Authority: measured optical-flow facts + bounded inference.
Extracts global/local motion, camera likelihood and motion-energy curve.

### 4. Typography & Layout Agent
Authority: OCR/layout evidence.
Tracks text continuity, placement, occupancy, hierarchy signals and layout anchors. Never asserts exact font without evidence.

### 5. Audio Rhythm Agent
Authority: physical audio envelope/onset candidates.
Maps timing relationships between sound transients and editing events. Semantic beat labels require stronger provider evidence.

### 6. Visual DNA Agent
Authority: evidence-bound normalization.
Builds style/color/material/composition grammar from measured signals.

### 7. Editing Graph Agent
Authority: deterministic projection.
Maps shots, transitions, motion grammar, audio cues and template slots into the existing typed EditingGraph ontology without creating a second graph authority.

### 8. Template Compiler Agent
Authority: deterministic generalization policy.
Separates invariants/source-locks/variables and emits the selected replication mode.

### 9. Fidelity / Generalization QA Agent
Authority: explicit evaluator outputs.
- exact mode: frame/temporal fidelity;
- structural mode: structure retention on substituted content;
- style mode: style similarity + scene independence.

### 10. Librarian Agent
Authority: corpus indexing/retrieval only.
Stores StyleSignatures/templates with provenance, deduplicates content hashes and makes templates retrievable by style/use-case.

## 8. Cross-agent handoff artifact

Every reference analysis ends with one bounded `ReverseEngineeringBundle` directory:

```text
<run>/
  analysis_manifest.json
  feature_pack.json
  motionstyle2json.json
  frame_timeline.json
  editing_template.json
  remotion_scene_spec.json
  motionSpec.ts
  qa/
  evidence/
```

No future agent needs the originating chat.

## 9. Compiler targets

### Remotion
- deterministic beat boundaries;
- layer topology;
- placeholder assets/copy;
- transition/motion presets;
- frame-safe duration contract.

### After Effects event map
- `at_frame` / `at_ms`;
- layer/target;
- channel;
- from/to;
- duration/ease;
- transition and camera events.

### Seedance / Sora prompt skeleton
The template exports constraints, rhythm, transition/camera grammar and slots. Generative-video prompting is a target, **not** evidence authority.

### Storyboard/keyframe specification
Provides required hero frames and layout states for the image-first → animation workflow.

## 10. Template quality gates

### Contract validity
- schema valid;
- source SHA present;
- frame count/duration/fps coherent;
- all beats contiguous and inside duration;
- frame timeline covers `[0, total_frames)` exactly.

### Evidence
- every HARD_INVARIANT has evidence refs;
- no `measured` claim without provider evidence;
- unavailable domains remain explicit;
- literal copy in structural/style modes is rejected.

### Replicability
For `STRUCTURAL_TEMPLATE`, test with at least 3 substituted content packs before promotion:
- beat coverage = 100%;
- no fixed-copy leakage;
- required slots satisfiable;
- timing deviation within template tolerance;
- hierarchy violations = 0;
- renderer coverage = 100%.

### Fidelity
For `RECONSTRUCT_EXACT`, compare:
- cut boundary error;
- motion trajectory error where measurable;
- text/layout position error;
- palette distance;
- audio event alignment;
- frame similarity where rights/assets allow direct comparison.

### Style transfer
Measure components separately; no vanity scalar:
- cadence similarity;
- transition-family similarity;
- motion-energy similarity;
- typography-density similarity;
- composition/layout similarity;
- visual palette/style similarity.

## 11. Anti-copy / source-boundary rule

MOTION.OS may reverse engineer **structure, timing, composition and motion behavior**. A reusable template must not silently bundle third-party source media, logos, proprietary copy or unlicensed music. Exact reconstruction is source-bound and requires source provenance/rights to be handled explicitly by the caller/project.

## 12. Implementation wave in this branch

This isolated branch implements:

- immutable user-source capture;
- this plan and canonical reverse-engineering knowledge;
- additive EditingTemplate JSON Schema;
- deterministic frame timeline compiler;
- deterministic editing-signature/template compiler;
- raw-video CLI built on existing `analyze_video()`;
- tests covering modes, timing, source-copy stripping, audio/cut sync and frame coverage;
- immutable agent lifecycle evidence;
- draft PR only; no merge while the regression barrier is active.

## 13. Explicit non-goals for v1

- no new vector database;
- no second event bus;
- no mutation of Phase07 coordination contracts;
- no new graph authority;
- no foundation-model claim of exact typography/object tracking;
- no automatic copyright/rights determination;
- no claim of production OCR/OpenCV/Whisper accuracy until measured against real corpus.

## 14. Follow-up superwaves after first user videos

### Wave A — Real corpus calibration
Analyze 10 heterogeneous supplied/reference videos. Create declared manual ground truth for cut boundaries, visible text, major transitions and motion classes.

### Wave B — object/layout tracking
Add measured object/card/subject tracks beyond OCR boxes, with explicit provider capability gates.

### Wave C — transition classifier
Train/evaluate deterministic/ML transition-family classifier against annotated samples; keep confidence/evidence per event.

### Wave D — typography behavior
Track text lines/blocks across frames and infer entrance/exit/mask/scale/kinetic patterns while keeping literal typeface identity evidence-bound.

### Wave E — renderer replication benchmark
Compile at least 3 templates to Remotion, physically render them, and compare structural/fidelity metrics against reference.

### Wave F — template retrieval/selection
Persist template signatures and measure retrieval usefulness across unseen briefs before adding heavier infrastructure.

## 15. Definition of done

This capability is not `VERIFIED` because code exists. It becomes empirically qualified only when:

1. real supplied videos have run through the physical pipeline;
2. frame/timeline coverage is validated;
3. template outputs survive substitution tests;
4. exact-mode fidelity is measured where applicable;
5. at least 3 compiled templates render successfully;
6. another zero-context agent can select a template, provide new content and reproduce the editing logic without this conversation.
