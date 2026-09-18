# BMW DUBAI — EXECUTION GRAPH V1

Status: **EXECUTED / MASTER RENDER PENDING VISUAL QA**  
Correlation: `BMW-DUBAI-FILM-20260918`  
Branch: `prod/bmw-dubai-reference-film`  
Base after Learn V2 test merge: `72674bca609196c25cc99e05f93ad170f22e28e4`

## North Star

Produce a 15 s, 9:16, 1080p, high-bitrate, audio-enabled premium BMW M3 G80 film in one coherent Downtown Dubai world. Transfer the **execution grammar** of the recovered BMW reference, not its rooftop/mountain art direction.

```text
BMW TECHNIQUE VIDEO
  │ temporal/edit authority
  ▼
CAUSAL CAMERA / EDIT GRAMMAR
  │
  ├─ low center-lock
  ├─ x lateral tracking
  ├─ z dolly macro push
  ├─ small yaw arc
  ├─ speed-ramp impulse
  ├─ foreground occlusion crossing
  ├─ glass reflection handoff
  ├─ wheel-spoke circular crossing
  └─ wireframe → solid registered resolve
  │
  ▼
DUBAI WORLD AUTHORITY
  ├─ road spline
  ├─ limestone occluders
  ├─ glass reflection planes
  ├─ champagne practicals
  ├─ restrained damp reflections
  └─ Burj landmark choreography
  │
  ▼
BMW HERO AUTHORITY
  │
  ▼
PURPOSE-BUILT COVERAGE + TRANSITION STATES
  │
  ▼
SEEDANCE 2.5 OMNI_REFERENCE MASTER
  │
  ▼
FRAME / AUDIO / CONTINUITY GAUNTLET
```

## 1. Recovered source authority

BMW technique media:
- Higgsfield media: `bf212ce1-b59d-4a94-8a40-42826085b441`
- measured prior forensic facts: 512×910, H.264, 30 fps, 456 frames, ~15.20 s, AAC
- repeated Higgsfield analyses agree on: wireframe/chassis→solid BMW, low frontal product beats, fast push/zoom, rear/taillight macro, reflection/aperture transition, rear tracking, wheel-spoke circular crossing, diffuser/rear resolution
- prior measured high-change landmarks: `f056, f079, f103, f129, f141, f158, f180, f201, f207, f228, f244, f259, f281, f302, f335, f347, f358, f380, f405, f429`
- strongest prior discontinuity: around `f358 / 11.933 s`

Source reference is **TECHNIQUE/TEMPORAL AUTHORITY ONLY** for the final film. Rooftop, mountains, daylight and original geography are explicitly rejected.

## 2. Learn V2 contract gate

PR #174 `test: harden Learn V2 causal MotionStyle contracts`:
- PR head: `bf5e9202810b418923b9804ebf166a5374a6fff0`
- Merge Safe run: `35282939226`
- `Local contract / Python 3.12`: SUCCESS
- `MERGE_SAFE`: SUCCESS
- review threads: 0
- exact-head squash merge: `72674bca609196c25cc99e05f93ad170f22e28e4`

The causal/6DoF/micro-choreography foundation is therefore qualified before this production wave.

## 3. World authority

WORLD MASTER:
- `4117ac42-ce00-4409-b4b0-e0361a671591`
- status: **WORLD_LOCK_CANDIDATE**
- visual promotion must still be based on direct pixel inspection; connector metadata/status alone is not semantic QA

Generated same-world boundary conditions:
- W01 establish low curve: `495f90c0-bd90-4a44-af2a-623a8cb6a0ed`
- W02 parallel track axis: `9b39a50a-f7fa-4c4b-bebe-4c052d76e9ec`
- W03 rear departure axis: `93a934f7-04a0-45a7-b142-d4b440283182`
- W04 limestone occluder: `f7f32deb-28a3-4be6-9e1d-1a6d20028e2f`
- W05 glass reflection transfer: `a707c389-0502-4039-a9ab-028bafdfe91d`
- W06 final Burj payoff axis: `1542df6f-5e02-4794-a62d-ae4128fcc559`

## 4. Hero authority

Frames extracted from the real BMW source clip and uploaded as reusable evidence:
- front ~1.70 s: `3bad219d-a190-4fd6-b0db-09fa64c9bb89`
- front 3/4 ~3.50 s: `fed025f8-2c18-4bac-9458-58cb4080d217`
- rear/track ~7.50 s: `8eb8092a-25e5-47de-9fa4-e23c67aac80d`
- wheel ~9.50 s: `93add8fc-27d8-4a56-8dbf-235ca8e8199c`
- front low ~11.50 s: `d2b9a405-92e1-4011-815f-23c720ec3037`

HERO MASTER:
- `ea592be8-a49a-4696-a4b3-b4d36874780b`
- purpose: exact black BMW M3 G80 identity transplanted into locked Dubai world
- status: GENERATED, pending direct semantic visual QA

Hero coverage:
- H01 front low read: `f1f6ffba-e1b9-43ab-a780-aeaaf81ef5fe`
- H02 front 3/4 track: `c234bf6d-7010-4510-97d9-f8324dae268f`
- H03 centered front read: `da743f40-8fb7-42fc-b7f0-150659b77ba2`
- H04 rear 3/4 track: `8f493e8b-cd7d-40da-a277-0c7025fefdfe`
- H05 taillight macro: `b93254b9-0b01-4edb-9e6a-52f6c7bc8f97`
- H06 wheel macro: `336005a0-875f-455d-9fc8-4cf91f3789c4`

## 5. Transition authority

Film-specific fingerprint:
- T01 registered wireframe assembly: `1672961b-7790-4477-a100-68e4d102dc77`
- T02 limestone occlusion crossing: `cb00d8f8-20c3-4d69-abda-7b5536340252`
- T03 glass reflection transfer: `0849d65b-84ef-4344-9b1d-5123a4b4ed8b`
- T04 wheel match/crossing: `2f6f062c-3326-4147-8e77-8b894f556c24`
- T05 final rear + Burj payoff: `242b6417-5ae6-4fef-9c5b-8a59319c5334`

Causal law:
`APPROACH → FEATURE ACQUISITION → OCCLUSION/REFLECTION/MATCH GEOMETRY → CROSS AT MAXIMUM INFORMATION HIDING → MOTION-VECTOR HANDOFF → RESOLVE → READ`

## 6. Final edit graph

| Time | Function | Camera / causal action | Authority |
|---|---|---|---|
| 0.00–0.90 | IMPACT | registered wireframe/chassis → solid resolve; world fixed | T01 |
| 0.90–1.80 | READ | low front center-lock, small yaw arc | H01 |
| 1.80–2.70 | IMPACT | x+z tracking acceleration, parallax grows | H02 |
| 2.70–3.20 | CROSS | limestone reaches 70–85% coverage; cut at max hiding | T02 |
| 3.20–4.20 | READ | same-world front 3/4 resolve; speed settles | H02 |
| 4.20–5.10 | IMPACT | z-dolly into taillight/body; rack focus | H05 |
| 5.10–6.10 | HANDOFF | physical glass reflection, reflection→hero focus transfer | T03 |
| 6.10–7.15 | READ | low rear 3/4 parallel track | H04 |
| 7.15–8.15 | IMPACT | wheel macro push, circular anchor acquired | H06 |
| 8.15–8.75 | CROSS | spoke/rim occlusion; circular match at peak blur | T04 |
| 8.75–9.70 | READ | low frontal matched resolve | H01/H03 |
| 9.70–10.80 | IMPACT | controlled z-dolly + small yaw arc + speed ramp | H01 |
| 10.80–12.10 | READ | diffuser/rear product beat | H04 |
| 12.10–13.10 | IMPACT | architecture-derived occlusion/whip; no generic glitch | T02/W world |
| 13.10–15.00 | PAYOFF | low rear settle; full Burj reveal; camera eases out | T05 |

## 7. Burj choreography

`EARLY GLIMPSE → HIDDEN DURING PRODUCT/MACROS → REFLECTION FRAGMENT CALLBACK → FULL FINAL REVEAL`

Burj is a spatial landmark, not repeated wallpaper.

## 8. Seedance compile

Model: `seedance_2_5`  
Mode: `omni_reference`  
Duration: 15 s  
Aspect: 9:16  
Resolution: 1080p  
Bitrate: high  
Native audio: true  
Preflight cost: **135 credits**  
Balance before submit: **4321.17 credits**

Final high-information pack:
- video technique authority: `bf212ce1-b59d-4a94-8a40-42826085b441`
- image refs: H01, H02, H04, H05, H06, T01, T02, T03, T04, T05
- total: **1 video + 10 images**

Submitted Seedance master:
- job: `964a7476-84e5-47eb-a160-0d78e7a13757`
- submit state at persistence: **QUEUED**
- no blind retry permitted

## 9. Visual QA gates after completion

Score exact rendered output with timestamps/evidence:
- HERO_IDENTITY
- WORLD_CONTINUITY
- BURJ_GEOGRAPHY
- PHOTOREALISM
- SHOT_DIVERSITY
- EDIT_DENSITY
- CAMERA_ENERGY
- CAUSAL_TRANSITIONS
- MASK/OCCLUSION_QUALITY
- SPEED_RAMP/RETIME
- MACRO↔HERO_RHYTHM
- VFX_INTEGRATION
- PHYSICS
- ARTIFACT_CONTROL
- SOUND_DESIGN
- FINAL_HERO
- OVERALL

Do not call the film complete until the exact video has been inspected. Missing requested mechanisms and malformed mechanisms are logged separately.

---

## 10. EXECUTION RESULT — 2026-09-18

### Seedance outcome

Two paid-model submission strategies were attempted after successful preflight:

1. **V1 technique-video + still fabric**
   - job `964a7476-84e5-47eb-a160-0d78e7a13757`
   - terminal status: `IP_DETECTED`
   - no finished video promoted.

2. **V2 original topology + still fabric only**
   - job `42fd21e3-a1e3-4172-a2ee-a0505cd5954d`
   - source technique video was removed;
   - choreography was rewritten as an original Dubai-specific edit;
   - terminal status: `IP_DETECTED`
   - no finished video promoted.

**Decision:** IP detection is treated as a terminal platform constraint for these attempts. Do not repeatedly resubmit, disguise, or otherwise attempt to bypass that control. The reference film remains forensic learning evidence only.

### Deterministic V3

A permitted deterministic master was rendered from the already-created BMW/Dubai still fabric with FFmpeg.

Canonical media:
`9f3a9784-c435-44fb-a16e-74a9daf07378`

Measured:
- 1080×1920
- 30 fps
- 450 frames
- 15.000 s
- H.264
- AAC stereo
- ~9.74 Mb/s
- -15.7 LUFS integrated
- -0.4 dBFS measured true peak

Semantic critic `bb3b8587-d5a6-42ce-9060-7184abbc2ed9` recovered 12 functional scenes and explicitly recognized:
- BMW M3 hero;
- Dubai night / wet luxury road;
- Burj Khalifa;
- glass/reflection opening;
- limestone/stone occlusion;
- wireframe/chassis technical reveal;
- taillight macro;
- rear/diffuser;
- wheel macro;
- frontal product read;
- final rear + Burj payoff.

**V3 weakness:** the critic describes multiple shots as static. The still-reference fabric is coherent, but camera energy remains below the intended automotive standard.

### V3.1 audio experiment

Media `1ef0fbb3-d59b-47e5-919d-329d73ea6e06` is **REJECTED**.
The attempted limiter/resample path measured +1.3 dBFS true peak after AAC and therefore is not a promotion candidate.

### Motion V4 candidate

V4 changes no hero/world authority. It modifies only the deterministic camera choreography:
- nonlinear z-dolly;
- lateral x tracking;
- micro vertical drift;
- impact-only temporal frame mixing;
- controlled transition blur;
- crisp READ settles;
- longer final-payoff settle.

Canonical V4 media:
`a2a42737-5aaf-4203-8fee-7b9d25500913`

Technical qualification:
- 1080×1920
- 30 fps
- 450 frames
- 15.000 s
- H.264
- AAC stereo 48 kHz
- ~15.89 Mb/s
- -16.4 LUFS integrated
- -2.1 dBFS true peak

Measured motion-energy delta vs V3:
- median adjacent luma delta: **+4.97%**
- trimmed-95 mean: **+11.09%**
- P75: **+7.93%**
- P90: **+4.77%**

V4 semantic critic:
`9cc59ecd-32fe-4491-aa3b-100cd19b41a4`

Promotion state at this checkpoint:
**TECHNICAL_VERIFIED / SEMANTIC_PENDING**.

Do not promote V4 solely from motion-energy metrics. It must retain hero identity, world continuity, landmark geography, macro↔hero rhythm and final payoff under exact rendered-video semantic review.

