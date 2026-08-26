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
### Vector exact candidates
text, UI cards, icons, lines, paths, circles/rings, masks, clips, badges, counters, pointers.

### Non-vectorizable / hybrid candidates
photographic footage, organic changing texture, film grain, raster plates, complex baked shadows, video montage.

## Output contract
A. `SVG_FRAME_RECON_PLAN`
B. `SVG_ASSET_MAP`
C. `SVG_TIMELINE_FRAME_DATA`
D. actual `SVG_IMPLEMENTATION`
E. max-8 fidelity uncertainty notes
F. capture requirements if needed

## Hard gates
- exact copy strings / line breaks / accents
- stable element IDs
- stable anchors
- absolute coordinate system
- no invented glyph morph
- no invented blur
- no hidden interpolation replacing observable frame behavior
- unknowns explicit

## QA implementation targets
- per-frame SSIM / pixel-diff on rasterized SVG
- bbox error per tracked element
- text string exact match
- coordinate drift max
- timing boundary error in frames
- deterministic replay hash for identical input

## Definition of Done
Reconstruct a known MOTION.OS-generated test scene from exported frames and demonstrate thresholded frame fidelity with a reproducible SVG/JS output and an uncertainty report.

## Learning delta from Phase 04
Phase 04 extraction can become the measurement front-end for reconstruction, but creative `MotionStyle2JSON` labels must never replace exact coordinate/frame evidence.
