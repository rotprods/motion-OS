# AVE × MOTION.OS Semantic Knowledge Plane

## Status

This layer is a **rebuildable retrieval projection** over Git repositories. Git/commit history remains authority. Qdrant is never a canonical truth store and its data is not committed to Git.

## Architecture

```text
rotprods/ave --------------------┐
                                 ├─ source-aware chunker
rotprods/motion-OS --------------┘
        │
        ├─ provenance: repo / commit / path / line span / hashes
        ├─ secret-path exclusion + inline secret redaction
        ▼
Ollama bge-m3
        │ 1024D normalized embedding
        ├───────────────────────────────┐
        ▼                               ▼
Qdrant named vector: semantic       Deterministic JL projection
1024D / Cosine                      20D / normalized
                                        │
                                        ▼
                                Qdrant named vector: cos20
                                        │
                                coarse candidate routing
                                        ▼
                                exact 1024D cosine rerank
                                        │
                                        ▼
                          provenance-preserving GraphRAG
```

The 20D routing vector is deliberately **not** authority. It narrows the candidate set, then native BGE-M3 1024D cosine decides final ranking.

## COS Graph Engine 20-level binding

The canonical COS engine has 20 levels L0-L19. This knowledge plane does not redefine them.

| COS level | Binding in this implementation |
|---|---|
| L0 Visual | graph payload can be projected to visual nodes/edges |
| L1 Execution | index → embed → project → upsert → graphify pipeline |
| L2 State | source → chunked → embedded → indexed → graphified lifecycle |
| L3 Dependency | repository/path provenance available for dependency enrichment |
| L4 Call | future source extractor; not fabricated by semantic similarity |
| L5 CFG | future source extractor; not fabricated by semantic similarity |
| L6 DataFlow | future source extractor; not fabricated by semantic similarity |
| L7 Compute | embedding/projection execution can be instrumented here |
| **L8 Knowledge** | chunk identities, source facts, provenance |
| **L9 Semantic** | semantic-neighbor relationships |
| **L10 Embedding** | BGE-M3 1024D + derived cos20 routing vector |
| **L11 GraphRAG** | 20D routing → 1024D exact rerank → neighbors/context |
| **L12 Memory** | local Qdrant projection, rebuildable from Git |
| L13 Agent | agents consume `/cos-graph-engine` results |
| L14 Tool | Ollama/Qdrant are explicit tool nodes/boundaries |
| L15 Workflow | index/graphify/benchmark workflow |
| L16 Network | loopback-only local service topology |
| L17 Social | no synthetic binding |
| L18 Biological | no synthetic binding |
| L19 Molecular | no synthetic binding |

Only L8-L12 are materialized as semantic knowledge behavior here. The remaining levels stay available to the canonical `rotprods/cos-graph-engine`; no fake edges are emitted merely to claim “20D”.

## Qdrant collection contract

Default collection: `ave_motion_semantic_v1`

Named vectors:

- `semantic`: 1024 dimensions, Cosine, native Ollama `bge-m3` embedding.
- `cos20`: 20 dimensions, Cosine, deterministic dense Johnson-Lindenstrauss/Rademacher projection (`motion-cos20-jl-v2`).

Payload fields include:

`repo`, `commit`, `path`, `language`, `start_line`, `end_line`, `source_sha256`, `chunk_sha256`, `embedding_model`, `semantic_dims`, `cos_route_dims`, `projection_version`, `index_run`, `indexed_at`, `text`, `cos_level_bindings`, and after graphification `graph_neighbors`.

Stable point IDs derive from repository + path + line span + chunk content hash. Every indexing run upserts first and deletes stale points **only after the new run finishes**, so a failed embedding batch cannot erase the previous good projection.

## Chunk policy

Default target is 1,600 characters, hard target 2,200, overlap 240. Boundaries prefer blank lines, Markdown headings and code declarations. The system indexes UTF-8 source, docs and configs throughout both repositories.

It intentionally skips binary/media, package vendors, build outputs, caches and files above 1.5 MiB. Secret-bearing paths such as `.env`, private keys and credentials are never indexed. Common inline token/private-key patterns are redacted before embedding and payload persistence.

## Local bootstrap

From the MOTION.OS repository:

```bash
bash scripts/bootstrap_semantic_plane.sh
```

That operation:

1. verifies `ollama` and Docker exist;
2. starts Ollama locally if needed;
3. pulls `bge-m3`;
4. starts pinned Qdrant `v1.19.0` on `127.0.0.1:6333` with a persistent named volume;
5. runs `doctor`, which creates or validates the collection schema and probes the live embedding dimension.

Do not expose the Qdrant port publicly. The compose file binds REST to loopback only. If the service ever moves off-host, add Qdrant authentication/TLS before changing that boundary.

## Index both repositories

Assuming sibling checkouts:

```bash
python -m src.semantic_index index \
  --repo ../ave \
  --repo .
```

The command is idempotent and incremental at the projection layer: unchanged chunks have stable IDs; stale chunks are removed only after the replacement run succeeds.

## /graphify

CLI:

```bash
python -m src.semantic_index graphify \
  --repo-id rotprods/ave \
  --repo-id rotprods/motion-OS \
  --neighbors 8
```

HTTP:

```bash
python -m src.semantic_index serve
curl -sS http://127.0.0.1:8791/graphify \
  -H 'content-type: application/json' \
  -d '{"repo_ids":["rotprods/ave","rotprods/motion-OS"],"neighbors":8}'
```

Graphification first searches the cheap 20D route space, then reranks candidates with exact 1024D cosine. Persisted semantic edges always carry source provenance.

## /cos-graph-engine

CLI:

```bash
python -m src.semantic_index query \
  --repo-id rotprods/ave \
  --repo-id rotprods/motion-OS \
  --limit 10 \
  'where does reference retrieval feed Visual DNA and the critic loop?'
```

HTTP:

```bash
curl -sS http://127.0.0.1:8791/cos-graph-engine \
  -H 'content-type: application/json' \
  -d '{"query":"reference retrieval visual dna critic loop","limit":10}'
```

The response exposes the full 20-level COS vocabulary, identifies L8-L12 as the active semantic retrieval layers, and returns ranked chunks with repository/path/line provenance.

## Benchmark and gates

Deterministic core benchmark (no external services):

```bash
python -m src.semantic_index benchmark
```

Live benchmark after indexing:

```bash
python -m src.semantic_index benchmark --live
```

Core release gates:

- projection output is exactly 20D;
- top-10 native-neighbor candidate recall through 20D routing >= 0.95 on the deterministic clustered corpus;
- topic precision after exact 1024D rerank >= 0.99;
- unit/contract tests green;
- live Ollama/Qdrant benchmark must be explicitly executed on the target host before claiming live performance.

The synthetic benchmark is a regression test for the routing algorithm, not a substitute for empirical recall on the real AVE/MOTION corpus. A production promotion should add a labeled query set from real tasks and report Recall@K/MRR/NDCG alongside latency.
