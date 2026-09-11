# T08-W2 Camera / Depth / Occlusion — Defect Graph

Authority: append-only gauntlet ledger for the cross-golden camera/depth/occlusion qualification wave.
A successful compiler or workflow proves only the declared derived qualification. It cannot reveal hidden original
After Effects camera/precomp topology, physical camera motion, occluded geometry, or a total z-order that flattened
source pixels do not expose.

## Durable evidence chain

Canonical source:
- source SHA256: `9b3076cb542e358386942a0fb6b160f1345564d4326738f9a340e2b5b38e199d`
- 512x1108 @ 30fps
- Drive source: `1mEnC97VZMPkz-lZ-KDtIKOGdKOqHNeum`

Physical W2 measurements:
- optical-flow baseline Drive ID: `1sfIurf_bie-Ji5dQldw-y1D9w_PtL92z`
- optical-flow baseline SHA256: `e20dde9c84e9209962b21f140da6f13928501002a10d018164062bdfc9380990`
- 220-candidate micro-motion adjudication Drive ID: `1JQCbfLPuRJ4E4IU3bPcQVgmXGFKYTPQ8`
- micro-motion evidence SHA256: `821fafae8e33c8b883e7e34590722c2a61fac397277bcc97cc068ede43c94b04`
- camera/depth evidence summary Drive ID: `1CCGajR2_ysAm6jqVh8HSbRMkTymywJK7`
- summary SHA256: `63c36c39ddd0ce27f583d5a7499cbbdd8f562cf0829b8f0af997ad6584bd3a53`
- W2 qualification Drive ID: `1rlNiPy70UzTVm-EzIlozRwgpXUkRJtQ7`
- qualification SHA256: `a909364ee6e704e46be7063b098243b15c4e86a0b75633c54f7b61bacbbfd323`

Exact-head executable qualification:
- W2 executable head: `80d8926f49873dabc64cc381e22806fc92740194`
- Golden 9D Camera Depth run `34600058526` -> SUCCESS
- Golden 9D Motion Kinematics run `34600058504` -> SUCCESS
- Merge Safe run `34600058414` -> SUCCESS
- GitHub artifact `10263503237`
- artifact digest `sha256:d9994c23d4915273d41ac14ffed1452bc696abae69c4cb1d8815398695633a78`
- durable Drive artifact `11P40ZMe2khhyHOKep3vGh3Q9Xe86u-Ro`

Matrix projection proof:
- matrix + regression head: `4a3b586af7e92aa4fcce6f696ac09e85d0364adb`
- Golden 9D Camera Depth run `34600509920` -> SUCCESS
- Golden 9D Motion Kinematics run `34600509972` -> SUCCESS
- Merge Safe run `34600510045` -> SUCCESS

## W2-DEF-CONT-001 — stale frontier can cause completed wave replay

- domain: `CONTINUITY / AUTHORITY PROJECTION`
- severity: `P1 zero-context execution integrity`
- discovered during: T08 reclaim before W2 execution
- observed: `W1_DEFECT_GRAPH.md` and the live branch already proved W1 complete, but
  `qualification/golden_9d/next_frontier.json` still declared the current checkpoint as T07 and instructed a successor
  to execute W1 again.
- root-cause family: `STALE_FRONTIER_PROJECTION_REPLAYS_COMPLETED_WORK`.
- rejected behavior: trust a single handoff/frontier document without reconciling live Git/CI/Drive/Event Bus truth.
- repair: provider reconciliation + frontier update at `2bb0044cff0dd5bf87829d6e699207145efb0405`.
- permanent invariant: the active frontier must identify the evidence head, documentation head, current wave and exact
  next safe action; live durable truth overrides stale projection text.
- status: `REPAIRED / EXACT_HEAD_REVERIFIED`.

## W2-DEF-CAM-001 — foreground motion laundered into camera motion

- domain: `CAMERA / CAUSAL AUTHORITY`
- severity: `P0 structural editing-DNA integrity`
- root-cause family: `FOREGROUND_MOTION_LAUNDERED_AS_CAMERA`.
- counterexamples:
  - S04 subject/caption movement while the common background remains effectively static;
  - S11 pill/hook/copy group lift while the graphic canvas remains effectively static;
  - S14 card+heading carousel translation while the background common vector remains effectively zero.
- physical baseline:
  - S04 background median flow ~`0.002706 px/frame`, foreground ~`0.030301`;
  - S11 background median flow ~`2.35e-7`, foreground ~`7.29e-5`;
  - S14 background median flow ~`0.000296`, foreground ~`0.205497`;
  - S16 background median flow ~`0.000632`, foreground ~`0.029535`.
- rejected repair: classify camera from bbox centroid movement, object consensus alone, or a historical semantic label.
- architecture repair:
  1. measure source-pixel common/background motion separately from foreground/entity motion;
  2. preserve object/group transforms as local editing behavior;
  3. grant global camera/reframe authority only when common-frame evidence supports it;
  4. preserve unresolved subject-native-vs-precomp reframe causality as PARTIAL/UNKNOWN.
- regressions:
  - a static camera/canvas claim fails if the measured common background vector exceeds its gate;
  - S04 A026 cannot self-promote to global camera authority;
  - S11 group lift and S14 carousel parent remain foreground/group authority.
- status: `REPAIRED_VERIFIED / ORIGINAL_CAMERA_CAUSALITY_REMAINS_PARTIAL`.

## W2-DEF-CAM-002 — low-texture background optical flow can miss a real common reflow

- domain: `CAMERA / MEASUREMENT ORACLE`
- severity: `P1 camera-classification integrity`
- origin: S16 historical camera report v1 -> v2
- root-cause family: `LOW_TEXTURE_BACKGROUND_FLOW_FALSE_NEGATIVE_ON_GLOBAL_REFLOW`.
- observed: background optical flow correctly established static framing through local86 but, by itself, under-observed
  the local87..91 common upward reflow because the relevant background region is low texture.
- independent corroboration: foreground/overlay consensus showed common dy `[-4,-4,-4,-4,-2]`, cumulative `-18 px`,
  coincident with Reels UI reveal.
- rejected inference: call this an editorial camera move merely because the composite shifts.
- repair: combine background/common flow with multi-entity consensus and source-UI coincidence; classify local87..91 as
  `SOURCE_LOCK_UNLESS_INDEPENDENTLY_PROVEN_EDITORIAL`.
- permanent invariant: absence of background flow in a low-texture region is not sufficient evidence of global-frame
  stasis when multiple independent visible entities share the same displacement.
- status: `REPAIRED_VERIFIED / CAUSE REMAINS UNKNOWN`.

## W2-DEF-MICRO-001 — low-amplitude bbox variation promoted without pixel corroboration

- domain: `MOTION / CAMERA / MEASUREMENT NOISE`
- severity: `P1 micro-motion authority`
- root-cause family: `LOW_AMPLITUDE_BBOX_VARIATION_PROMOTED_WITHOUT_PIXEL_FLOW_CORROBORATION`.
- input: exactly `220` W1 candidate steps with `0.45 < bbox centroid speed <= 1.5 px/frame`.
- physical source-pixel adjudication:
  - `95` -> `CORROBORATED_DIRECTIONAL_PIXEL_FLOW`;
  - `81` -> pixel activity/visible change without translation authority;
  - `41` -> not corroborated above background/noise;
  - `3` -> SOURCE_LOCK excluded.
- rejected repair: lower/raise one bbox threshold until the candidate universe “looks right”.
- architecture repair: candidate entity/frame pairs are tested against their source pixels, local gradient-supported flow,
  background-derived noise floor, direction cosine/support and structural eligibility.
- permanent invariant: bbox micro-motion remains a candidate until source-pixel evidence corroborates the declared
  observable. Even directional corroboration grants only visible local-motion proxy, not original transform/easing/camera causality.
- status: `REPAIRED_VERIFIED`.

## W2-DEF-DEPTH-001 — flattened source silently expanded into a total z-order

- domain: `DEPTH / OCCLUSION / GRAPH AUTHORITY`
- severity: `P0 depth-grammar integrity`
- root-cause family: `TOTAL_Z_ORDER_INVENTED_FROM_FLATTENED_SOURCE`.
- problem: a flattened render often proves some pairwise foreground/background relationships while providing no
  persistent overlap for other pairs. Topologically sorting known edges must not create authority for unobserved pairs.
- explicit unresolved examples:
  - S04 `SUBJECT <-> BACKGROUND`;
  - S11 `CURVED_ARROW <-> HERO_PILL` and `SUPPORT_ROWS <-> HOOK_COPY`;
  - S14 `OUTGOING_CARD <-> INCOMING_CARD`;
  - S16 `COLUMN <-> QUESTION_MARK`.
- architecture repair:
  1. store depth as an acyclic partial order, not a total order;
  2. store unsupported pairwise relations as first-class UNKNOWN nodes with reasons;
  3. reject cycles;
  4. reject any edge that silently orders an explicitly UNKNOWN pair.
- regression: `tests/test_golden_9d_camera_depth.py` attacks both cycle creation and UNKNOWN->edge laundering.
- status: `REPAIRED_VERIFIED / SOURCE-LIMITED UNKNOWNS INTENTIONALLY REMAIN`.

## Final W2 qualification

Physical source measurements + exact-head clean-runner qualification now support:

```text
MICRO_MOTION_CANDIDATE_UNIVERSE = 220 CLOSED_PARTITION
DIRECTIONAL_PIXEL_FLOW_CORROBORATED = 95
PIXEL_ACTIVITY_WITHOUT_TRANSLATION_AUTHORITY = 81
NOT_CORROBORATED_ABOVE_BACKGROUND = 41
SOURCE_LOCK_EXCLUDED = 3

S04_CAMERA_STRUCTURAL = PARTIAL
S11_CAMERA_STRUCTURAL = QUALIFIED
S14_CAMERA_STRUCTURAL = QUALIFIED
S16_CAMERA_STRUCTURAL = QUALIFIED

CAMERA_RECONSTRUCT_EXACT = PARTIAL_ACROSS_ALL_GOLDENS
DEPTH_RECONSTRUCT_EXACT = PARTIAL_ACROSS_ALL_GOLDENS
DEPTH_STRUCTURAL_TEMPLATE = PARTIAL_ACROSS_ALL_GOLDENS
ORIGINAL_CAMERA_OR_AE_PARENTING = BLOCKED_OR_UNKNOWN
FULL_9D_FIDELITY_VALIDATED = FALSE
CANONICAL_TEMPLATE = FALSE
```

W2 completion means that camera-vs-object behavior, measured depth edges, SOURCE_LOCK exclusions and the unresolved
causal/depth relations are now executable and regression-protected. It does **not** mean that hidden original camera,
AE parenting/precomp topology, full occluded geometry or a total source z-order have been recovered.

## Next safe frontier

`T08-W3 — Stimulus and Retention Grammar`

W3 must compile high-salience visual events into causal event clusters, quantify cadence/dead intervals, preserve
deliberate calm holds (especially S16 local54..86), and avoid the failure family `OBJECT_COUNT_OR_PIXEL_CHANGE_USED_AS_RETENTION_QUALITY`.
