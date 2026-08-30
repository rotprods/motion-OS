# MOTION.OS — Reverse Engineering Atomic Action Ontology v2

## Purpose

Evidence/intermediate contract for decomposing flattened reference video into renderer-independent editing operations. It projects into the existing MOTION.OS `TypedEditingGraph`; it is **not** a competing graph authority.

## Operation hierarchy

An **action** is the smallest useful semantic editing operation unless the visible behavior contains independently timed children. In that case the action is a parent grouping and each child becomes a `subevent`.

Examples:
- hero word scaling 84% → 112% → 100%;
- continuous count-up over many frames;
- phone precomp scaling/reframing;
- 4-frame RGB/white glitch bridge;
- UI list parent with independent word/row child events;
- five example cards entering in stagger;
- Factor-X editorial hold while source-native face/body movement continues underneath.

## Mandatory parent fields

`action_id`, `scene_id`, `start_frame`, `impact_frame`, `end_frame`, `domain`, `verb`, `target`, `function`, `parameters`, `audio_link`, `z_role`, `authority`, `confidence`, `evidence_refs`, `renderer_mapping`.

Optional but canonical v2 semantics:
- `temporal_mode`
- `motion_origin`
- `subevents[]`

## Temporal modes

- `discrete` — bounded action with meaningful start/impact/settle anchors.
- `continuous` — behavior spans a window; internal metric peaks do not imply extra editorial keyframes.
- `staggered` — semantic parent with independently timed visible children; explicit subevents required.
- `hold` — deliberately stable editorial state.
- `compound` — inseparable cluster of transition/FX mechanisms.
- `source_native` — movement belongs to underlying footage/plate rather than the edit.

## Motion origin

- `editorial` — caused by editing/compositing/motion design.
- `source_native` — facial/body/camera/object motion baked into source plate.
- `mixed` — both editorial and source-native motion visibly coexist.
- `unknown` — cannot be separated from flattened evidence.

This distinction prevents optical-flow peaks from being falsely converted into motion-design operations.

## Subevent contract

Each subevent records:
`subevent_id`, `start_frame`, `impact_frame`, `end_frame`, `verb`, `target`, `parameters`, `authority`, `confidence`, `evidence_refs`.

Subevents must be temporally contained by the parent. A `staggered` parent without subevents fails validation.

Typical subevents:
- each word in progressive kinetic copy;
- each UI list row;
- each card/icon/metric bubble in a stagger;
- each synchronized SFX accent when distinct timing is evidenced.

## Domains

`transition`, `caption`, `typography`, `motion`, `camera`, `object`, `depth`, `background`, `fx`, `audio`, `source_lock`.

## Authority

`measured`, `measured_heuristic`, `measured_visible`, `evidence_bound_inference`, `inferred_from_mixed_audio`, `assumption`, `unknown`.

## Function taxonomy

Functions describe why the operation exists:
`hook`, `disclose_information`, `semantic_emphasis`, `direct_attention`, `pattern_interrupt`, `connect_states`, `preserve_continuity`, `prove_system_behavior`, `establish_depth`, `create_breathing_window`, `synchronize_audio`, `reward`, `payoff`, `source_fidelity`.

## Source locks

`verb=source_lock` preserves source-specific content in `RECONSTRUCT_EXACT` only. Structural/style templates strip or slot it.

Examples: Instagram/Reels chrome, literal screenshots, speaker footage, exact source copy, licensed artwork.

## Renderer mapping rule

Every observable parent action must provide After Effects, Remotion and HyperFrames implementations. Subevents inherit the parent renderer target unless a target-specific override is later required by evidence.

Renderer mappings describe implementation mechanisms; they may not change timing, hierarchy, z-order or transition semantics.

## Peak adjudication

Measured frame-change/flow peaks are not automatically editor actions. Each residual is adjudicated as:
- `anchored` — near parent/subevent key timing;
- `continuous` — inside a declared continuous operation;
- `source_native` — attributable to source footage/plate;
- `unexplained` — blocks observable closure.

## Graph projection

`Scene → CONTAINS → OperationProjection`

`OperationProjection → COMPILES_TO → AfterEffects/Remotion/HyperFrames`

Parent/subevent hierarchy remains evidence metadata or typed projection detail; canonical semantic/editing truth remains MOTION.OS `TypedEditingGraph`.
