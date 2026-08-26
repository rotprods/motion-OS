# Phase 04 Plan — Visual DNA Extraction + Style Compiler

## Goal
Build the robust bridge between raw reference video and reusable motion-system knowledge.

The core design is intentionally two-layered:

```text
VIDEO
 ↓
DETERMINISTIC / LOW-LEVEL EXTRACTION
 ↓
FEATURE PACK (measured evidence)
 ↓
LLM NORMALIZATION / TAXONOMY
 ↓
MotionStyle2JSON (schema-valid)
 ↓
STYLE SIGNATURE + EVIDENCE
 ↓
COMPILER TARGETS / KNOWLEDGE STORE
 ↓
GENERATE / RECONSTRUCT / RETRIEVE
```

The LLM must not be treated as the primary measurement engine when measurable signals are available.

# 1. Extraction architecture

## 1.1 Ingest
Implementation target: FFprobe/FFmpeg.
Output:
- duration_ms
- fps rational + float
- width/height
- aspect ratio
- codec
- bitrate
- audio tracks
- frame count when reliable

Gate: metadata round-trip validated against source.

## 1.2 Shot segmentation
Preferred initial stack: PySceneDetect + deterministic fallback based on frame histogram distance.
Output per shot:
- shot_id
- start/end frame
- start/end ms
- confidence
- detection method

Gate: no overlap, sorted shots, full timeline coverage or explicit gaps.

## 1.3 Keyframe sampling
Default: start/mid/end + adaptive frame for high-motion shots.
Store source frame index, exact timestamp, SHA256 and image reference.

## 1.4 OCR / text tracking
OCR is a pluggable provider, not hard-coded. Use exact frame evidence and track blocks across frames.
Output:
- text
- bbox normalized + pixels
- confidence
- role hypothesis
- approximate weight/size class
- fill color
- contrast ratio estimate
- continuity_id

Rules:
- exact font identity remains unknown unless external evidence proves it
- track text separately from blur/mask layers

## 1.5 Color extraction
Per video + per shot:
- dominant colors
- accent candidates
- luminance/saturation stats
- gradient candidates: linear/radial, angle/center, approximate stops
- contrast distribution

Initial algorithms: k-means/median-cut in perceptual color space + gradient residual heuristics.

## 1.6 Layout extraction
Signals:
- safe margins
- alignment lines
- center-of-mass
- repeated x/y anchors
- probable column grid
- card count and bbox distribution
- composition archetype candidates

Output remains probabilistic with evidence.

## 1.7 Motion extraction — priority module
Use optical flow + tracked boxes + frame differences to measure:
- shot transition class
- global camera motion vs local object motion
- dominant direction
- translation / scale / rotation trajectories
- apparent parallax bands
- stagger / delay patterns
- entry/exit timing
- motion blur proxy
- periodic motion
- velocity / acceleration profiles for easing classification

Then LLM normalizes measured curves into closed primitive/easing taxonomy.

Important: `easeOutCubic` is an inferred label over a measured trajectory, not a directly observed fact.

## 1.8 FX extraction
Heuristics for:
- blur
- bloom / glow
- grain/noise
- shadow softness
- vignette
- light leak

Every FX label stores confidence + supporting frames/timestamps.

## 1.9 2D/3D asset/material typing
Closed primitives + material cues:
- circle, ring, arc, capsule, cube, sphere, ribbon, wire, blob, panel/card, complex_other
- glass, matte_plastic, brushed_metal, polished_metal, paper, clay, ceramic, raster_photo, other

Do not infer true 3D geometry when only 2D evidence exists; use `appearance_3d` confidence.

## 1.10 Audio
Provider abstraction:
- transcript words/segments + timestamps
- beat/onset timestamps
- loudness envelope
- transient events
- speech/music/sfx coarse classification

Compute visual cut/motion-event synchronization against audio events.

# 2. Feature Pack contract
A measurement-oriented intermediate representation. It MUST NOT contain unsupported polished style conclusions.

Top-level:
- video_meta
- shots
- keyframes
- ocr
- color_stats
- layout_stats
- motion_stats
- fx_stats
- asset_stats
- audio_stats
- extraction_provenance
- warnings

Every extraction field that is inferred has confidence + method + evidence refs.

# 3. LLM normalization
Input: Feature Pack + optional user/reference context.
Output: `MotionStyle2JSON` validated against schema.

Responsibilities:
- controlled taxonomy mapping
- conflict detection
- style chaptering instead of averaging incompatible modes
- naming high-level grammar from low-level signals
- deriving reusable timing rules
- emitting assumptions separately from observations

Forbidden:
- inventing measurements
- inventing font identity
- changing timestamps to make narrative cleaner
- emitting unknown taxonomy IDs without `other`

# 4. MotionStyle2JSON contract
Required domains:
- video
- style_system
- camera_rigs
- shots
- evidence
- quality
- compiler_targets

Each shot contains:
- exact boundaries
- on_screen_text
- composition tokens
- camera_plan
- depth_plan
- transition_spec
- motion_events
- micro_choreography

Completeness target: >=12 atomic choreography events per non-trivial shot, or explicit justified assumption.

# 5. Compiler targets

## Remotion
Compile:
- project dimensions / FPS / duration_frames
- scene boundaries
- layer IDs
- z-order
- atomic frame events
- easing functions
- asset references
- camera transforms

## Framer Motion
Compile named contracts and cubic-bezier/spring presets. Framer output is allowed for interactive/prototype use; deterministic video export still routes through the production render path.

## Future targets
- After Effects JSON bridge
- SVG timeline
- Rive/Lottie where representationally valid

# 6. Knowledge storage architecture
Do not prematurely introduce distributed infrastructure.

### v1 — current scale
- SQLite/Postgres-compatible relational schema for videos, shots, style signatures, primitives, evidence, confidences
- filesystem/Drive for frames and large media
- embeddings stored as optional vectors/blobs or external index later

### vector retrieval trigger
Adopt pgvector/Qdrant/etc. only after enough analyzed references exist to justify semantic similarity retrieval. Do not add Pinecone/Weaviate merely because the source example mentions them.

# 7. Taxonomy evolution
Taxonomy is versioned. New labels require:
- definition
- parent/family
- positive evidence examples
- negative/confusable examples
- renderer mapping
- migration strategy

No free-form style label enters canonical DB directly.

# 8. Graph engineering delta
New graph nodes:
- SourceVideo
- ExtractionRun
- Shot
- Keyframe
- OCRBlock
- MeasuredMotionTrack
- ColorProfile
- LayoutProfile
- AudioEvent
- FeaturePack
- TaxonomyLabel
- StyleSignature
- EvidenceClaim
- CompilerTarget

New edges:
- SourceVideo HAS_SHOT Shot
- Shot HAS_KEYFRAME Keyframe
- ExtractionRun MEASURED EvidenceClaim
- EvidenceClaim SUPPORTED_BY Keyframe/AudioEvent
- FeaturePack AGGREGATES EvidenceClaim
- LLMNormalization MAPS FeaturePack → TaxonomyLabel
- StyleSignature DERIVED_FROM FeaturePack
- StyleSignature COMPILES_TO CompilerTarget
- ReferenceCluster CONTAINS StyleSignature
- MotionSystem LEARNS_FROM StyleSignature

# 9. QA gates
## Extraction QA
- metadata correctness
- shot coverage
- timestamps in range
- evidence refs resolve
- no duplicate frame identities
- OCR text confidence represented
- no unsupported exact-font claim

## Normalization QA
- schema valid
- taxonomy IDs valid
- every major style/motion label has evidence
- assumptions segregated
- incompatible style systems not silently averaged

## Compiler QA
- scene frame boundaries sum to project duration
- all target IDs resolve
- every enter has settle unless intentionally continuous
- every trace/underline has start/progress/end
- no occlusion event without z/depth relationship
- all glow/blur/grain tokens used in choreography are declared in style system and vice versa

# 10. Implementation milestones
### CP4.1 Contracts
- Feature Pack JSON Schema
- MotionStyle2JSON JSON Schema
- taxonomy YAML
- extraction provenance schema

### CP4.2 Technical ingest
- ffprobe metadata
- shot detection
- keyframe extraction
- deterministic fixtures/tests

### CP4.3 Visual signals
- color
- layout
- OCR provider interface
- optical flow/motion trajectories

### CP4.4 Audio
- transcript provider interface
- onset/beat extraction
- AV sync metrics

### CP4.5 Normalizer
- structured LLM input
- schema repair
- evidence binding
- taxonomy mapper

### CP4.6 Compiler
- MotionStyle2JSON → Remotion scene spec
- Framer contracts

### CP4.7 Knowledge loop
- persist style signatures
- retrieve similar references
- feed successful styles/primitive sequences into generation planning

# 11. Definition of Done
Analyze at least 10 deliberately different reference videos and demonstrate:
- reproducible extraction runs
- schema-valid Feature Packs
- schema-valid MotionStyle2JSON
- evidence traceability for major labels
- taxonomy consistency
- useful style similarity retrieval
- Remotion compilation for at least 3 references
- no reliance on chat context

# 12. Current risks
- OCR provider quality and language coverage
- false camera-motion inference from object-dominant shots
- confusing raster bloom with actual vector glow
- font guessing
- gradient detection in compressed footage
- overfitting taxonomy to current reference library
- excessive micro_choreography generated by LLM without evidence

# 13. Required experiments
1. Analyze one native MOTION.OS render where true timeline is known; compare extracted values against ground truth.
2. Analyze an Apple-like calm ident and hyper-commercial UI ad; confirm taxonomy keeps them separate.
3. Extract RC06/RC09 known primitives and measure primitive-classification accuracy.
4. Compile extracted style back into a new piece; evaluate style fidelity without copying exact content.
5. Use exact-reconstruction mode on a vectorizable shot and compare to extraction-mode estimates to calibrate errors.

## Learning changelog — interaction 2026-08-26 / Phase 04
- Added deterministic measurement layer ahead of LLM.
- Refined reference intelligence from prose DNA extraction to evidence-bound Feature Packs.
- Added MotionStyle2JSON compiler layer.
- Added micro-choreography as atomic representation between style analysis and renderer timeline.
- Added camera/depth/transition contracts.
- Rejected immediate mandatory vector DB: defer until dataset scale justifies it.
- Made exact font identification an evidence-gated claim.
- Connected Phase 04 extraction to both GENERATE and RECONSTRUCT while keeping their optimizers separate.
