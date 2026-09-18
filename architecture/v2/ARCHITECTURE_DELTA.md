# MOTION.OS — V1/current → V2 Architecture Delta

Authority: PROPOSED_V2
Source revision: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`

| Current reality | V2 target | Classification | Why |
|---|---|---|---|
| Multiple hand-maintained current-state surfaces | one canonical current-state projector + generated/validated views | REFACTOR | current split brain is a proven P0 defect |
| Issue #39 + repo events + Runtime EventStore appear as separate buses | one logical event semantics across surfaces | REFINE | prevent independent coordination truths |
| GitHub lifecycle facts mixed into stale projections | live lifecycle overlay has explicit precedence | KEEP/REFINE | current PR/main state must supersede stale event/docs |
| COS/Unified Graph already derived | typed temporal hypergraph/COS remains one-way rebuildable | REFINE | improve queryability without hidden authority |
| Agent identity exists; session discipline varies by generation | Session first-class in every event/task/decision/evidence/handoff | REFINE | context loss and concurrent agents require durable lineage |
| Studio EditingGraph + render routing exists | L1 semantic → L2 editing → L3 runtime/evidence graph contract | REFINE | prevent renderer specifics from owning creative intent |
| Remotion physically verified | keep as production renderer backend | KEEP | evidence exists on main |
| HyperFrames compiler + open physical proof | physically verify, then route per-layer/subgraph | MIGRATE | compiler-ready is not runtime authority |
| Lottie internal subset | strict supported portable-vector runtime boundary | REFINE | fail closed on unsupported features |
| FFmpeg compositor global time/z fixed on main | integrate single audio + alpha + color normalization | REFINE | heterogeneous mastering remains fragmented across PRs |
| Physical video extraction/Visual DNA foundation | evidence-first corpus + GraphRAG retrieval quality | KEEP/REFINE | extraction is strong; empirical corpus remains weak |
| SQLite StyleStore/GraphRAG seed | hybrid hard-filter → graph → similarity → history/user rerank | REFINE | similarity is useful but cannot authorize |
| Skill runtime exists | capability/authority/failure traces durable and graph-projected | REFINE | executor failures must never disappear |
| QA/repair graph exists | run-scoped defects + actual mutation targets + physical localized repair proof | REFINE | explainability and regression safety |
| Phase06 content/avatar transactional authority | keep single-host; strengthen semantic identities and spend/claim/TTS gates | KEEP/REFINE | working authority with discovered boundary bugs |
| Local-first MERGE_SAFE | keep, add canonical current-state/event preflight and admin ruleset | KEEP/REFINE | strong protocol, weak administrative enforcement |
| NetworkX/SQLite | retain until measured trigger | KEEP | no measured need for distributed infra |
| Drive artifact/recovery plane | hash-bound artifacts + explicit degraded mode + recovery drill | REFINE | availability is not always proven |
| Historical docs rewritten manually | supersede old versions, retain lineage, generate present projections | MIGRATE | preserve history and eliminate silent staleness |
| Product/architecture work sometimes competes | product score separate from promotion-risk score | REFINE | architecture must visibly improve output |

## Greenfield ideal vs pragmatic V2

A clean greenfield system would begin with a typed event/state/graph kernel, generated projections, explicit evidence identities and per-layer renderer routing. The current repo already contains substantial equivalents. V2 therefore **does not** replace verified extraction, Remotion, Phase06 transactional state, MERGE_SAFE, EditingGraph, or EventStore foundations. It converges them around explicit authority and removes ambiguous duplicate truth.

## Deliberately not added

- Postgres/Supabase multi-host authority until actual contention/HA trigger;
- Redis/Kafka/general queues;
- Kubernetes/microservices;
- external vector DB or graph DB;
- CDN/distributed workers;
- new generic observability platform.

Interfaces may anticipate these capabilities; deployment is deferred until evidence says the simpler topology fails.
