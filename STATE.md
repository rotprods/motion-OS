# STATE.md — MOTION.OS

## Canonical infrastructure state
- GitHub software source of truth: **ACTIVE on `main`**.
- Canonical repo: `rotprods/motion-OS`.
- Bootstrap PR #10: MERGED.
- RC06 promotion PR #19: MERGED.
- Real Analysis Superwave PR #32: **MERGED** (`b3a568993df7ed4df99494c4c6a65f59e0292dcd`).
- CI Python 3.11: PASS.
- CI Python 3.12: PASS.
- Dedicated physical `analysis-runtime`: PASS (FFmpeg + FFprobe + OpenCV asserted; real encoded-MP4 E2E executed).
- Repo Health: PASS.
- Security Baseline: PASS.

## Product / creative state
- Phase: v0.9.1 creative convergence + generalization validation.
- Release: **BLOCKED**.
- Working master candidate selected for promotion: **RC09E**.
- RC06: prior working master retained for lineage and rollback.
- RC07: HOLD / NOT PROMOTED.
- RC08: structural-diversity discovery only; no branch promoted.
- RC09: four structural exploration branches + exploit branch E. RC09E preserves the canonical narrative and validated 6.65–7.50s RC06 transition while materially improving hero framing, SYSTEM hierarchy and final-frame structure.
- RC09E technical: 1080×1920, 30 fps source, 10.000 s, AAC audio preserved.
- Wave 05: unseen surgical-robotics brief across clinical product, surgical HUD, biotech editorial and industrial engineering; new articulated robotic-instrument hero family.
- Primitive qualification: 15 verified / 30 quarantined.
- Benchmark definition: 25 briefs / 5 style families.

## Intelligence / Phase 04 state
### Physical ANALYZE path — VERIFIED V2
`MP4 → FFprobe → FFmpeg physical frames + SHA256 → measured cut scores → shots/keyframes → visual/motion/OCR/FX/audio providers → FeaturePack schema → MotionStyle2JSON schema → Remotion scene spec + TypeScript`.

- Physical frame decode: VERIFIED IN CI.
- Real encoded 90-frame/3-shot ground-truth fixture: VERIFIED IN CI; cut recovery required at frames 30/60 within <=1 frame.
- OpenCV Farneback provider: VERIFIED AVAILABLE in dedicated analysis runtime and exercised through E2E.
- Tesseract OCR: implemented optional provider + temporal continuity tracking; production accuracy benchmark remains open.
- Audio: physical PCM envelope/onset provider implemented; optional Whisper runtime/model benchmark remains open.
- StyleSignature v1: inspectable measured vector + SQLite corpus/retrieval path implemented.
- Reference conditioning: retrieved evidence can feed GENERATE only as provenance-bearing soft constraints with anti-copy lock.
- RECONSTRUCT_EXACT: content-addressed physical frames can form an exact raster-sequence/hybrid fidelity baseline; vectorization proof remains open.

### Remaining empirical Phase 04 gates
1. Benchmark a known historical/native MOTION.OS master against declared ground truth.
2. Analyze >=10 heterogeneous reference videos.
3. Quantify OCR/flow/taxonomy accuracy against labeled real data.
4. Human-label retrieval relevance instead of relying on self-neighbor sanity checks.
5. Compile and actually render >=3 analyzed references through Remotion production runtime.

## Remaining P0 release gates
1. Verify HyperFrames production runtime.
2. Verify Remotion production runtime.
3. Connect authoritative full-video temporal multimodal critic.
4. Converge canonical RC to semantic/creative release thresholds >=9.

## Persistence
- GitHub = software truth.
- Drive = artifacts / progress / recovery truth.
- SQLite = structured operational knowledge / StyleSignatures at current scale.
- Graph = execution, evidence and causal lineage.
- Local sandbox = disposable compute.

## Anti-overengineering
Do not add generic distributed infrastructure, external vector DBs, queues or orchestration layers unless measured corpus/runtime scale demonstrates the need. Current bottlenecks are empirical accuracy, renderer runtime proof and authoritative creative QA.
