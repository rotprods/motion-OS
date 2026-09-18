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

This execution proved parser/compiler/runtime mechanics only. The adversarial review below prevented promotion of its naive centroid-speed interpretation.

## W1-DEF-KIN-001 — bbox centroid motion conflates translation with scale/reveal

- domain: `MOTION KINEMATICS / AUTHORITY TYPE`
- severity: `P0 motion-grammar integrity blocker`
- root-cause family: `VISIBLE_BBOX_SHAPE_CHANGE_CONFLATED_WITH_OBJECT_TRANSLATION`
- baseline counterexamples:
  - `S11_UI_LIST/pill` initially appeared to move centroid `DOWN` while its top edge moved upward and width/height expanded strongly;
  - `S16_FACTOR_X/question_mark` initially appeared `DOWN_LEFT` while a partial punctuation bbox was growing into the full visible mark;
  - `S04_CIENTIFICAMENTE/hero` produced a ~119 px/frame centroid jump when a partial visible bbox became the full hero word.
- rejected repair: tune thresholds until labels match human expectations.
- architecture repair:
  1. preserve centroid, four edge deltas, size deltas and opacity proxy separately;
  2. classify each step/segment as `TRANSLATION_DOMINANT`, `SCALE_OR_REVEAL_DOMINANT`, `MIXED_TRANSLATION_AND_SCALE`, or `STATIC_OR_MICRO`;
  3. cap centroid-speed/easing authority whenever bbox shape/reveal materially contributes;
  4. never infer physical object/camera direction from centroid displacement alone.
- permanent regressions: synthetic bbox-growth and visibility-build fixtures in `tests/test_golden_9d_motion_kinematics.py`.
- post-repair examples:
  - S11 pill initial segment -> `SCALE_OR_REVEAL_DOMINANT`;
  - S16 question initial segment -> `SCALE_OR_REVEAL_DOMINANT`;
  - S04 hero initial segment -> `SCALE_OR_REVEAL_DOMINANT`.
- status: `REPAIRED_VERIFIED`.

## W1-DEF-KIN-002 — screen/scene-boundary clipping distorts bbox kinematics

- domain: `VISIBLE OUTPUT / CLIPPING`
- severity: `P1 curve-authority integrity`
- root-cause family: `SCREEN_BOUNDARY_CLIPPING_DISTORTS_BBOX_KINEMATICS`.
- observed:
  - S14 outgoing/incoming cards/headings clip against x=0 / viewport boundaries;
  - S16 column is bottom-clipped by the editorial content viewport during its visible state;
  - S16 Factor X begins at that lower boundary.
- repair: clip-aware samples/segments; curve confidence capped LOW; authority becomes `VISIBLE_OUTPUT_CLIPPED_PROXY_NOT_HIDDEN_OBJECT_CURVE`.
- permanent regression: synthetic touching-boundary fixture.
- status: `REPAIRED_VERIFIED / REMAINS A SOURCE LIMITATION`.

## W1-DEF-KIN-003 — sparse keyframe interpolation can manufacture a speed profile

- domain: `SOURCE RESOLUTION / EASING`
- severity: `P1 easing-authority integrity`
- scenes: S04, S11, S14.
- root-cause family: `KEYFRAME_LINEAR_RENDERER_PROJECTION_MISTAKEN_FOR_ORIGINAL_EASING`.
- repair: any `KEYFRAME_LINEAR_*` source caps curve confidence LOW and labels the result `RENDERER_PROJECTION_BEHAVIOR_PROXY_NOT_MEASURED_ORIGINAL_EASING`.
- only full-frame/no-interpolation evidence such as S16 can support stronger behavioral curve confidence, and even there clipping/shape/source-lock caveats apply.
- status: `REPAIRED_VERIFIED / ORIGINAL EASING STILL BLOCKED`.

## W1-DEF-KIN-004 — source-lock reflow can contaminate reusable motion grammar

- domain: `SOURCE LOCK / TEMPLATE GENERALIZATION`
- severity: `P1 structural-template integrity`
- scene: S16 local `87..91`.
- root-cause family: `SOURCE_NATIVE_REFLOW_PROMOTED_TO_EDITORIAL_GRAMMAR`.
- source evidence: late global upward movement coincides with Reels UI reveal; causal editorial origin remains UNKNOWN.
- repair: exact visible kinematics remain measurable, but every S16 entity marks local87..91 `structural_template_eligible=false`; affected segments carry `SOURCE_LOCK_RANGE_EXCLUDED_FROM_STRUCTURAL_MOTION_GRAMMAR`.
- post-repair artifact reports 3 source-lock-excluded motion segments across S16 entities.
- status: `REPAIRED_VERIFIED`.

## W1-DEF-KIN-005 — full video canvas mistaken for scene-visible viewport

- domain: `CLIPPING / COORDINATE SYSTEM`
- severity: `P1 motion-authority integrity`
- root-cause family: `SCENE_CONTENT_VIEWPORT_MISTAKEN_FOR_FULL_FILE_CANVAS`.
- discovery: S16 column repeatedly satisfies `y + height ~= 1014`, while the encoded video is 1108px tall. The relevant editorial/source content viewport terminates at y=1014; using y=1108 failed to flag the lower reveal/clipping boundary.
- repair: every scene source manifest can define `clip_rect`; S16 uses `[0,0,512,1014]` while the other current goldens use the full 512x1108 frame.
- regression: test proves the same bbox is bottom-clipped at y=1014 even though it is not clipped at the encoded canvas bottom.
- status: `REPAIRED_VERIFIED`.

## W1-DEF-KIN-006 — subpixel/low-pixel bbox variation is not automatically editorial micro-motion

- domain: `MOTION / MEASUREMENT NOISE / MICRO-STIMULI`
- severity: `P1 micro-motion authority boundary`
- root-cause family: `LOW_AMPLITUDE_BBOX_VARIATION_PROMOTED_WITHOUT_OPTICAL_FLOW_CORROBORATION`.
- final W1 qualifier preserves every low-amplitude step but does not promote it. Candidate definition for handoff: `0.45 < bbox centroid speed <= 1.5 px/frame`.
- final candidate counts:
  - S04: 32
  - S11: 121
  - S14: 19
  - S16: 48
  - total: 220
- interpretation: candidates may include real micro-crops, text/shape settling, raster/glyph bbox quantization, tracking noise, compression influence, or source-native subject movement. W1 cannot distinguish these from bbox data alone.
- resolution path: T08-W2 optical-flow/camera/depth corroboration. Candidates remain queryable rather than deleted.
- status: `OPEN_OWNED_BY_T08_W2`.

## Final W1 execution

- exact head: `f2d0a0b487f6b7e287d6e24138d05f0fb9baded9`
- `Golden 9D Motion Kinematics` run `34385578190`: SUCCESS
- `Merge Safe` run `34385578137`: SUCCESS
- artifact: `10117564464`
- artifact digest: `sha256:786866e29df5f4e00d7104d687a02806bbe2535e9e5ae12f5f69937ac8ac5184`
- Drive recovery artifact: `154wCG7CFfnyOzWu9OT8k3gMWhcUCD_xi`
- scenes: 4
- entities: 18

Final derived qualification:

```text
VISIBLE_BBOX_KINEMATICS = QUALIFIED_ACROSS_ALL_FOUR_AT_PINNED_TRACK_RESOLUTION
RECONSTRUCT_EXACT_MOTION = PARTIAL
STRUCTURAL_TEMPLATE_MOTION = PARTIAL
ORIGINAL_EASING_GRAPH = BLOCKED
MICRO_MOTION = PENDING_T08_W2_OPTICAL_FLOW_CORROBORATION
W1_STATE = COMPLETE_WITH_RESIDUAL_MOTION_AUTHORITY_BLOCKERS
```

This is intentional. W1 completion means the motion evidence, transform decomposition and uncertainty are now executable/queryable; it does **not** mean full motion/easing fidelity has been proven.

## Next safe frontier

`T08-W2 — camera + depth + occlusion + optical-flow corroboration`.

W2 must determine which of the 220 low-amplitude bbox candidates are supported by global/local pixel flow, separate source-native subject motion from editorial camera/reframe, construct evidence-bound depth partial orders and preserve unresolved relations as UNKNOWN.
