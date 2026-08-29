# MOTION.OS V2 — Assurance Model

Authority: PROPOSED_V2_CANDIDATE

## Test architecture

Every critical invariant maps to at least one authoritative test class. Test state vocabulary is exact: `NOT_RUN`, `SKIPPED`, `CANCELLED`, `PASS`, `FAIL`.

| Class | Purpose | Authoritative examples |
|---|---|---|
| Unit | pure logic and boundary predicates | finite budget, semantic TTS classes, graph IDs |
| Contract | cross-module semantic compatibility | Event Fabric, renderer evidence, Studio handoff |
| Schema | machine payload shape and formats | event/context/evidence manifests |
| Property | invariants over generated cases | dedupe/idempotency, hash binding, conflict symmetry |
| Mutation | prove tests detect meaningful corruption | media hash swap, evidence revision, wrong run ID |
| Integration | adjacent subsystem behavior | Content→Studio, renderer→assembly, critic→repair |
| E2E | whole product path | brief→real release manifest |
| Physical runtime | actual tool/runtime/media execution | Remotion/HyperFrames/Lottie/FFmpeg |
| Security | attack trust boundaries | SSRF, shell, unsafe deserialization, secret persistence |
| Concurrency | simultaneous/stale writers | semantic claims, lease takeover, main advancement |
| Replay | event ordering/idempotency | duplicate/late/out-of-order events |
| Recovery | destruction and rebuild | graph/cache/chat/local checkout deletion |
| Performance | measured bottlenecks only | CI duration, render duration, queue time |
| Benchmark | exact product suite | APSR/GSR, unseen styles |
| Empirical | real outcomes | CAL2/performance learning |
| Death drill | zero-context continuity | successor resumes in <=5 min |

## Escaped-bug corpus

Permanent families that must never regress:

1. visual duration must use frame-count/time-base authority, not mux duration alone;
2. fencing generations never reset after release;
3. JSON schema formats must execute real format validation;
4. drift detection does not grant overwrite authority;
5. timeout-after-possible-provider-acceptance reconciles before retry;
6. main advancement invalidates stale merge evidence;
7. cancelled/skipped CI is not PASS;
8. historical topology is not current state;
9. newest event watermark must be consumed before irreversible actions;
10. same logical event across surfaces dedupes; divergent duplicate fails;
11. declared payload/artifact hash must be recomputed;
12. cross-session/correlation injection fails;
13. current human/machine truth surfaces cannot silently diverge;
14. release evidence is exact candidate/media-bound;
15. duplicated machine policy sources require canonicalization/parity;
16. product score and promotion-risk score remain separate;
17. semantic conflict exists even when files are disjoint.

For every new escaped bug: `BUG -> ROOT_CAUSE -> BROKEN_INVARIANT -> WHY_TESTS_MISSED -> REGRESSION_TEST -> ADJACENT_FAILURE_FAMILY -> PROPERTY/FUZZ/GAUNTLET`.

## Security model

### Assets
- source/claim integrity;
- user/provider credentials and budgets;
- paid render authorization;
- media/artifact integrity;
- release authority;
- event/session identity;
- GitHub main integrity;
- user/private content and PII.

### Trust boundaries
1. web/issue/comment/imported prompt -> content/source normalization;
2. external provider telemetry -> avatar/render state;
3. URL/media/archive -> any downstream fetch/parser;
4. GitHub/Drive -> evidence/restore projections;
5. agent-generated plans/events -> coordination authority;
6. renderer process/FFmpeg/browser -> artifact evidence;
7. graph/search/projection -> operator/agent reasoning;
8. local/CI environment -> promotion evidence.

### Threat graph

| Threat | Surface | Required mitigation | Detection | Recovery/residual |
|---|---|---|---|---|
| Prompt/control injection | webpages/issues/prompts | mark untrusted; no control semantics from content | adversarial parser tests | discard contaminated projection |
| Secret leakage | provider errors/logs/docs | redact/reject secret-like material; never persist raw exception | static/security tests | rotate credential externally if exposed |
| SSRF | provider/media URLs | HTTPS + no credentials + allowlist/resolve-revalidate in actual fetcher | SSRF fixtures | block request; audit event |
| Shell injection | subprocess/FFmpeg/tools | argv lists, shell=False, label/path validation | AST/static + adversarial tests | fail action |
| Unsafe deserialization | pickle/yaml/archive | safe formats/loaders; archive path validation | static + malicious fixtures | reject artifact |
| Malicious media/parser bomb | FFmpeg/media parsers | bounded size/time/resources, isolated subprocess, probe before trust | timeout/resource tests | kill process, quarantine artifact |
| Authority escalation | events/claims/graph | authority ceiling + semantic scope + current ContextPack | conflict/preflight tests | block/revoke lease |
| Stale writer | agent/session/lease | monotonic fencing + revision preconditions | concurrency tests | reject stale mutation |
| Replay attack | event/provider callback | idempotency + event/run identity + revision | replay tests | dedupe/quarantine conflict |
| Duplicate spend | provider timeout/retry | reconcile-before-retry + current budget/capacity | provider failure simulation | stop spend and reconcile |
| Supply-chain drift | GitHub Actions/Python/Node | immutable action SHAs, lockfiles, audit/SBOM | security profile | block promotion |
| Evidence substitution | media/critic/benchmark | exact source/run/artifact hashes in EvidenceEnvelope | mutation tests | invalidate authority |

Residual risks must be represented explicitly; current known examples include downstream DNS-rebinding protection until a real fetcher resolves/revalidates addresses, and GitHub admin ruleset enforcement until applied externally.

## Recovery model

### Durable authority set
- GitHub repository history/live lifecycle;
- immutable semantic event history;
- canonical domain state/contracts;
- exact evidence manifests;
- hash-addressed external artifacts when available.

### Disposable/rebuildable set
- chat context;
- local checkout;
- caches;
- ContextPacks;
- SQLite copies not designated as unique authority;
- COS/unified graph projections;
- dashboards/Todoist/read models.

### Cold-recovery algorithm
1. read live `main` and PR lifecycle;
2. load canonical contracts/state at exact revision;
3. replay valid immutable events with idempotency/revision checks;
4. rebuild state snapshots;
5. rebuild coordination/content/COS graphs;
6. reconcile live lifecycle over stale historical projections;
7. verify hashes/revisions;
8. enumerate missing external artifacts as `DEGRADED_EXTERNAL`;
9. compile ContextPack for a new session;
10. return North Star/current objective/blockers/owners/next safe action.

### Disaster campaigns
- delete graph projections -> rebuild identical important topology;
- delete local DB/cache -> reconstruct from durable authority;
- remove chat history -> zero-context successor drill;
- Drive unavailable -> state recovers, artifact authority explicitly degraded;
- duplicate/reordered events -> same canonical state or explicit conflict;
- corrupt evidence manifest -> fail closed;
- main changes during recovery -> invalidate snapshot and restart projection.

## Performance / cost assurance

Measure before optimizing:
- CI minutes per PR and cancelled-run waste;
- render wall time per renderer/brief;
- provider credits per accepted artifact;
- retry/failure rates;
- agent onboarding/reconstruction time;
- conflict/collision rate;
- artifact storage/transfer volume.

Do not introduce distributed stores, caches, queues or CDNs without a recorded measured trigger and a before/after target.
