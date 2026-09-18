# Phase 08 — AVE × MOTION.OS Semantic Knowledge Plane

## Objective

Create a local-first, rebuildable semantic plane over both repositories without replacing Git truth, Motion's coordination graph, or the canonical `rotprods/cos-graph-engine`.

## Work packages

### P08.1 Corpus contract
- Repository manifests in AVE and MOTION.OS.
- UTF-8 code/docs/configs indexed; binaries/vendors/build artifacts excluded.
- Repo/commit/path/line/hash provenance mandatory.
- Secret-bearing files excluded and common inline credentials redacted.

**DoD:** deterministic chunks and stable IDs; source authority recoverable for every point.

### P08.2 Local embeddings
- Ollama endpoint on loopback.
- `bge-m3` default model.
- Enforce 1024D response contract.
- Batch embedding with explicit model/version metadata in payload.

**DoD:** dimension mismatch fails closed; no silent model drift.

### P08.3 Qdrant projection
- Pinned local Qdrant container.
- Single versioned collection with named vectors `semantic` and `cos20`.
- Cosine distance for both.
- Payload indexes on repo/path/commit/index_run.
- Upsert-before-stale-delete transaction discipline.

**DoD:** re-index failure cannot destroy previous valid projection; incompatible collection schema fails closed.

### P08.4 COS 20D / 20-level integration
- Deterministic 1024D→20D JL routing projection.
- 20D used only to retrieve a broad candidate set.
- Exact 1024D cosine rerank determines final semantic order.
- `/graphify` writes derived semantic-neighbor edges with provenance.
- `/cos-graph-engine` exposes GraphRAG retrieval while preserving L0-L19 canonical vocabulary.
- Material semantic behavior maps to L8 Knowledge, L9 Semantic, L10 Embedding, L11 GraphRAG and L12 Memory.

**DoD:** no semantic-neighbor edge is promoted as a causal/dependency fact; canonical COS remains upstream authority for its graph contracts.

### P08.5 Operator surface
- `doctor`
- `index --repo ...`
- `graphify`
- `query`
- loopback HTTP `/health`, `/index`, `/graphify`, `/cos-graph-engine`
- bootstrap script and pinned compose service.

**DoD:** one documented sequence reconstructs the complete derived plane from two clean repo checkouts.

### P08.6 Verification
- chunk boundary/provenance/security tests;
- deterministic 20D projection test;
- Qdrant named-vector schema contract test;
- stale-cleanup ordering test;
- candidate routing + native rerank test;
- synthetic routing benchmark;
- live Ollama/Qdrant benchmark on target host;
- real-corpus labeled retrieval benchmark after initial indexing.

**Promotion gates:**
1. tests = green;
2. deterministic benchmark: candidate exact Recall@10 >= 0.95, reranked topic precision >= 0.99;
3. `doctor.ok=true` on target host;
4. both repo commits fully indexed with zero service errors;
5. graphify completes for all indexed points;
6. 25+ labeled cross-repo questions achieve agreed Recall@10/MRR threshold;
7. MERGE_SAFE clean-runner proof before main promotion.

## Failure policy

- Never delete an existing Qdrant collection to solve schema mismatch; bump the versioned collection name.
- Never expose local Qdrant/Ollama publicly by default.
- Never index secrets to improve recall.
- Never call Qdrant or a semantic neighbor “canonical truth”.
- Never claim live latency/throughput without target-host execution evidence.
