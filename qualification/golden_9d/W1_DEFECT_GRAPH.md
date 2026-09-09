# T08-W1 Motion Kinematics — Defect Graph

Authority: append-only gauntlet ledger. A mechanically successful compiler run does not grant motion/easing authority.

## Baseline W1 execution

- head: `79590e022938daa2c3173fe5950ac640af45b248`
- workflow: `Golden 9D Motion Kinematics` run `34384652570` -> SUCCESS
- artifact: `10117222420`
- digest: `sha256:bb380dc0ed28f65011f6744bf7a6b8305df73a4c9f252f85c0f07ace46fde3ad`
- scenes: 4
- entities: 18
- source refs: exact pinned live golden heads

This execution proves parser/compiler/runtime mechanics only. The adversarial review below prevents promotion of its naive centroid-speed interpretation.

## W1-DEF-KIN-001 — bbox centroid motion conflates translation with scale/reveal

- domain: `MOTION KINEMATICS / AUTHORITY TYPE`
- severity: `P0 motion-grammar integrity blocker`
- root-cause family: `VISIBLE_BBOX_SHAPE_CHANGE_CONFLATED_WITH_OBJECT_TRANSLATION`
- counterexamples from baseline artifact:
  - `S11_UI_LIST/pill` first active segment was labeled centroid direction `DOWN`, even though its top edge moves upward while height/width expand strongly. This is a group expansion/build, not defensible downward translation authority.
  - `S16_FACTOR_X/question_mark` first active segment was labeled `DOWN_LEFT`; the source bbox grows from a small partial mark to the full punctuation shape while its top edge rises. Centroid direction is dominated by glyph/scale emergence.
  - `S04_CIENTIFICAMENTE/hero` reports a maximum centroid speed around `119 px/frame` at initial appearance because a partial visible bbox becomes the full hero word. Treating that as physical translation would be false motion grammar.
- rejected repair: change thresholds until expected verbal labels appear.
- architecture repair:
  1. preserve centroid/edge/size deltas as separate measured observables;
  2. classify each step/segment as `TRANSLATION_DOMINANT`, `SCALE_OR_REVEAL_DOMINANT`, `MIXED_TRANSFORM` or `STATIC_OR_MICRO`;
  3. when bbox-shape change dominates, cap translation/easing confidence and attach `BBOX_SHAPE_CHANGE_CONFLATES_TRANSLATION_WITH_SCALE_OR_REVEAL`;
  4. never infer a physical object/camera trajectory from centroid displacement alone.
- status: `OPEN_PENDING_COMPILER_V3 + REGRESSION`.

## W1-DEF-KIN-002 — screen-boundary clipping distorts bbox kinematics

- domain: `VISIBLE OUTPUT / SCREEN CLIPPING`
- severity: `P1 curve-authority integrity`
- observed: S14 outgoing/incoming cards/headings repeatedly touch x=0 / viewport boundaries. Their visible bbox shrinks as pixels leave frame.
- root-cause family: `SCREEN_BOUNDARY_CLIPPING_DISTORTS_BBOX_KINEMATICS`.
- pre-run architecture repair already present in v2 compiler: mark clipping per sample/segment, cap curve confidence LOW and use authority `VISIBLE_OUTPUT_CLIPPED_PROXY_NOT_HIDDEN_OBJECT_CURVE`.
- baseline proof: S14 entities report nonzero `boundary_clipped_sample_count` and clipped segments carry the caveat.
- status: `MITIGATED / MUST_REMAIN_PERMANENT_TEST`.

## W1-DEF-KIN-003 — sparse keyframe interpolation can manufacture a speed profile

- domain: `SOURCE RESOLUTION / EASING`
- severity: `P1 easing-authority integrity`
- scenes: S04, S11, S14.
- root-cause family: `KEYFRAME_LINEAR_RENDERER_PROJECTION_MISTAKEN_FOR_ORIGINAL_EASING`.
- baseline compiler explicitly caps all such curve proxies LOW and labels them `RENDERER_PROJECTION_BEHAVIOR_PROXY_NOT_MEASURED_ORIGINAL_EASING`.
- only full-frame/no-interpolation evidence such as S16 can support stronger behavioral curve confidence, and even there bbox-shape/clipping/source-lock caveats still apply.
- status: `MITIGATED / MUST_REMAIN_PERMANENT TEST`.

## W1-DEF-KIN-004 — source-lock reflow can contaminate reusable motion grammar

- domain: `SOURCE LOCK / TEMPLATE GENERALIZATION`
- severity: `P1 structural-template integrity`
- scene: S16 local `87..91`.
- root-cause family: `SOURCE_NATIVE_REFLOW_PROMOTED_TO_EDITORIAL_GRAMMAR`.
- source evidence: late global upward movement coincides with Reels UI reveal; causal editorial origin remains UNKNOWN.
- repair: exact visible kinematics remain measurable, but every S16 entity marks local87..91 as `structural_template_eligible=false` and affected segments carry `SOURCE_LOCK_RANGE_EXCLUDED_FROM_STRUCTURAL_MOTION_GRAMMAR`.
- status: `MITIGATED / MUST_REMAIN PERMANENT TEST`.

## Promotion state

After baseline W1 run:

`MOTION_KINEMATICS_COMPILER_EXECUTED = true`

but:

`MOTION_DIMENSION_QUALIFIED = false`
`EASING_AUTHORITY_QUALIFIED = false`

Next action: implement W1-DEF-KIN-001 repair, rerun the same pinned four-scene compiler, adversarially inspect transform-class and curve-authority outputs, then produce a dimension qualification rather than relying on raw metrics.
