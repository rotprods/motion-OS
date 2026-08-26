# Phase 03 Plan — Exact Frame Reconstruction

## Goal
Provide a deterministic reconstruction mode separate from creative generation:

```text
video / PNG sequence
→ physical frame evidence
→ vector/raster segmentation
→ persistent element tracking
→ absolute coordinate reconstruction
→ per-frame/dense-keyframe timeline
→ SVG/SVG+JS/hybrid implementation
→ frame-diff fidelity QA
```

## Optimizer priority
1. frame fidelity
2. text integrity
3. geometric consistency
4. timing fidelity
5. deterministic replay
6. compactness only after fidelity

## Inputs by confidence
- BEST: PNG frame sequence + fps + resolution + duration
- GOOD: MP4 + reliable metadata + physical decode
- WEAK: sparse screenshots
- DESCRIPTION ONLY: cannot claim exactness

## Reconstruction representations
- full per-frame vector state map
- dense vector keyframes + explicit interpolation exceptions
- hybrid: per-frame for high-motion/text/cursor; keyframes for stable transforms
- **exact raster-sequence baseline** for genuinely non-vectorizable regions/source frames

## Layer classification
Vector exact candidates: text, UI cards, icons, lines, paths, circles/rings, masks, clips, badges, counters, pointers.
Hybrid candidates: footage, changing organic texture, grain, raster plates, baked shadows and montage content.

## Output contract
A. SVG_FRAME_RECON_PLAN
B. SVG_ASSET_MAP
C. SVG_TIMELINE_FRAME_DATA
D. SVG_IMPLEMENTATION
E. fidelity uncertainties
F. capture requirements

## Hard gates
Exact strings/line breaks, stable IDs/anchors, absolute coordinates, no invented glyph morph or blur, no hidden interpolation, explicit unknowns, content-addressed source evidence.

## Implemented after Gauntlet 10X
- `src/reconstruction/fidelity.py`: per-element, per-frame and timeline fidelity metrics.
- hard text-integrity and persistent-ID checks.
- frame-count exactness and numeric state RMSE.
- deterministic encoding policy: typing/high motion → per-frame; stable content → dense/hybrid.
- `src/reconstruction/svg_player.py`: actual SVG+JS deterministic frame player using persistent IDs and embedded timeline JSON.
- unit tests for zero-error exact replay and text-integrity regression.

## Implemented in Real Analysis Superwave
- Phase 04 now provides physical FFmpeg-decoded frames with SHA256 identity as a common evidence root.
- `src/reconstruction/raster_sequence.py` implements an explicit `exact_raster_sequence` fallback for non-vectorizable frames.
- every raster frame retains frame number, timestamp, file path and source SHA.
- timeline gets a deterministic SHA256.
- emitted HTML/JS player displays exact frame assets without adding blur/morph/easing.
- `verify_raster_records()` fails if a source frame mutates after timeline creation.

This is deliberately called **raster-sequence reconstruction**, not vector reconstruction. It establishes a fidelity floor and cleanly separates “exact replay” from “successful vectorization”.

## Remaining hard proof
- reconstruct a known MOTION.OS vectorizable scene from exported PNG frames.
- segment vectorizable vs raster layers and replace raster baseline layers progressively with actual SVG elements.
- rasterize emitted vector/hybrid output and compute pixel/SSIM comparison against source frames.
- measure bbox/timing errors against ground truth.
- deterministic replay hash across two independent runs/environments.

## Definition of Done
Reconstruct a known test scene from exported frames and demonstrate thresholded frame fidelity with reproducible SVG/JS or justified hybrid output and uncertainty report. A 100% raster replay alone does **not** satisfy the vector reconstruction objective; it only satisfies the non-vectorizable fallback contract.

## Learning delta from Phase 04
Phase 04 measurements can accelerate segmentation/tracking, but creative MotionStyle2JSON labels never substitute exact coordinate/frame evidence.

## Learning delta from Gauntlet 10X
The reconstruction vertical gained an executable fidelity gate and SVG player. The remaining problem became empirical source reconstruction.

## Learning delta from Real Analysis Superwave
The exactness chain now begins at content-addressed physical frames rather than abstract measurements. New strategy:

```text
physical frame evidence
→ exact raster baseline
→ identify vectorizable layers
→ replace one layer family at a time with SVG
→ rasterize candidate
→ compare to source
→ keep replacement only if fidelity remains inside gate
```

This gives the Gauntlet a monotonic reconstruction path: compactness/vectorization can improve only after fidelity is protected.
