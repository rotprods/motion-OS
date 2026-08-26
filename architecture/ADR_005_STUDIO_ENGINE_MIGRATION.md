# ADR-005 — Studio Engine Migration Invariants

Status: ACCEPTED FOR PHASE 05 EXECUTION

## Decision
MOTION.OS evolves into a graph-native Studio Engine by extending existing modules rather than introducing parallel replacements.

## Ownership map
- extraction = deterministic/low-level evidence production
- normalization = evidence-bound taxonomy mapping
- knowledge = retrieval memory seed
- graph = causal/editing/execution graph foundation
- primitives = semantic motion component layer
- compilers = graph-to-renderer compilation
- renderers = capability-aware execution backends
- qa = critics, gates, defect evidence
- agents = skill orchestration/runtime

## Three-level invariant
L1 Semantic/Creative Graph → L2 Editing/Motion Graph → L3 Render/Evidence Graph.

L3 MUST be regenerable from L1+L2+capabilities. Renderer implementation MUST NOT become the source of creative intent.

## Stable identity
Every persistent graph entity requires a stable ID. IDs survive renderer changes, partial rerenders and serialization round-trips.

## Evidence/provenance
Any inferred or externally sourced node must retain evidence/provenance references. Missing provider capability or uncertain licensing cannot silently become accepted truth.

## Mutation
Changes invalidate only causal descendants. Re-extraction is forbidden when the mutated node has no dependency path to extraction evidence.

## Persistence
- GitHub: software/control truth.
- Drive: heavy artifact/recovery truth.
- SQLite: structured retrieval/operational memory.
- NetworkX MultiDiGraph: initial graph runtime.

External graph/vector databases require measured scale triggers before adoption.

## Renderer boundary
Remotion, HyperFrames, Lottie, SVG and generated/raster video are backends. Routing may happen per subgraph/layer.

## QA authority
Fixture/sampled QA cannot satisfy an authoritative release gate. Defects attach to graph nodes/edges and repairs mutate only affected subgraphs where possible.

## Migration constraints
1. no duplicate `GraphV2` architecture beside current graph without explicit migration adapter;
2. no provider result promoted without provenance state;
3. no skill execution without capability resolution;
4. no timeline gap introduced by graph compilation;
5. no hard-coded renderer state in semantic nodes;
6. all schema changes require representative fixtures and tests.

## Rollback
Phase 05 changes remain additive until typed graph serialization and migration tests prove round-trip integrity. Existing pipelines remain callable during migration.
