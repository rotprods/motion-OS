# Phase 04 Plan — Visual DNA Extraction + Style Compiler

## Goal
Build the robust bridge between raw reference video and reusable, evidence-bound motion-system knowledge.

```text
VIDEO
 ↓
DETERMINISTIC / LOW-LEVEL EXTRACTION
 ↓
FEATURE PACK
 ↓
LLM / RULE NORMALIZATION
 ↓
MotionStyle2JSON
 ↓
COMPILER TARGETS + STYLE SIGNATURE
 ↓
GENERATE / RECONSTRUCT / RETRIEVE
```

The LLM is not the primary measurement engine when a measurable signal exists.

## CP4.1 Contracts — VERIFIED
- Feature Pack JSON Schema
- MotionStyle2JSON Schema
- controlled visual-DNA taxonomy
- extraction/learning graph
- schema + traceability tests

## CP4.2 Technical ingest — IMPLEMENTED V1
- `src/extraction/ingest.py`: FFprobe normalization, rational FPS, metadata, source SHA256.
- `src/extraction/segmentation.py`: deterministic change-score shot segmentation, full-coverage validation, keyframe planning.
- tests cover FPS rationality, shot continuity and keyframe invariants.

Production adapter still needed for computing real histogram scores and writing extracted keyframe images.

## CP4.3 Visual signals — IMPLEMENTED CORE / PROVIDERS OPEN
- `src/extraction/visual.py`: deterministic quantized palette, luminance/contrast, gradient candidate and bbox layout inference.
- `src/extraction/motion.py`: trajectory direction, speed, easing hypothesis and camera/local motion separation.
- OCR provider, real optical-flow provider and image FX/material detectors remain open integrations.

## CP4.4 Audio — IMPLEMENTED METRICS / PROVIDERS OPEN
- `src/extraction/audio_metrics.py`: nearest-event AV sync, hit-rate/delta metrics, event density and transcript coverage.
- Whisper/transcript and onset extraction remain provider integrations.

## CP4.5 Feature Pack + normalizer — IMPLEMENTED V1
- `src/extraction/feature_pack.py`: assembly, coverage warnings, schema validation and evidence coverage.
- `src/normalization/motionstyle.py`: controlled style inference, evidence claims, assumptions segregation, camera/depth/transition contracts and schema-valid MotionStyle2JSON.
- crucial invariant: when measured micro-choreography is insufficient, the normalizer records the gap instead of fabricating 12 events.

## CP4.6 Compiler — IMPLEMENTED V1
- `src/compilers/remotion.py`: deterministic scene-spec/TypeScript emitter + scene coverage validation.
- `src/compilers/framer.py`: required Framer contracts and easing presets.

## CP4.7 Knowledge loop — IMPLEMENTED V1 / SCALE BENCHMARK OPEN
- `src/knowledge/style_store.py`: SQLite style-signature store + evidence-aware cosine retrieval.
- no external vector DB until corpus size/latency justifies it.

## Measurement contracts
### Feature Pack
video_meta, shots, keyframes, OCR, color/layout/motion/FX/asset/audio stats, extraction provenance, warnings.

### MotionStyle2JSON
video, style_system, camera_rigs, shots with camera/depth/transition/motion/micro-choreography, evidence, quality and compiler targets.

## QA hard rules
- timestamps in range and shots contiguous.
- measurable facts cannot be invented by normalizer.
- exact font identity requires evidence.
- major inferred labels carry confidence + evidence.
- incompatible modes are chaptered rather than averaged.
- compiler scene boundaries must cover total duration.
- every creative/reconstruction promotion requires appropriate authority, not fixture-only evidence.

## Storage
Current scale: SQLite-compatible relational knowledge + Drive artifacts + graph lineage. External vector DB remains deferred.

## Graph delta after Gauntlet 10X
Added executable nodes/edges for:
`FFprobeIngest → ShotSegmenter → KeyframePlanner → VisualSignals/MotionSignals/AudioMetrics → FeaturePackAssembler → EvidenceBoundNormalizer → MotionStyle2JSON → RemotionCompiler/FramerCompiler → StyleStore → Retrieval → MotionSystem`.
Exact reconstruction branches from measured frame evidence into `FidelityGate → SVGJSPlayer` and never uses creative labels as exact geometry.

## Definition of Done
Still requires an empirical corpus run:
- one known MOTION.OS source with ground-truth timeline,
- >=10 heterogeneous references,
- extraction accuracy, timing error, evidence coverage and taxonomy consistency,
- useful retrieval,
- >=3 compiled references,
- no chat dependency.

## Current status after Gauntlet 10X
Architecture/contracts: HIGH MATURITY.
Core deterministic algorithms: IMPLEMENTED V1.
Provider integrations: PARTIAL.
Corpus benchmark: OPEN.
Production renderer proof: OPEN.
Authoritative temporal critic: OPEN.

## Next highest-leverage work
1. Real frame extractor + histogram/optical-flow provider using FFmpeg/OpenCV.
2. OCR provider abstraction with tracked blocks.
3. audio onset/transcript provider.
4. ground-truth benchmark runner against a known MOTION.OS render.
5. feed retrieved StyleSignature into grammar selection and compare generated outputs.
