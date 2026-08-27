# ADR-006 — Storage, Database and CDN Triggers

Status: ACCEPTED FOR CURRENT SCALE
Date: 2026-08-26

## Decision
MOTION.OS will **not** add Postgres merely because the system generates media or because a multi-host architecture is theoretically possible.

Current authority remains:
- GitHub: software/control truth.
- SQLite WAL: local/single-host operational metadata, manifests, render intents, calibration and structured memory at current scale.
- Local filesystem / Drive: development and recovery artifacts.
- Content-addressed object storage: the future production home for heavy media assets when remote delivery/persistence requires it.
- CDN: layered in front of object storage when assets must be served repeatedly/globally.

Heavy MP4/MOV/PNG/audio/model assets MUST NOT be stored as ordinary Postgres blobs. A relational DB stores metadata, provenance, object keys, hashes, leases, state transitions, workspace/user relations and queryable indexes; object storage stores bytes.

## Why
The current product is primarily a content-generation/editing engine, not yet a high-concurrency multi-tenant SaaS. Adding Postgres today would introduce migrations, credentials, network availability, backup/restore, connection pooling and distributed-failure modes without removing a measured bottleneck.

Top-tier engineering means preserving migration seams before the trigger, not deploying infrastructure before it is needed. `RenderStateStore` remains an interface so a network implementation can be added without rewriting the pipeline.

## Postgres trigger
Introduce a network transactional store only when one or more are true and measured/required:
1. more than one independent host must concurrently own/reconcile paid render jobs;
2. server-side scheduled/background workers run independently of the controlling host;
3. multi-user or multi-workspace SaaS state requires shared transactional authority;
4. SQLite write contention/locking measurably impacts throughput or correctness;
5. HA/failover requirements require authority to survive host loss;
6. remote analytics/query patterns materially exceed the local SQLite operating envelope.

Until a trigger fires, multi-host Postgres work is `DEFERRED_BY_DESIGN`, not a release blocker.

## Object-storage/CDN trigger
Introduce production object storage when any is true:
1. heavy assets must survive ephemeral runners/hosts;
2. downstream workers need the same artifact from different machines;
3. published or preview assets require stable URLs;
4. Drive/local filesystem throughput, permissions or lifecycle management becomes a bottleneck;
5. global/repeated delivery makes CDN caching economically useful.

Recommended architecture when triggered:
`metadata DB -> object key + sha256 + provenance -> object storage -> optional CDN`.

Candidate implementations may include S3-compatible storage, Cloudflare R2, or Supabase Storage. Provider choice is a deployment decision, not a semantic dependency of MOTION.OS.

## Security invariants
- signed/time-limited URLs for private assets;
- content-type and size allowlists on ingest;
- streamed hashing and content-addressed identity;
- no executable trust derived from filename/extension;
- tenant/workspace authorization checked before issuing object access;
- lifecycle/retention policy explicit;
- provider secrets never enter manifests, graphs or prompts.

## Consequence for Phase 06
The previously planned Postgres-class `RenderStateStore` is no longer mandatory for the current merge/release gate. Keep SQLite authority and distributed-store contract boundaries; activate network authority only when a trigger above becomes real.

This decision reduces overengineering without removing the path to multi-host production.