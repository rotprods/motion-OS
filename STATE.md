# STATE.md — MOTION.OS

## Canonical infrastructure state
- GitHub software source of truth: **ACTIVE on `main`**.
- Canonical repo: `rotprods/motion-OS`.
- Bootstrap PR #10: MERGED.
- RC06 promotion PR #19: MERGED.
- CI Python 3.11: PASS.
- CI Python 3.12: PASS.
- Repo Health: PASS.
- Security Baseline: PASS.
- Phase 08 AVE × MOTION semantic knowledge plane: **IMPLEMENTED + PHYSICAL CLEAN-RUNNER SMOKE VERIFIED ON PR #128; FULL DUAL-REPO CORPUS NOT YET QUALIFIED OR CANONICAL**.

## Product state
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

## Remaining P0
1. Verify HyperFrames production runtime.
2. Verify Remotion production runtime.
3. Connect authoritative full-video temporal multimodal critic.
4. Converge canonical RC to semantic/creative release thresholds >=9.

## Phase 08 semantic plane boundary
- Source authority remains Git/commit history.
- Qdrant collection `ave_motion_semantic_v1` is a derived, rebuildable retrieval projection only.
- Native semantic vector: local Ollama `bge-m3` 1024D.
- Derived `cos20`: deterministic 20D coarse routing vector; exact 1024D rerank determines final semantic ranking.
- AVE `GRAPH/graph.json` and `communities.json` are reused as repository-owned structural metadata rather than replaced or reinterpreted as semantic truth.
- Exact head `a1b69658b2a5032dfc298bdf6062bb686209a1ee`: `Merge Safe` PASS + physical `Semantic Live Smoke` PASS with real `ollama/ollama:0.33.2`, `bge-m3` 1024D and `qdrant/qdrant:v1.19.0`.
- Latest clean-runner physical smoke observed end-to-end search p50 104.633 ms / p95 117.014 ms and Ollama batch-4 p50 264.509 ms / p95 264.812 ms. These are smoke-runner measurements, not full-corpus SLOs.
- `graphify-v4-qdrant-prefetch-rerank` performs `cos20` prefetch + exact semantic rerank inside Qdrant and transfers no 1024D vectors back to Python during graphification.
- 25-query real-corpus benchmark ground truth is frozen and stale architecture labels are guarded by tests. AVE stale authority docs discovered during archaeology are excluded from the AVE semantic corpus until repaired.
- Full AVE + MOTION indexing, complete cross-repo graphify, labeled Recall@10/MRR/NDCG and portable Qdrant snapshot remain the promotion gate.
- AVE private GitHub Actions currently cannot allocate runners because the account-level GitHub Actions included usage and configured Actions budget are exhausted for the current billing period. This is an infrastructure/billing gate, not a semantic-plane failure. Restore Actions budget/capacity or execute `scripts/qualify_semantic_corpus.sh` on the target Mac/sibling checkouts before promotion.

## Persistence
- GitHub = software truth.
- Drive = artifacts / progress / recovery truth.
- SQLite = structured operational knowledge.
- Graph = execution and causal lineage.
- Qdrant = rebuildable semantic retrieval projection, **not authority**.
- Local sandbox = disposable compute.

## Anti-overengineering
Do not add generic infrastructure unless it removes a current P0/P1 or improves measured creative output.
