# Professional Motion System Canon

## Thesis
Motion graphics are design in motion. Professional quality comes from a system, not isolated prompts or effects.

## Studio pipeline
1. Reference mining: collect ~20 references and extract repeated structural patterns rather than aesthetic imitation.
2. Reverse engineering: identify layers, persistent elements, repeated motion patterns, visual hierarchy, transition logic, opening/closing behavior.
3. Lock `motion_system` tokens and rules before rendering.
4. Translate copy into visual behavior rather than animating sentences literally.
5. Segment into scenes with one objective and one dominant event per scene.
6. Compile scenes to structured renderer instructions (YAML/JSON) with layers, timeline, events, easing, sound and restrictions.
7. Run professional QA; failed gates trigger rebuild/repair rather than threshold relaxation.

## motion_system contract
### Tokens
- spacing scale
- radius scale
- typography roles
- palette
- grid
- shadow/material rules
- camera space
- easing registry

### Hard rules
- no drift
- text integrity
- no destructive blur on text unless source requires it
- stable geometry and anchor points
- one dominant idea per beat
- every entrance/transition must have semantic intent
- persistent IDs for persistent objects
- continuity must be transformation-led: nothing appears arbitrarily when a motivated transform can connect states

### Pattern registry examples
- typing
- split
- expand
- collapse
- panel seed -> full card
- collect -> condense -> brand
- reward unlock
- audio pulse
- UI module build
- object -> behavior -> system

## Semantic translation layer
Copy is converted into behavior. Examples:
- copiloto -> secondary supporting panel
- autonomía -> central controlling node
- productividad -> parallel branching
- cuello de botella -> geometric narrowing
- crecimiento -> expansion / graph propagation
- coordinación -> synchronized modules
- decisión -> convergence / selection / lock state

The planner MUST create `semantic_behavior_map` before primitive selection.

## Scene contract
Each scene/beat must define:
- objective
- information priority
- dominant event
- persistent elements from previous scene
- transform into next scene
- duration
- camera behavior
- sound events
- text content
- QA invariants

For generative-video renderers, obey model-specific maximum sequence durations rather than assuming a universal limit. If a source workflow uses 12s/15s chunks, store that as renderer capability metadata, not as a global product law.

## Reference analysis policy
Do not ask a critic whether a reference is 'good'. Extract:
- opening grammar
- hierarchy order
- invariants
- repeated transition families
- pacing distribution
- final-hold strategy
- geometric continuity
- text treatment
- material behavior
- camera space

Reference output becomes rules/Visual DNA, never a blind style-copy instruction.

## Professional QA
Mandatory dimensions:
- drift
- text sharpness/integrity
- geometry consistency
- hierarchy-under-motion
- transition motivation
- motion intent
- pacing / beat focus
- unnecessary visual noise
- brand/system coherence
- audio-event alignment
- final-hold stability

Failure policy: repair or rerender. Never lower the standard to make a candidate pass.

## Product implication for MOTION.OS
MOTION.OS supports two different objectives:
1. GENERATE: synthesize an original motion piece from brief + references + grammar.
2. RECONSTRUCT: reproduce source behavior as faithfully/deterministically as input evidence allows.

These objectives MUST NOT share the same optimizer. GENERATE optimizes professional design quality and semantic communication. RECONSTRUCT optimizes frame fidelity and deterministic geometry.