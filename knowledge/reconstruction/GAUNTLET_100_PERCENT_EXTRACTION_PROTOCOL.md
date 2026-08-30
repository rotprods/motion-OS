# Gauntlet Protocol — 100% Observable Replicable Action Coverage

## Non-negotiable definition

“100%” means **all observable high-salience replicable actions are mapped or explicitly declared source-locked/unknown**. It never means recovering hidden source-project internals from flattened media.

The gauntlet must attack both **coverage** and **granularity**. A broad parent action that spans a visible sequence is insufficient when exact replication requires child timings.

## G01 — Temporal census

Fail if:
- any decoded frame lacks scene/shot authority;
- any P90 frame-change peak is not covered;
- any strong scene boundary is unexplained;
- a deliberate hold/breathing state is mislabeled as missing editing.

## G02 — Caption + depth

Fail if:
- caption exists only as OCR/subtitle text;
- hero keyword lacks independent geometry/timing;
- foreground/device/subject/background z relationships are missing;
- visible occlusion is not represented;
- source UI leaks into reusable DNA.

## G03 — Motion + transitions

Fail if:
- `pop/zoom/glitch/camera move` has no bounded timing;
- crop/reframe is falsely claimed as physical camera motion;
- major motion peaks have no operation;
- transition driver/duration/direction/FX are absent.

## G04 — Audio + retention

Fail if:
- strong mixed-audio onsets are ignored;
- SFX semantic class is claimed as measured without stems;
- hero caption/transition events lack audio relationship review;
- low-entropy resets are confused with dead editing;
- stimulus density is used without attention hierarchy.

## G05 — Renderer parity

Fail if any operation cannot be expressed in After Effects, Remotion and HyperFrames without inventing a new creative decision.

## G06 — Adversarial missing-action search

Attack with:
- P90 change/flow peaks;
- 3–10 frame events;
- layer-order changes;
- sudden caption geometry changes;
- flashes/blur spikes;
- source-lock leaks;
- static-looking frames whose foreground/depth changes.

Every residual becomes:
1. a new operation/subevent;
2. evidence attached to an existing operation;
3. explicit `UNKNOWN/UNAVAILABLE`.

## G07 — First coverage closure

Pass only when:
- scene coverage = 100%;
- current P90 frame-change peak coverage = 100%;
- current P90 motion peak coverage = 100%;
- renderer mapping coverage = 100%;
- no unresolved P90 high-salience event remains;
- unknown internals explicit.

This gate is necessary but not sufficient.

## G08 — Subaction granularity

Attack broad actions that can hide multiple editor operations.

### Staggered
`staggered` actions MUST expose child `subevents`, one per independently timed visible unit whenever evidence supports it.

Examples:
- word-by-word progressive copy;
- UI list rows;
- card sequences;
- metric bubbles;
- icon cascades;
- sound accents tied to those child events.

### Continuous
A `continuous` action represents behavior spanning the window, e.g. a count-up or deterministic tracking/reframe. Do not manufacture point keyframes solely to explain internal metric peaks.

### Source-native
Separate plate/subject motion from editorial motion. Facial/body movement, baked camera movement or movement inside embedded footage can be `source_native` or `mixed`; it is not automatically a motion-design operation.

Fail if a broad parent range is the only explanation for visibly separable child events.

## G09 — Low-threshold residual review

Repeat peak adjudication below P90:
- required: P80 and P75 for frame-change and optical-flow metrics;
- recommended during calibration: P70/P65/P60 until residual discovery stops adding meaningful editor actions.

For each peak, status must be one of:
- `anchored` — close to an action/subevent start/impact/end;
- `continuous` — inside a declared continuous action;
- `source_native` — attributable to the underlying footage/plate;
- `unexplained` — FAIL.

An `unexplained` residual blocks `OBSERVABLE_ACTION_CLOSED`.

## Current first-specimen outcome

The first professional specimen caused G08/G09 to be added. The first P90-only pass hid four important classes:
- internal count-up activity;
- progressive UI-word/row timings;
- example-card child events;
- source-native motion during the Factor X hold.

After subevent/continuous/source-native modeling, the v2 inventory has 98 parent actions + 32 explicit subevents (121 leaf operations under the current leaf-count convention). Local residual attack is closed through P70 on the current frame-change/flow measurements; exact repository/clean-runner and physical reconstruction gates remain separate.

## Post-observable closure

Observable closure MUST NOT promote the template to canonical. Execute:

`freeze graph → golden-scene physical reconstruction → frame-level diff → graph-native defects/repairs → repeat → 3× substituted-content generalization`
