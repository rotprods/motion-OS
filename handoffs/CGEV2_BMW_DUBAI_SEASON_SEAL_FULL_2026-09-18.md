# /CGEV2 — BMW DUBAI · SEASON SEAL FULL · ACTA DE CONSCIENCIA · HANDOFF

**sealed_at:** 2026-09-18T00:24+02:00  
**project:** MOTION.OS / automotive reference-driven cinematic generation  
**repo authority:** `rotprods/motion-OS`  
**chat_id:** not exposed  
**session_id:** `SES-MOTION-BMW-DUBAI-20260918-0024` (local recovery alias; platform session id not exposed)  
**handoff_id:** `HOFF-MOTION-BMW-DUBAI-CGEV2-20260918-001`  
**agent_id:** `motion://agent/bmw-dubai-reference-director` (handoff identity)  
**status:** `SEALED → SUCCESSOR_REQUIRED`  

---

## 0. COLD-START LAW

Do not use chat memory as authority. Successor executes:

`RECONSTRUCT → VERIFY → CHALLENGE → EXECUTE → TEST → QUALIFY → PERSIST → HANDOFF`

Read first:
1. `AGENTS.md`
2. `STATE.md`
3. `GOAL.md`
4. `coordination/AGENT_PROTOCOL.md`
5. `coordination/ACTIVE_AGENTS.yaml`
6. this handoff
7. `copy_pastes/phase_04_b_motionstyle2json_master.md`
8. `knowledge/CAR_VFX_CAUSAL_CAMERA_GRAMMAR_V2.md`
9. `schemas/motionstyle2json.schema.json`
10. `src/normalization/motionstyle.py`
11. PR #174 and exact current `main` / PR HEADs

Chat is not source of truth. Reconcile GitHub live state before mutation.

---

## 1. NORTH STAR

Immediate creative mission: **produce the BMW-inspired Dubai automotive film**, using the analyzed BMW reference as execution grammar while replacing its art direction/world with a coherent Dubai world whose Burj Khalifa is a physically consistent landmark.

Higher-level product mission remains Motion.OS North Star: brief → professional motion master. Architecture is subordinate to visible creative output.

Do NOT spend the next session inventing another architecture. The next frontier is production after minimal verification.

---

## 2. HOW THIS PROJECT EVOLVED

### Phase A — reverse-engineering top-tier automotive edits
The project began by analyzing several high-end car edits (Ferrari and other automotive references), extracting:
- shot density;
- macro↔hero cadence;
- masks/rotoscoping;
- wheel/body apertures;
- match shapes;
- speed ramps;
- directional motion blur;
- camera energy;
- wireframe / technical states;
- deformation / morph states.

Critical learning: copy **technique grammar**, not pixels/art direction.

### Phase B — failed independent-image methodology
Independent image generation caused world/vehicle drift. Corrected methodology:

`WORLD → WORLD COVERAGE → HERO-IN-WORLD → HERO COVERAGE → DETAIL COVERAGE → TRANSITION STATES → VIDEO`

World and hero become immutable authorities before video generation.

### Phase C — successful meadow automotive film
A flower-meadow film was generated with one coherent world, one locked burgundy/McLaren-like GT hero, multiview coverage, macro transition assets and a Ferrari technique reference. User explicitly judged the result a success.

Learning: world-first + hero-lock + purpose-built reference images materially improved coherence. More references could improve vocabulary, but reference slots/attention are finite.

### Phase D — Skyline/Tokyo film
The system was expanded for a Nissan Skyline/R34-style Tokyo-night film. More purpose-built hero angles and VFX states were created. Seedance 2.5 `omni_reference`, 15 s, 1080×1920, high bitrate, native audio was used. A 2-video + 11-image payload was rejected at submit even after cost preflight; 1 video + 10 images submitted successfully. Therefore optimize information/reference, not raw count.

### Phase E — BMW reference → Dubai adaptation
User supplied a BMW automotive edit and requested exhaustive reverse engineering, then adaptation to Dubai with Burj Khalifa. The reference was analyzed into temporal/event blocks and a frame-addressed forensic template. User then supplied three Google Docs with motion/VFX prompting knowledge. Two were successfully recovered, especially `Motion style` and `CAR VFX`; one Drive doc remained unavailable in that session.

This caused the current Learn V2 upgrade: move from effect labels to **causal 3D choreography**.

---

## 3. BMW REFERENCE — VERIFIED TECHNICAL FACTS

Higgsfield media id used for the BMW forensic reference:
`bf212ce1-b59d-4a94-8a40-42826085b441`

Measured in the prior session:
- 512×910
- H.264
- 30 fps
- 456 frames
- ~15.20 s
- AAC audio

Measured high-change landmarks included approximately:
`f056, f079, f103, f129, f141, f158, f180, f201, f207, f228, f244, f259, f281, f302, f335, f347, f358, f380, f405, f429`.

Strongest measured single-frame discontinuity in that scan: around `f358 / 11.933 s`.

A local sandbox forensic artifact was created as `BMW_REFERENCE_VIDEO_FORENSIC_TEMPLATE_V1.md` with 456 frame addresses and 18 functional blocks. Sandbox is disposable; this handoff captures its durable semantics. If exact V1 file is needed, reconstruct from source rather than trusting sandbox persistence.

---

## 4. BMW EXECUTION DNA

Dominant reusable grammar:
- center-locked hero;
- low automotive camera;
- arc pan / controlled orbit;
- parallel tracking;
- Z dolly / macro push;
- foreground/vehicle occlusion as hidden cut;
- wheel/circular component as transition anchor;
- real↔wireframe registered reveal;
- macro↔hero scale alternation;
- directional motion blur;
- speed-ramp impulses;
- match-position continuity;
- sparse high-energy transitions separated by readable product beats.

Master edit law:

`READ → APPROACH PHYSICAL FEATURE → FEATURE BECOMES MASK/OCCLUDER/MATCH-SHAPE → ACCELERATE → CUT/CROSS AT MAX INFORMATION HIDING → RESOLVE AT MATCHED ANCHOR → READ`

Do not make every beat an impact. Preserve `READ ↔ IMPACT` alternation.

---

## 5. LEARN V2 — CAUSAL 3D CAMERA LAW

The Drive documents elevated the representation standard.

A transition is no longer just `wheel portal`, `whip`, `roto`, etc. Every non-trivial transition should describe:

1. **Approach** — camera trajectory, hero/pivot lock, focus, initial velocity.
2. **Feature acquisition** — tracked feature, mask/roto topology, screen coverage.
3. **Transformation** — detach/deform/open/reveal with explicit depth relation.
4. **Crossing** — camera crosses aperture plane or occluder reaches defined coverage.
5. **Handoff** — incoming scene relationship + motion-vector/focus/anchor transfer.
6. **Resolve** — deceleration, blur normalization, hero settle, distortion back to baseline.

Telemetry when measurable:
- camera `x/y/z`;
- camera `yaw/pitch/roll`;
- hero 6DoF if independently moving;
- pivot/target;
- screen-space anchor;
- focus plane;
- occlusion %;
- mask topology;
- motion vector;
- speed/velocity curve;
- motion blur direction/amount;
- incoming scene spatial relation;
- audio impulse;
- evidence refs;
- confidence.

Unknown values remain null/assumption. Never fabricate precision.

Reference images are **boundary conditions of a plausible 3D trajectory**, not moodboard images.

---

## 6. DURABLE IMPLEMENTATION ALREADY APPLIED TO MAIN

The following changes were applied sequentially to `rotprods/motion-OS/main` in this session. Successor MUST verify live HEAD/history before assuming they remain current.

1. `d9fc030f7f2130e192b8a7e232a80c074bfa6e1f`
   - added `knowledge/CAR_VFX_CAUSAL_CAMERA_GRAMMAR_V2.md`

2. `10548b31a9388827007bbc4111c13c26d6f659ff`
   - upgraded `copy_pastes/phase_04_b_motionstyle2json_master.md`
   - added causal camera/VFX requirements and generative-video boundary-condition law

3. `04ae1a6163a9c3e80655a39d21e3fb3dae741329`
   - extended `schemas/motionstyle2json.schema.json`
   - added automotive rigs, 6DoF, hero plan, causal transition representation, new choreography actions/channels

4. `6c94fdafa6205d8bbe626693a1f75efaa87a43e7`
   - updated `src/normalization/motionstyle.py`
   - propagates evidence-bound camera 6DoF / causal transitions
   - preserves measured micro-choreography
   - explicitly does NOT synthesize filler to satisfy >=12 event gate
   - adds generative-video boundary-condition invariants

Important pre-existing authority discovered: Motion OS already had MotionStyle2JSON schema/normalizer/micro-choreography. Learn V2 **extended the existing authority instead of creating a parallel system**.

---

## 7. TEST FRONTIER / PR #174

User asked whether CI can run locally. **Yes — repository AGENTS.md explicitly says local-first verification is mandatory.** Canonical command when local runtimes are available:

`python scripts/local_verify.py merge`

GitHub Actions is clean-runner merge authority, not interactive debugger.

A dedicated test branch was created:
`test/learn-v2-causal-motionstyle`

PR:
`#174 — test: harden Learn V2 causal MotionStyle contracts`

PR base at creation:
`main @ 6c94fdafa6205d8bbe626693a1f75efaa87a43e7`

PR HEAD at creation:
`bf5e9202810b418923b9804ebf166a5374a6fff0`

Added test file:
`tests/test_learn_v2_causal_motionstyle.py`

Test coverage:
1. schema-valid automotive causal fixture;
2. 6DoF + automotive rig survives normalization;
3. causal aperture/crossing survives normalization;
4. >=12 measured micro-choreography events preserved;
5. missing evidence is NOT fabricated to reach 12;
6. absent causal evidence remains null;
7. generative-video boundary-condition invariants exposed;
8. invalid 6DoF type rejected by schema;
9. unknown choreography channel rejected by schema.

At last observation, GitHub `Merge Safe` run `35282939226` was `queued`. Do not assume its later result; successor must query current PR/CI state.

### IMPORTANT
Do not burn paid/remote CI iterating if the failure is reproducible locally. If successor has a local/Work/Codex checkout, run local verification first. In this chat environment there was no direct shell checkout of the GitHub repo available through the GitHub connector, so the tests were authored but not locally executed here.

---

## 8. DUBAI FILM — CREATIVE NORTH STAR

Adapt the BMW execution grammar into a new Dubai film. Do not pixel-copy BMW.

### World
Premium Dubai night / blue-hour automotive environment with Burj Khalifa as a spatial landmark, not pasted wallpaper.

Burj choreography:
`ESTABLISH GLIMPSE → DISAPPEAR DURING PRODUCT MACROS → REFLECTION/FRAGMENT CALLBACK → FULL LANDMARK FINAL PAYOFF`

Suggested palette:
- obsidian / graphite hero;
- warm limestone / champagne architecture;
- architectural white/cool-white highlights;
- restrained ruby taillights;
- avoid generic purple/cyan cyberpunk soup.

Slightly wet/reflective road may be used if physically plausible; do not imply absurd heavy rain simply to obtain reflections.

### Dubai-specific transition vocabulary
- architectural-column wipe;
- Burj reflection aperture;
- wheel ↔ circular architectural-light match;
- glass/façade reflection transfer;
- limestone foreground occlusion;
- headlight ↔ building-light luminance match;
- road-light-streak whip;
- macro→hero;
- registered technical/wireframe accent;
- speed-ramp/blur bridges.

### Camera requirements
Every planned shot should be expressible in X/Y/Z + yaw/pitch/roll. Use center-lock/pivot explicitly. No magical floating camera.

---

## 9. DUBAI WORLD ASSET ALREADY GENERATED

A Dubai World Master was generated earlier in the session via Higgsfield:
`4117ac42-ce00-4409-b4b0-e0361a671591`

Successor MUST inspect it visually before promoting it to WORLD_LOCK. Do not assume prior text declaration equals visual QA.

The correct production sequence remains:

`WORLD MASTER → WORLD QA → 4–6 SAME-WORLD CAMERA COVERAGE → HERO MASTER → HERO LOCK → 8–13 HERO/DETAIL ANGLES → 4–6 TRANSITION AUTHORITY STATES → REFERENCE COMPILER → SEEDANCE 2.5 → FRAME GAUNTLET`

Do not regenerate unrelated independent images.

---

## 10. REFERENCE-FABRIC LESSONS FROM PREVIOUS SUCCESSFUL RUNS

Durable laws:
- world-first + hero-lock improves continuity;
- hero multiview coverage should derive from one accepted hero master;
- macro images should be designed as transition geometry, not beauty shots only;
- specialized video references should have declared roles;
- more references are useful only when orthogonal/non-conflicting;
- Seedance 2.5 omni-reference successfully produced a coherent finished automotive film from one technique video + purpose-built images;
- a prior 2-video + 11-image payload was rejected at submit after cost preflight accepted it; reduced 1-video + 10-image payload submitted. Treat as run-specific evidence, not a universal hard maximum;
- never auto-retry a paid generation blindly;
- preflight cost before paid video generation;
- generative video does not guarantee deterministic edit topology; for strict source-preserving topology, use a more deterministic/source-preserving path when available.

---

## 11. LOCAL-FIRST TESTING ANSWER

Question left hanging immediately before seal: “¿No podemos hacer CI en local?”

Answer: **yes**. `AGENTS.md` current main explicitly mandates local-first verification. The intended merge profile is:

```bash
python scripts/local_verify.py merge
```

Successor should:
1. fetch PR #174 live state;
2. run the relevant test file locally first if a checkout/runtime is available;
3. run `python scripts/local_verify.py merge`;
4. fix causes locally;
5. only then use GitHub Merge Safe as clean-runner evidence;
6. qualify the exact HEAD.

Do not confuse local PASS with GitHub merge authority, but do not waste GitHub Actions as a debugger.

---

## 12. EXACT NEXT-SAFE-ACTION

Do not start by writing more architecture.

### Wave 1 — 5–10 minute qualification
- verify `main` HEAD;
- inspect PR #174 HEAD/status/CI;
- run local `tests/test_learn_v2_causal_motionstyle.py` and `scripts/local_verify.py merge` if runtime exists;
- fix only demonstrated blockers;
- do not let this consume the creative session indefinitely.

### Wave 2 — immediately resume film production
- inspect Higgsfield Dubai World Master `4117ac42-ce00-4409-b4b0-e0361a671591`;
- either WORLD_LOCK or regenerate only if visual QA fails;
- generate 4–6 SAME-WORLD camera positions as boundary conditions of BMW-derived camera trajectories;
- introduce one hero vehicle into the locked world;
- lock hero;
- derive 8–13 hero/detail frames matched to the BMW shot/event grammar;
- derive transition-authority states for Dubai-specific geometry;
- compile a high-information reference pack within Seedance media constraints;
- preflight cost;
- generate one final 15 s 1080×1920 high-bitrate audio-enabled Seedance 2.5 omni-reference master;
- no blind retry;
- frame-by-frame QA and score.

---

## 13. DO NOT DO

- Do not overengineer another graph before producing the film.
- Do not treat chat memory as authority.
- Do not create independent unrelated Dubai images.
- Do not paste Burj Khalifa randomly into every shot.
- Do not describe camera with adjectives only; use trajectory/pivot/occlusion/crossing/resolve.
- Do not fabricate exact lens/6DoF values when not evidenced; hypotheses must be labeled.
- Do not synthesize fake micro-events merely to satisfy >=12.
- Do not repeatedly use the same portal/morph effect; maintain VFX diversity budget.
- Do not declare CI/QA green without exact-head evidence.
- Do not spend paid generation