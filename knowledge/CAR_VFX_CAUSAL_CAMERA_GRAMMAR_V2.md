# CAR VFX Causal Camera Grammar v2

Source provenance: Roberto-supplied Google Drive document `CAR VFX`, reviewed 2026-09-18. This file captures durable operational rules; it does not preserve vendor-specific prose as authority.

## Purpose
Convert automotive VFX/editing intent into parameterizable, evidence-bound camera and transition contracts suitable for forensic analysis, MotionStyle2JSON, deterministic compositing, and generative-video compilation.

## Core invariant
A transition is not merely an effect label. It must explain both:
1. what the viewer perceives in screen space; and
2. what physically/causally happens in scene space.

No magical camera. Every claimed movement must be representable with parameters or explicitly marked inferred/unknown.

## Automotive camera grammar
Canonical recurring primitives:
- `center_lock`: keep the hero/feature anchored while camera/world vectors change.
- `arc_pan`: camera travels around a defined pivot/hero with compensating yaw.
- `parallax_around_hero`: background/foreground displacement differs while hero remains controlled.
- `dolly_in` / `dolly_out`: explicit Z trajectory.
- `side_motion_blur`: directional edge blur tied to measured/declared motion vector.
- `speed_ramp_in` / `speed_ramp_out`: acceleration/deceleration curve, never a vague “dynamic” instruction.
- `rotoscope_feature`: tracked isolation of emblem, wheel, watch, aperture, body feature, etc.
- `detach_feature`: isolated feature separates from its source plane with explicit depth/occlusion behavior.
- `aperture_transition`: a tracked feature or generated opening becomes the geometric passage to the incoming scene.
- `refocus`: explicit focus-plane transfer between subjects/depth layers.

## Required 6DoF representation
When evidence supports camera motion, capture:
- position: `x`, `y`, `z`
- orientation: `yaw`, `pitch`, `roll`
- pivot/target id
- screen-space anchor
- start/end values or trajectories
- easing/velocity curve
- confidence + evidence refs

For the hero/object, use the same 6DoF representation when it moves independently.

## Causal transition contract
Every non-trivial automotive transition should be decomposed into:

### 1. Approach
- camera trajectory
- hero lock / pivot
- focus state
- initial velocity

### 2. Feature acquisition
- tracked feature id
- roto/mask topology
- feature screen coverage
- confidence/evidence

### 3. Transformation
- detach/deform/open/reveal operation
- object depth relationship
- occlusion progression
- FX tied to concrete channels

### 4. Crossing
- camera crosses aperture/occluder plane or the occluder reaches full screen coverage
- outgoing scene reaches defined occlusion threshold
- incoming scene is spatially/perceptually registered behind the transition surface

### 5. Handoff
- incoming motion vector matches or intentionally contrasts outgoing vector
- center lock/pivot is transferred or released explicitly
- focus plane transfers explicitly

### 6. Resolve
- speed ramp decelerates or settles
- blur returns to baseline
- hero lock stabilizes
- distortion returns to zero unless evidence says otherwise

## Minimum transition telemetry
For every transition, capture where measurable:
- `camera_6dof`
- `hero_6dof`
- `focus_plane`
- `occlusion_pct`
- `mask_topology`
- `screen_anchor`
- `motion_vector`
- `speed_curve`
- `motion_blur`
- `incoming_scene_relation`
- `audio_impulse`
- `evidence_refs`
- `confidence`

Unknown values must remain null/unknown; never fabricate precision.

## Aperture-transition example contract
```yaml
approach:
  camera_motion: dolly_in
  hero_lock: true
feature:
  target: wheel_or_emblem
  tracking: evidence_bound
camera:
  x: arc_component
  y: stable_or_measured
  z: accelerate_toward_feature
  yaw: compensate_to_center_lock
  pitch: measured_or_null
  roll: 0_or_measured
transition:
  feature_screen_coverage: increasing
  occlusion_pct: 0_to_100
  motion_blur: directional_edges
  speed_curve: accelerate_into_crossing
handoff:
  crossing_plane: feature_aperture
  incoming_scene_relation: behind_aperture
  motion_vector_match: required_or_explicitly_broken
resolve:
  speed_curve: decelerate
  center_lock: recover_or_transfer
  distortion: zero_unless_evidenced
```

## Refocus contract
A refocus event is not `blur_in`. It requires:
- source focus target/depth
- destination focus target/depth
- focus transition start/end frame
- foreground/background blur evolution
- camera/object motion during pull
- confidence/evidence

## Forensic completeness
MotionStyle2JSON already requires >=12 micro-choreography steps per shot unless justified. Automotive forensic shots additionally require that meaningful camera/hero/occlusion/focus changes be represented as separate atomic events rather than collapsed into prose.

## Image-to-video boundary-condition rule
Reference images used for generative video are boundary conditions of a plausible spatial trajectory, not merely attractive keyframes. Adjacent references must preserve:
- hero identity and geometry;
- plausible camera orbit/dolly continuity;
- compatible screen-space anchors;
- transition-surface geometry;
- incoming/outgoing motion vectors;
- lighting/time continuity unless a deliberate transition changes them.

## Anti-drift / failure modes
Reject or flag:
- impossible camera teleportation;
- center-lock claims without a defined target;
- speed ramps without a velocity/temporal interval;
- motion blur unrelated to motion direction;
- portal/aperture transitions with no crossing/occlusion logic;
- incoming scene that cannot plausibly exist behind the transition surface;
- fake warp used instead of Z motion for macro/dolly behavior;
- roto/detach without tracked feature identity;
- unexplained distortion;
- generative interpolation that changes vehicle identity/body geometry.

## Compiler principle
A downstream Seedance/gen-video prompt should be compiled from these contracts. Prefer explicit trajectory + pivot + crossing + resolve instructions over adjectives such as “cinematic”, “smooth” or “dynamic”.
