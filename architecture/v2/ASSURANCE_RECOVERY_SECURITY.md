# MOTION.OS V2 — Assurance, Security & Recovery Model

Authority: PROPOSED_V2
Source: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`

## 1. Test architecture

### Taxonomy

| Layer | Purpose | Authority ceiling |
|---|---|---|
| Unit | pure function/local invariant | VERIFIED for local behavior |
| Contract | schema/API/state transition | VERIFIED for contract |
| Schema | shape + format + semantic constraints | VERIFIED for serialization boundary |
| Property | generalized invariant over generated inputs | VERIFIED for explored input class |
| Mutation | prove tests detect changed behavior | assurance evidence only |
| Integration | subsystem boundaries | VERIFIED for tested composition |
| E2E | full operational path | VERIFIED for exact fixture/path |
| Physical runtime | real renderer/provider/media tool | EXECUTED/VERIFIED for exact runtime/version |
| Security | trust-boundary attack/regression | VERIFIED for tested class |
| Concurrency | races/leases/idempotency/fencing | VERIFIED only for tested topology |
| Replay | duplicate/order/restart/event recovery | VERIFIED for replay semantics |
| Recovery | durable rebuild after loss | VERIFIED for listed durable planes |
| Performance | latency/cost/capacity observation | observation, not causal product rule |
| Benchmark | repeated product/generalization measurement | VERIFIED dataset evidence |
| Empirical qualification | real productions/corpus | EMPIRICALLY_QUALIFIED when thresholds met |
| Agent-death drill | successor resumes without chat | continuity VERIFIED |

### Evidence-state law

`PASS`, `FAIL`, `SKIPPED`, `CANCELLED`, `NOT_RUN` are distinct. Only PASS from the required environment/scope contributes positive assurance. A skipped expensive gate may be appropriate for a path-classified PR but cannot be cited as executed evidence.

### Critical invariant mapping

| Invariant | Permanent test family |
|---|---|
| visual duration = frame_count/fps | mux-tail mismatch physical fixture |
| fencing generation monotonic | expire/reacquire/stale writer property tests |
| JSON Schema formats real | invalid date-time/URI cases with `FormatChecker` |
| replica drift ≠ overwrite permission | conflicting replica refresh tests |
| provider accepted/timeout → reconcile | duplicate-spend adversarial scenario |
| main changes after CI | stale combined-head/preflight rejection |
| cancelled/skipped CI ≠ PASS | lifecycle truth reducer tests |
| TTS semantic identity | percentage/currency/decimal/year/version/name failure families |
| PRV/MNF/Beat/content IDs stable | mutation at Studio boundary must fail |
| performance observation ≠ causation | learning-rule authority test |
| evidence belongs to artifact | cross-media/hash substitution rejection |
| logical event duplicate conflict | same logical ID + different payload fails closed |

### Bug escape protocol

For every escaped bug persist:

`BUG → ROOT_CAUSE → BROKEN_INVARIANT → WHY_TESTS_MISSED → REGRESSION_TEST → ADJACENT_FAILURE_FAMILY → PROPERTY/FUZZ/GAUNTLET`.

A one-case patch without generalized family is incomplete.

## 2. Threat model

### Primary assets
- software/main/release authority;
- event history/aggregate revisions;
- paid-render authorization and provider job identity;
- content/PRV/MNF/Beat identities;
- artifact bytes/hashes/manifests;
- credentials and provider tokens;
- PII/source material;
- creative/evaluation evidence;
- recovery state.

### Trust boundaries

1. **External text/data:** web, README, issues/comments, Slack/Drive/provider payloads, imported prompts.
2. **Filesystem/media:** user paths, archives, MP4/images/fonts, generated HTML/JS.
3. **Process boundary:** FFmpeg, npm/node, browser, renderer CLI, OCR/Whisper.
4. **Network/provider:** Pinterest/Pexels/HeyGen/model APIs/remote services.
5. **Coordination:** agent events, claims, leases, ContextPack, GitHub lifecycle.
6. **Promotion:** PR → combined head → main → release.

All external inputs are `UNTRUSTED_DATA` until validated for their boundary. They cannot become control-plane instructions by appearing in data.

### Threat / mitigation matrix

| Threat | Detection/mitigation | Residual |
|---|---|---|
| prompt injection via source/reference | data/control separation, source provenance, no instruction execution from content | model judgment remains attack surface; require bounded skills |
| provider poisoning | provider identity, hashes, schema validation, cross-source checks | provider compromise remains external residual |
| secret/PII leakage | sanitized exception traces, no raw credentials in events, static secret gate | runtime third-party logs require provider policy |
| path traversal | normalized/root-bounded paths, reject file URLs where unneeded | media tools still require sandbox discipline |
| SSRF/file URL | URL allowlists/scheme checks, no blind internal fetch | provider redirects require validation |
| shell/filter injection | argv arrays `shell=False`; filter labels whitelisted | third-party CLI parsing remains external |
| malicious media parser | resource/time limits, current patched tools, disposable sandbox | zero-day parser risk |
| dependency compromise | pinned actions, lockfiles, npm integrity, dependency audit | upstream supply-chain residual |
| stale writer | expected revision + fencing generation + lease semantics | multi-host claim deferred until tested |
| replay/duplicate spend | idempotency + reconcile-before-retry + transactional single-host store | provider API ambiguity may require manual reconcile |
| authority self-promotion | closed vocabulary + `Authority=min(Build,Assurance)` + external evidence | documentation language still needs drift gate |
| performance poisoning | observational data separated from causal rules | low-volume empirical bias |
| artifact substitution | SHA-bound critic/release manifests | Drive/file alias alone cannot authorize |

### Security promotion law

Do not state “security scan PASS” unless the named scanner actually ran. Repo-native static checks and dependency audits have their exact scope. External/full repository scanners remain separate authority.

## 3. Recovery model

### Destruction scenarios

Recovery must tolerate loss of:
- chat history;
- agent memory;
- local checkout;
- cached ContextPack;
- COS/graph projections;
- local read-model databases;
- local render cache.

### Durable recovery hierarchy

1. GitHub main/PR lifecycle and immutable repository history.
2. Promoted durable event history / immutable repo events.
3. Artifact registry + hash-bound durable media evidence (Drive when available).
4. Domain transactional stores that are themselves durably backed/qualified.
5. Rebuildable projections: ContextPack, state snapshots, COS, docs/status.

### Cold-recovery procedure

1. resolve live `main` SHA and open regression/barrier state;
2. load authoritative contracts/schemas at that SHA;
3. replay canonical event history to watermark; verify idempotency/revisions/content root where available;
4. overlay live GitHub lifecycle for PR/main facts;
5. rebuild State Snapshot and active ownership;
6. rebuild session/workstream graph and COS projection;
7. load artifact registry and verify referenced SHA-bearing artifacts;
8. if Drive unavailable, mark artifact-dependent paths `DEGRADED_EXTERNAL`; never invent availability;
9. compile ContextPack from rebuilt state;
10. compare important state/topology/blockers/next-safe-action to persisted recovery expectation;
11. only then allow new WRITE claim.

### Recovery invariants

- historical events are not rewritten to match present state;
- missing artifact bytes cannot be replaced by a report claiming they existed;
- projection hash mismatch invalidates projection, not source authority;
- live GitHub lifecycle overrides stale lifecycle projections;
- current session cannot inherit stale lease/claim authority;
- recovery never upgrades single-host evidence to multi-host authority.

## 4. Agent-death drill

A zero-context agent must determine within 5 minutes:

- North Star;
- current objective/phase;
- live main SHA;
- event watermark(s) and their authority;
- active barrier;
- active workstreams/scopes;
- open PRs and exact authority states;
- verified/unverified capabilities;
- candidate artifacts + hashes/availability;
- P0/P1 blockers/risks;
- tests/evidence required next;
- exact next safe action.

Failure to do so is a `CONTINUITY_DEFECT` and blocks production authority.

## 5. Recovery evidence packet

Every release-capable state should bind:

- Git SHA;
- event watermark/content root;
- state projection hash;
- graph snapshot hash;
- artifact manifest hashes;
- renderer/provider versions;
- test run IDs/conclusions;
- security review IDs;
- candidate/release manifest;
- recovery drill result;
- handoff/session IDs.

The packet is evidence, not a second mutable state store.
