# Exact Frame Reconstruction Canon — SVG / SVG+JS

## Mission
Given a video, image sequence or frame references, reconstruct animation as exact SVG, SVG+JS, or a declared hybrid while prioritizing source fidelity over style imitation.

## Priority
1. frame fidelity
2. text integrity
3. geometric consistency
4. timing fidelity
5. deterministic replay
6. compactness only after fidelity is preserved

## Modes
- `per_frame`: explicit state for every frame
- `dense_keyframes`: dense keys only where interpolation is proven equivalent
- `hybrid`: per-frame for high-motion/text/cursor/clicks; keyframes for stable transforms

## Hard rules
- preserve text exactly: content, case, accents, punctuation, line breaks
- never morph letters unless visible in source
- do not blur text unless visible in source
- persistent elements keep persistent IDs
- stable absolute coordinate space using viewBox pixels
- no coordinate/scale/style drift
- unknowns must be explicit
- exact requests may not be replaced by generic easing descriptions
- if exactness needs per-frame data, output per-frame data

## Layer classification
### Vectorizable
- text
- UI cards
- icons
- lines/strokes
- rectangles
- circles/rings
- simple paths
- masks/clips
- cursors
- badges
- counters

### Non-vectorizable / hybrid candidates
- photographic footage
- organic/changing texture
- film grain/noise plates
- montage footage
- complex baked shadows
- blur-heavy raster plates

For non-vectorizable regions route to one of:
1. embedded raster frame sequence masked by SVG
2. HTML canvas/video layer + SVG overlay
3. vector approximation only when explicitly permitted

## Input quality hierarchy
Best: PNG frame sequence + fps + resolution + duration.
Good: MP4 + reliable fps + target dimensions.
Weak: textual description; all unsupported geometry/timing becomes unknown and cannot be labeled exact.

## Segmentation
Partition timeline by motion characteristics:
- static
- low_motion
- high_motion
- typing
- cursor/click
- raster-heavy
- transition boundary

Each segment receives encoding policy: per_frame | dense_keyframes | hybrid.

## Strict output order
A. `SVG_FRAME_RECON_PLAN` (YAML)
B. `SVG_ASSET_MAP` (YAML/JSON)
C. `SVG_TIMELINE_FRAME_DATA` (JSON)
D. `SVG_IMPLEMENTATION` (real SVG/HTML/CSS/JS)
E. Fidelity Notes — uncertainties only, max 8 bullets
F. Next Capture Requirements — only if needed, max 6 bullets

## Core plan schema
```yaml
SVG_FRAME_RECON_PLAN:
  meta:
    title:
    mode: exact_frame_reconstruction
    source_type: video|frame_sequence|description
    duration_s:
    fps:
    total_frames:
    aspect_ratio:
    resolution: [width, height]
    coordinate_space:
      viewBox: [0, 0, width, height]
      units: px
  reconstruction_policy:
    priority: frame_fidelity
    text_integrity: strict
    no_drift: strict
    interpolation_policy: minimal_only
    unknown_policy: explicit
  segmentation: []
  persistent_elements: []
  qa_gates: []
```

## Frame data minimum
Each element state may include:
- visible
- x/y/w/h
- opacity
- translate/scale/rotate
- fill/stroke/strokeWidth/blur
- exact text state
- cursor state where applicable

## Implementation policy
Use:
1. pure SVG + SMIL/CSS for truly simple short motion;
2. SVG + JS frame player for exact frame-state playback;
3. HTML + SVG overlay + JS/canvas/video for mixed vector/raster scenes.

For large exact timelines, embed compact JSON and drive stable element IDs via a deterministic frame runner.

## Fidelity QA
Required gates:
- frame registration error
- bbox error by persistent element
- text exact-string equality
- anchor drift
- transform drift
- style-token drift
- timing offset
- visibility mismatch
- raster/vector classification correctness

Exact reconstruction is RELEASED only when unknown regions are either resolved or explicitly accepted as non-exact.