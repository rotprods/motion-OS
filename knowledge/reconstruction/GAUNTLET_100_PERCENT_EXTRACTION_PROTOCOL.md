# Gauntlet Protocol — 100% Observable Replicable Action Coverage

## Non-negotiable definition

“100%” means **all observable high-salience replicable actions are mapped or explicitly declared source-locked/unknown**. It never means recovering hidden source-project internals from flattened media.

## Loop G01 — Temporal census

Fail if:
- any decoded frame lacks scene/shot authority;
- any P90 frame-change peak is not covered by an operation;
- any strong scene boundary is unexplained;
- a long hold is treated as missing work instead of a deliberate state when visually supported.

## Loop G02 — Caption + depth

Fail if:
- a caption is represented only as OCR text;
- a hero keyword lacks separate timing/animation semantics;
- foreground/device/subject/background z relationships are missing;
- visible occlusion is not represented;
- source UI is accidentally promoted to a reusable invariant.

## Loop G03 — Motion + transitions

Fail if:
- “pop”, “zoom”, “glitch”, “camera move” are used without temporal bounds;
- apparent crop/reframe is called physical camera movement without evidence;
- major motion peaks have no action;
- transition driver, duration, direction or supporting FX are absent.

## Loop G04 — Audio + retention

Fail if:
- strong audio onsets are ignored;
- SFX semantic identity is claimed as measured without stems;
- high-salience caption/transition events lack audio relationship inspection;
- low-entropy breathing windows are not differentiated from dead editing;
- visual stimulus density is used as a vanity metric without attention hierarchy.

## Loop G05 — Renderer parity

Fail if any action cannot be expressed in AE, Remotion and HyperFrames without inventing a new creative decision.

## Loop G06 — Adversarial missing-action search

Attack the extraction with:
- P90 change peaks;
- P90 optical-flow peaks;
- 3–10 frame micro-events;
- layer order changes;
- sudden caption geometry changes;
- short flashes/blur spikes;
- source-lock leaks;
- static-looking frames whose depth or foreground changed.

Every residual is either:
1. mapped to a new action;
2. merged into an existing action with evidence;
3. marked `UNKNOWN/UNAVAILABLE` with a reason.

## Loop G07 — Coverage closure

Pass only when:
- scene coverage = 100%;
- current measured P90 change peak coverage = 100%;
- current measured P90 motion peak coverage = 100%;
- every action has three renderer mappings;
- no unresolved high-salience event exists;
- unknown source internals are explicit;
- physical reconstruction and generalization are still reported separately.

## Post-closure gauntlet

Observable closure MUST NOT promote the template to canonical. Execute golden-scene physical reconstruction, frame-level diff, repairs, then 3× content substitution.
