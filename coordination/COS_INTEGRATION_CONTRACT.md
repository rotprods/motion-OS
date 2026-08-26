# MOTION.OS ↔ COS Graph Engine Integration Contract

Status: SHADOW DESIGN + LOCAL PROJECTION IMPLEMENTED

## Boundary
MOTION.OS owns domain truth for content/video execution and coordination.
COS Graph Engine provides reusable graph storage/traversal/reasoning/retrieval capabilities.

MOTION.OS MUST NOT depend on undocumented COS internals. Integration occurs through a versioned projection contract.

## Source flow

```text
Postgres durable coordination/event truth
+ GitHub executable truth refs
+ Drive evidence/artifact refs
        ↓
MOTION.OS CoordinationGraphProjector
        ↓
ProjectionSnapshot(version, hash, nodes, edges)
        ↓
CosProjectionSink adapter
        ↓
COS Graph Engine shadow projection
        ↓
queries / impact / GraphRAG / context inputs
```

No reverse mutation path from COS into authoritative coordination tables is allowed.

## ProjectionSnapshot contract
Required fields:
- projection_version
- source_event_count
- last_event_id
- nodes sorted canonically
- edges sorted canonically
- projection_hash SHA-256

Every adapter must:
1. verify local snapshot hash before send;
2. load as one explicit projection version;
3. return/obtain COS-side projection hash;
4. compare hashes/invariants;
5. mark projection HEALTHY only on match;
6. expose projection lag;
7. never partially promote a failed projection.

## Canonical identities
IDs are URIs. Examples:
- motion://project/MOTION.OS
- motion://agent/<id>
- motion://session/<id>
- motion://task/<id>
- motion://event/<uuid>
- motion://repo/rotprods/motion-OS/pr/37
- motion://artifact/<id>

Display names are properties only.

## Required graph semantics
COS integration must preserve:
- directed typed edges;
- deterministic identity;
- forward + reverse traversal;
- temporal metadata where supplied;
- provenance/evidence refs;
- project scope;
- sensitivity labels;
- projection version/hash;
- snapshot/rebuild semantics.

## Shadow qualification
Do not make agent execution depend on COS availability initially.

Stage C0 — LOCAL_ONLY
- local deterministic projector is authority for expected snapshot.

Stage C1 — COS_SHADOW
- same snapshot loaded into COS;
- queries run in parallel;
- mismatch recorded, never hidden.

Stage C2 — COS_READ_ASSIST
- COS may provide dependency neighborhoods/GraphRAG/context candidates;
- ContextPack compiler verifies projection version/hash and authority filters.

Stage C3 — COS_QUERY_AUTHORITY
- only after replay/rebuild/hash/query equivalence evidence;
- still not transactional state authority.

## Required qualification corpus
- active PR #34/#35/#37 topology;
- synthetic 3-agent disjoint work;
- same-resource conflict;
- task dependency chain;
- contract change impact;
- stale session after merge;
- artifact/evidence lineage;
- causal failure/recovery chain;
- lease expiry/takeover;
- decision supersession.

## Queries COS must support for MOTION.OS
1. What active agent owns or intends to mutate resource X?
2. Which PRs/tasks/contracts are downstream of schema Y?
3. What becomes stale if PR Z merges?
4. What evidence supports completion of task T?
5. What sessions are using a stale projection/context revision?
6. What is the causal path from failure F to artifact A?
7. Which work can proceed in parallel without dependency/resource collision?
8. What contracts bridge Content/Avatar → Studio → Renderer?
9. Which checkpoint is the minimal sufficient resume point for agent A?
10. Which failures/decisions repeatedly affect the same subsystem?

## Version pinning
A deployed adapter records:
- motion_coordination_contract_version
- cos_graph_engine_version or commit SHA
- cos_projection_adapter_version
- projection_schema_version

No floating `main` dependency is permitted for authority qualification.

## Failure semantics
- COS unavailable → coordination truth continues; projection marked DEGRADED/STALE.
- projection hash mismatch → fail closed for COS-assisted authoritative decisions.
- unknown node/edge type → quarantine projection delta or use explicit schema evolution.
- sensitivity filter failure → fail closed; do not compile context.
- projection lag above SLO → context pack must expose/consider stale status.

## Current implementation
`src/coordination/projection.py` provides:
- deterministic nodes/edges;
- canonical sorting;
- SHA-256 snapshot hash;
- pure rebuild from CoordinationEvent stream;
- `CosProjectionSink` protocol.

A concrete COS adapter is intentionally deferred until a COS version/commit is selected and qualified. This prevents hidden coupling to a moving hardening branch.
