# Phase 03 Plan — Exact Frame Reconstruction

## Goal
Provide a deterministic reconstruction mode separate from creative generation:

```text
video / PNG sequence
→ frame evidence
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
- GOOD: MP4 + reliable metadata
- WEAK: sparse screenshots
- DESCRIPTION ONLY: cannot claim exactness

## Reconstruction representations
- full per-frame state map
- dense keyframes + explicit interpolation exceptions
- hybrid: per-frame for high-motion/text/cursor; keyframes for stable transforms

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
Exact strings/line breaks, stable IDs/anchors, absolute coordinates, no invented glyph morph or blur, no hidden interpolation, explicit unknowns.

## Implemented after Gauntlet 10X
- `src/reconstruction/fidelity.py`: per-element, per-frame and timeline fidelity metrics.
- hard text-integrity and persistent-ID checks.
- frame-count exactness and numeric state RMSE.
- deterministic encoding policy: typing/high motion → per-frame; stable content → dense/hybrid.
- `src/reconstruction/svg_player.py`: actual SVG+JS deterministic frame player using persistent IDs and embedded timeline JSON.
- unit tests for zero-error exact replay and text-integrity regression.

## Remaining hard proof
- reconstruct a known MOTION.OS scene from exported PNG frames.
- rasterize emitted SVG and compute pixel/SSIM comparison.
- measure bbox/timing errors against ground truth.
- deterministic replay hash across two independent runs.

## Definition of Done
Reconstruct a known test scene from exported frames and demonstrate thresholded frame fidelity with reproducible SVG/JS output and uncertainty report.

## Learning delta from Phase 04
Phase 04 extraction can provide measurements, but creative MotionStyle2JSON labels never substitute frame-exact coordinate evidence.

## Learning delta from Gauntlet 10X
The reconstruction vertical now has an executable fidelity gate and player. The remaining problem is empirical source reconstruction, not representation design.
