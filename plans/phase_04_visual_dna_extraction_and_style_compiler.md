# Phase 04 Plan — Visual DNA Extraction + Style Compiler

## Goal
Build the robust bridge between raw reference video and reusable, evidence-bound motion-system knowledge.

```text
VIDEO
 ↓
PHYSICAL DECODE + DETERMINISTIC / LOW-LEVEL EXTRACTION
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

The LLM is not the primary measurement engine when a measurable signal exists. Runtime provider state is part of evidence authority: unavailable is a valid state; fabricated fallback is not.

## CP4.1 Contracts — VERIFIED
- Feature Pack JSON Schema
- MotionStyle2JSON Schema
- controlled visual-DNA taxonomy
- extraction/learning graph
- schema + traceability tests

## CP4.2 Technical ingest — VERIFIED V2
- `src/extraction/ingest.py`: FFprobe normalization, rational FPS, metadata and source SHA256.
- `src/extraction/providers.py`: physical FFmpeg PNG decode; every retained frame receives SHA256 evidence identity.
- real adjacent-frame change scoring combines luminance and edge-structure deltas.
- adaptive robust shot threshold uses median/MAD rather than a global magic constant.
- `src/extraction/segmentation.py`: contiguous shot segmentation + keyframe plan.
- physical keyframe records bind frame index, timestamp, shot and SHA256 artifact reference.
- synthetic real-MP4 ground-truth E2E test creates 90 source frames, encodes H.264, decodes the MP4 and requires recovery of boundaries at frames 30/60 within <=1 frame.

Remaining: benchmark against a historical/native MOTION.OS master, not only the controlled synthetic fixture.

## CP4.3 Visual signals — REAL PROVIDERS V1
- pixel palette and gradient measurement from retained keyframes.
- OCR: optional real Tesseract provider with confidence, normalized bbox, evidence frame and deterministic continuity tracking.
- optical flow: optional real OpenCV Farneback dense flow measuring global dx/dy, local residual motion and camera-likelihood.
- layout: current measured path derives anchor/grid signals primarily from OCR boxes; richer object/card/layout detection remains open.
- FX/material: measured contrast/edge/highlight/blur proxies + evidence-bound material candidates. These are deliberately labeled heuristic/inferred, not ground-truth material recognition.
- provider capability registry distinguishes `measured`, `unavailable` and failure states.

Runtime rule: the absence of OpenCV/Tesseract does not fabricate empty measured observations. It emits an explicit provider-unavailable warning.

## CP4.4 Audio — REAL SIGNAL PROVIDER V1
- FFmpeg physical PCM decode.
- RMS envelope + transient/onset candidate timestamps from measured energy deltas.
- onset candidates are not mislabeled as semantic music beats.
- optional local Whisper provider implemented; unavailable/model/runtime failures remain explicit.
- existing AV-sync metrics consume measured visual/audio timestamps.

Remaining: production verification of transcript provider and stronger beat/music event semantics.

## CP4.5 Feature Pack + normalizer — VERIFIED E2E V2
- `src/extraction/pipeline.py` orchestrates MP4 → decode → shots/keyframes → visual/motion/OCR/FX/audio → Feature Pack.
- provider provenance and authority are persisted.
- `src/extraction/feature_pack.py` validates the measurement pack.
- `src/normalization/motionstyle.py` emits schema-valid MotionStyle2JSON with evidence-bound inference and separated assumptions.
- crucial invariant: normalization never fabricates micro-choreography to satisfy a quantity target.

## CP4.6 Compiler — VERIFIED E2E V2
- MotionStyle2JSON compiles to deterministic Remotion scene spec and TypeScript.
- scene coverage must exactly equal project duration before the pipeline succeeds.
- Framer Motion contracts remain available for interactive/prototype targets.
- current E2E benchmark reaches Remotion spec generation from a physically encoded MP4.

Remaining: actual Remotion production runtime render and frame comparison.

## CP4.7 Knowledge loop — IMPLEMENTED V1 / CORPUS EXECUTION NEXT
- SQLite StyleSignature storage + evidence-aware cosine retrieval exists.
- corpus runner is the next scale step: analyze heterogeneous videos, persist signatures, measure retrieval usefulness and taxonomy stability.
- external vector DB remains deferred until corpus/latency evidence justifies it.

## Ground-truth benchmark policy
`src/extraction/benchmark.py` reports dimensions separately:
- shot precision / recall / F1
- mean/max boundary error in frames
- OCR recall
- palette RGB distance
- evidence counts and warnings

It intentionally does NOT collapse incomparable extraction dimensions into one vanity score.

Synthetic fixture authority: `ground_truth_measurement` for the controlled source construction.
Real-world style/creative authority: still requires real reference corpus and temporal critic.

## Measurement contracts
### Feature Pack
video_meta, shots, keyframes, OCR, color/layout/motion/FX/asset/audio stats, extraction provenance, warnings.

### MotionStyle2JSON
video, style_system, camera_rigs, shots with camera/depth/transition/motion/micro-choreography, evidence, quality and compiler targets.

## QA hard rules
- timestamps in range and shots contiguous.
- every retained physical frame is content-addressable.
- measurable facts cannot be invented by the normalizer.
- exact font identity requires evidence.
- major inferred labels carry confidence + evidence.
- unavailable providers are explicit capability states.
- incompatible modes are chaptered rather than averaged.
- compiler scene boundaries cover total duration exactly.
- creative/reconstruction promotion requires appropriate authority, not fixture-only evidence.

## Storage
Current scale: SQLite-compatible relational knowledge + Drive artifacts + graph lineage. External vector DB remains deferred.

## Graph delta — Real Analysis Superwave
Canonical measurement chain is now:

`SourceMP4 → FFprobe → FFmpegPhysicalDecode → FrameSHA → ChangeScore → ShotBoundary/Keyframe → Pixel/OCR/OpticalFlow/FX/AudioEvidence → CapabilityGate → FeaturePack → SchemaGate → MotionStyle2JSON → SchemaGate → RemotionCompiler → CoverageGate → GroundTruthBenchmark`.

Optional providers branch through `AVAILABLE/UNAVAILABLE`; only AVAILABLE providers may create measured claims.

## Definition of Done
Phase 04 is not fully closed until:
- a known historical/native MOTION.OS source is benchmarked against ground truth,
- >=10 heterogeneous external/reference videos are analyzed,
- taxonomy consistency and evidence coverage are measured,
- retrieval produces demonstrably useful neighbors,
- >=3 analyzed references compile and render through real Remotion runtime,
- no chat dependency is required.

## Current status after Real Analysis Superwave
Architecture/contracts: HIGH MATURITY.
Physical decode + shot/keyframe evidence: VERIFIED IN CI.
Ground-truth synthetic MP4 benchmark: VERIFIED IN CI.
OCR/OpenCV/Whisper implementations: OPTIONAL PROVIDERS / production capability verification still required.
End-to-end FeaturePack → MotionStyle → Remotion spec: VERIFIED IN CI.
Heterogeneous corpus benchmark: OPEN.
Production Remotion render proof: OPEN.
HyperFrames runtime proof: OPEN.
Authoritative temporal critic: OPEN.

## Next highest-leverage work
1. Execute the pipeline against a known MOTION.OS master with declared timeline ground truth.
2. Analyze >=10 heterogeneous references through a corpus runner and persist StyleSignatures.
3. Install/verify OpenCV + Tesseract in the production analysis image and quantify their accuracy, not just availability.
4. Upgrade layout/object tracking beyond OCR-only evidence.
5. Connect compiled Remotion spec to actual Remotion production render and compare output.
6. Feed retrieved StyleSignature into grammar selection, render A/B candidates and measure transfer fidelity vs originality.
