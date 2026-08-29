# MOTION.OS V2 — Migration Plan

Authority: PROPOSED_V2_CANDIDATE
Source main: `a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`

## Migration objective

Move from a strong but fragmented V1/V1.5 topology to one V2 authority/graph/documentation model without rewriting proven capabilities or erasing history.

## Current -> V2 delta

| Current | V2 target | Classification | Migration rule |
|---|---|---|---|
| Live GitHub + several hand-maintained state docs | GitHub live + canonical domain state + validated human projections | REFACTOR | promote #56-style validator/projector; do not hand-edit duplicates independently |
| GitHub Bus #39 body + comments + repo events + runtime EventStore | one Event Fabric semantic contract with adapters | REFINE/MIGRATE | promote #58; body becomes historical bootstrap, latest projector/watermark is current |
| Bootstrap `ACTIVE_AGENTS.yaml` | generated/validated active session/claim read model | REFACTOR | retain historical snapshot, stop treating it as current |
| COS/unified graph | V2 temporal hypergraph projection | REFINE | shared stable IDs; no reverse authority |
| Branch-specific evidence formats | common EvidenceEnvelope adapters | REFINE | adapt, do not break active domain contracts wholesale |
| Remotion physical runtime | evidence-bound renderer adapter | KEEP/REFINE | preserve proof; add dependency/provenance completeness |
| HyperFrames branch proof | production renderer adapter | REFINE | bind source/spec/runtime/run/artifact |
| Lottie compiler-ready | production renderer adapter | MIGRATE | execute official-player physical proof |
| single master audio | master assembly authority | KEEP | integrate color/alpha/timing around it |
| aggregate primitive/benchmark counts | exact ID-bound ledgers/suites | REFACTOR | historical aggregates remain authority_effect=NONE |
| fixture/non-authoritative QA | full-video temporal + creative authority | MIGRATE | real recoverable master required |
| path-first agent collision checks in weaker consumers | one semantic conflict engine | REFACTOR | import/reuse canonical implementation |
| protocol-only main protection | GitHub-native ruleset + protocol/CI | MIGRATE | external admin action required |
| optional Postgres target | deferred adapter implementation | DEFER | only on measured multi-host trigger |

## Migration train

### Train A — Truth/control plane
1. Reconcile current state (#56 or successor) against live main.
2. Promote Event Fabric (#58) through exact combined-head proof.
3. Rebuild active session/claim/current-state projections.
4. Requalify autonomous selector (#68) against promoted Event Fabric; keep disabled until later activation gate.

### Train B — Isolated correctness/security
Can proceed in parallel on isolated scopes, but merge serially against latest main:
- TTS semantic integrity #71;
- claim evidence #73;
- spend policy #74;
- provider telemetry #76;
- performance learning #77;
- static/security gate #70.

### Train C — QA/render truth
1. converge QA history #59;
2. exact frame authority #64;
3. renderer provenance #62;
4. master audio #61 if not already promoted;
5. semantic alpha #63;
6. color normalization #69 after assembly ownership permits;
7. Lottie physical runtime #66;
8. Node lockfile/reproducible install.

### Train D — Product authority
1. temporal critic #65 with real provider/run/frame/media evidence;
2. recover/regenerate canonical real master;
3. run creative tournament/release manifest;
4. primitive qualification #67;
5. benchmark/Visual DNA/unseen suite #75;
6. CAL2 performance learning.

### Train E — Governance and docs
1. apply GitHub main ruleset externally;
2. run recovery/concurrency/security/death drill;
3. freeze/promote V2 docs;
4. mark older architecture documents/ADRs as SUPERSEDED where applicable, never delete historical evidence;
5. update AGENTS/README/GOAL/STATE/TASKS/HANDOFF navigation and authority metadata;
6. activate bounded autonomous loop only after prerequisites.

## Per-PR migration protocol

Before irreversible promotion:
1. read newest main SHA;
2. read newest Event Fabric watermark/session claims;
3. invalidate stale ContextPack if either changed;
4. inspect semantic/path scopes and dependencies;
5. rebase/reconcile without discarding concurrent work;
6. run relevant local profiles;
7. run exact combined-head clean-runner gates;
8. review code/security/evidence claims;
9. merge one candidate;
10. verify new main;
11. emit PR merged/main verified event;
12. invalidate downstream proofs derived from old main.

## Rollback strategy

- Code: Git revert/safe rollback branch from exact merge SHA.
- State: append compensating/superseding event; never rewrite history.
- Artifacts: preserve prior hash-bound working master/rollback artifact.
- Graphs/read models: rebuild from pre-migration authority revision.
- Autonomous execution: kill switch disables scheduler; claims/leases expire/revoke; no hidden queue continues work.
- External provider spend: stop new authorization; reconcile accepted jobs before retry/cancel decisions.

## Supersession registry policy

Every architecture/current-state document eventually declares:
- authority;
- scope;
- owner;
- source_revision;
- valid_from / superseded_at when applicable;
- superseded_by.

Historical docs remain discoverable. A document lacking current authority metadata cannot outrank machine/live state.

## Migration completion criteria

Migration is complete only when:
- no V1/V2 competing current authority remains;
- all promoted contracts have exact combined-head evidence;
- docs/current-state projections match live GitHub;
- Event Fabric/current session topology is rebuildable;
- whole-product E2E and empirical gates pass;
- GitHub administrative main controls are active;
- post-migration cold recovery and agent-death drills pass;
- old branches/PRs are classified MERGED, CLOSED_UNMERGED, SUPERSEDED or BLOCKED with explicit lineage.
