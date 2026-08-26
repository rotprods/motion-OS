# MOTION.OS — Real Analysis Superwave — 2026-08-26

Status: IMPLEMENTED / PR VALIDATION

## Mission
Move the Visual-DNA system from algorithm contracts to physical MP4 evidence and an executable end-to-end path.

## What changed

### 1. Physical evidence root
`FFprobe` remains technical metadata authority. `FFmpeg` now physically decodes the video to analysis PNG frames. Each retained evidence frame is SHA256-addressed.

This removes the previous gap where segmentation/keyframe algorithms accepted scores/plans but did not own physical frame evidence.

### 2. Real cut measurement
Adjacent decoded frames are reduced deterministically and compared through luminance + edge-structure deltas. A robust threshold is derived from median/MAD, then fed into the existing contiguous shot segmenter.

### 3. Real optional vision providers
- OpenCV Farneback dense optical flow: global dx/dy, local residual, camera-likelihood.
- Tesseract OCR: exact observed string, confidence, normalized bbox, evidence frame.
- deterministic OCR tracking: persistent continuity IDs across nearby frames/positions.
- FX/material V1: pixel-level contrast, edge, blur-proxy and highlight measurements; material remains explicitly inferred.

Provider absence is not silently converted into measured empty data.

### 4. Real audio evidence
FFmpeg decodes mono PCM. The provider measures RMS envelope and positive-energy transient/onset candidates. These are not called semantic music beats. Whisper is optional and exposes unavailable/failed states explicitly.

### 5. End-to-end orchestrator
`src/extraction/pipeline.py` now executes:

```text
MP4
→ FFprobe
→ FFmpeg frames
→ cut scores
→ shots
→ keyframes + SHA
→ color/layout/OCR/flow/FX/audio
→ FeaturePack schema gate
→ evidence-bound MotionStyle2JSON schema gate
→ Remotion scene-spec compiler
→ exact coverage gate
→ JSON + TypeScript artifacts
```

### 6. Ground-truth benchmark
The benchmark reports:
- cut precision / recall / F1
- boundary error in frames
- palette RGB distance
- OCR recall
- evidence/warning counts

It intentionally has no global `quality_score`.

### 7. Real encoded-MP4 CI fixture
The E2E test constructs 90 known frames in three 30-frame scenes, encodes them with real FFmpeg/H.264, runs the generated MP4 through the analysis pipeline and requires recovery of the two hard cuts at frames 30 and 60 to <=1-frame boundary error. It then requires schema-valid FeaturePack/MotionStyle and exact 90-frame Remotion scene coverage.

This is ground-truth extraction evidence, not creative-quality evidence.

### 8. Corpus + retrieval bridge
A corpus runner now analyzes directory trees, persists evidence-bound StyleSignatures in SQLite and reports coverage/failure/retrieval diagnostics. `StyleSignature v1` uses an inspectable measured vector based on color, motion, FX, shot rate, layout and audio density.

Self top-1 retrieval is only a deterministic integrity sanity check. Semantic retrieval quality still needs human/corpus labels.

## CI evidence before documentation delta
PR #32 head `ba2479da...` passed:
- CI Python 3.11
- CI Python 3.12
- Repo Health
- Security Baseline

After this documentation/corpus delta, the PR must pass all gates again before merge.

## Major learnings
1. `provider unavailable` is a valid state and belongs in the evidence graph.
2. A fallback must never gain higher authority than the signal it replaces.
3. Physical frame SHA is the useful root for visual claims and future reconstruction lineage.
4. Synthetic ground truth is excellent for extractor correctness but cannot validate real-world style classification.
5. Retrieval needs an inspectable baseline before introducing opaque multimodal embeddings.
6. Scene coverage and schema validity are compiler correctness, not production rendering proof.
7. MotionStyle is inference over measurements; it must never erase the measurement pack.
8. Audio events and visual events can now share exact timestamps in the same evidence graph.

## Current vertical scorecard — maturity, not creative quality
| Vertical | Before | After | Remaining hard proof |
|---|---|---|---|
| physical video ingest | core only | real FFmpeg E2E | historical master |
| shot/keyframe evidence | planned algorithm | encoded-MP4 ground truth | heterogeneous cuts/transitions |
| color | deterministic core | physical pixels | perceptual calibration |
| OCR | interface gap | real optional provider + tracking | production install + multilingual accuracy |
| motion | trajectory core | real optional optical flow | production install + camera/object labels |
| FX/material | open | measured heuristic V1 | classifier/calibration |
| audio | metrics only | physical PCM/onsets + optional Whisper | transcript/beat verification |
| FeaturePack | implemented | physical E2E | 10+ corpus |
| normalization | implemented | physical E2E | taxonomy accuracy labels |
| Remotion compiler | implemented | physical E2E spec | actual render |
| style retrieval | SQLite core | measured signature/corpus runner | human relevance judgments |
| exact reconstruction | V1 | benefits from physical evidence root | SVG rasterized frame-fidelity benchmark |
| creative release | blocked | blocked | temporal critic + >=9 |

## Remaining critical path
1. Obtain/use a known historical MOTION.OS MP4 and declared timeline; run `scripts/analyze_video.py --ground-truth`.
2. Populate a >=10 heterogeneous corpus and run `scripts/analyze_corpus.py`.
3. Production-enable OpenCV/Tesseract and score them against labeled samples.
4. Connect MotionStyle/Remotion spec to a real Remotion runtime composition/render.
5. Compare generated output against source/system intent with temporal multimodal critic.
6. Close the learning loop: retrieve StyleSignature → compile grammar/motion_system → render → critic → Gauntlet.

## Anti-overengineering decision
Do not add Qdrant/Pinecone/Weaviate, orchestration services or distributed queues yet. Current bottlenecks are empirical accuracy and production runtime proof, not storage scale.
