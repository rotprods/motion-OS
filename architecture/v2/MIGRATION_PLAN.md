# MOTION.OS V2 — Migration Plan

Authority: `IMPLEMENTED_PENDING_REVIEW`
Source main: `a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`
Canonical V2 candidate: PR #91

## Objective

Move from the current strong-but-fragmented topology to one V2 authority/graph/documentation model without rewriting proven capability or erasing history.

## Migration classes

| Current | V2 target | Class | Rule |
|---|---|---|---|
| GitHub live + hand-maintained state docs | GitHub live + canonical state + validated human projections | REFACTOR | canonical truth owner fixes split-brain; history preserved |
| Issue #39 + repo events + Runtime EventStore | one Event Fabric semantic contract with adapters | REFINE/MIGRATE | promote #58 before autonomy |
| bootstrap `ACTIVE_AGENTS.yaml` | live/derived session+claim projection | REFACTOR | retain only as historical bootstrap snapshot |
| COS/unified graph | temporal hypergraph projection | REFINE | shared IDs, no reverse authority |
| loose evidence dictionaries | common evidence identity adapters | REFINE | bind source/spec/runtime/run/artifact without breaking active contracts blindly |
| Remotion runtime proof | production renderer adapter | KEEP/REFINE | preserve physical proof, add reproducibility/provenance completeness |
| HyperFrames branch proof | provenance-bound renderer adapter | REFINE | exact source/spec/runtime/run/artifact |
| Lottie compiler-ready | physical official-player adapter | MIGRATE | browser-player evidence required |
| single master audio | assembly audio authority | KEEP | integrate alpha/color/timing around it |
| aggregate primitive/benchmark counts | exact ID-bound ledgers/suites | REFACTOR | historical aggregate = observation only |
| fixture/mechanical QA | real full-video temporal + creative authority | MIGRATE | real recoverable master required |
| weak path-only conflict consumers | one semantic conflict engine | REFACTOR | import/reuse canonical semantics |
| protocol-only main protection | GitHub-native ruleset + CI protocol | MIGRATE_EXTERNAL | settings/admin action required |
| Postgres/queues/CDN ideas | interfaces now, deployment on measured trigger | DEFER | avoid premature infrastructure |

## Train A — Truth/control plane
1. Reconcile canonical current state (#56 lineage).
2. Promote Event Fabric (#58) through exact combined-head proof.
3. Rebuild active session/claim/current-state projections.
4. Requalify autonomous selector (#68) against promoted Event Fabric; keep scheduler disabled until later governance gate.

## Train B — Isolated correctness/security
May develop in parallel, but each promotion serializes against latest main:
- TTS semantic integrity #71;
- claim verification evidence #73;
- spend policy #74;
- provider telemetry #76;
- performance learning #77;
- static/security gate #70.

## Train C — QA/render truth
1. converge QA history #59;
2. close exact frame authority #64;
3. provenance-bind HyperFrames #62;
4. preserve master audio #61;
5. semantic alpha #63;
6. color normalization #69 after assembly ownership permits;
7. physical Lottie official player #66;
8. valid Node lockfile + `npm ci` reproducibility.

## Train D — Product authority
1. temporal critic #65 with exact provider/run/frame/media evidence;
2. recover or regenerate canonical real master;
3. run creative tournament/release manifest;
4. primitive qualification #67;
5. benchmark/Visual DNA/unseen suite #75;
6. CAL2/performance-learning qualification.

## Train E — Governance/docs
1. apply GitHub main ruleset externally;
2. run recovery/concurrency/security/death drill;
3. accept CP4 and promote V2 canonical docs/state navigation;
4. mark superseded architecture/ADR/current-state surfaces explicitly without deleting history;
5. update AGENTS/README/GOAL/STATE/TASKS/HANDOFF navigation/authority metadata;
6. activate bounded autonomous loop only after prerequisites.

## Per-PR promotion protocol

Before every irreversible promotion:
1. read newest main SHA;
2. read newest Event Fabric watermark/session claims;
3. invalidate stale ContextPack if either changed;
4. inspect path + semantic + authority scopes;
5. reconcile candidate without discarding concurrent work;
6. run relevant local profiles;
7. run exact combined-head clean-runner gates;
8. review code/security/evidence claims;
9. merge one candidate;
10. verify new main;
11. emit `pr.merged` + `main.verified` evidence;
12. invalidate downstream proofs based on old main.

## Rollback

- Code: Git revert/safe rollback branch from exact merge SHA.
- State: compensating/superseding event; history remains immutable.
- Artifacts: preserve previous hash-bound working master/rollback artifact.
- Graph/read models: rebuild from pre-migration authority revision.
- Autonomy: kill switch disables scheduler; claims/leases expire/revoke; no hidden queue continues work.
- Provider spend: stop new authorization and reconcile accepted jobs before retry/cancel.

## Supersession policy

Every current architecture/state document ultimately declares authority, scope, owner, source revision, validity/supersession and `superseded_by`. Historical docs remain discoverable. A document without current authority metadata cannot outrank machine/live state.

## Completion criteria

Migration completes only when no competing current V1/V2 authority remains, all promoted contracts have exact combined-head evidence, docs/state projections match live GitHub, Event Fabric/session topology rebuilds from durable authority, product E2E + empirical gates pass, GitHub administrative controls are active, post-migration cold recovery/death drill passes, and every old branch/PR is classified MERGED/CLOSED_UNMERGED/SUPERSEDED/BLOCKED with lineage.