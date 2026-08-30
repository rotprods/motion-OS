# MOTION.OS V2 — Gap / Risk Matrix

Authority: PROPOSED_V2
Source revision: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`
Priority model: Impact × Probability × Blast Radius × Strategic Importance ÷ Cost, with P0 correctness/security/authority overrides.

| ID | Gap | Sev | Probability | Blast radius | Current detection | Current mitigation | Target fix | Owner/workstream | Test/evidence | Phase |
|---|---|---:|---:|---:|---|---|---|---|---|---|
| V2-G001 | Current-state split brain across STATE/project_state/TASKS/HANDOFF | P0 | High | Very High | Issue #48/manual reconciliation | Live GitHub precedence | Canonical projector + drift CI; human docs generated/validated | canonical-truth / PR#56 | contradiction fixtures + live lifecycle overlay | V2-P1 |
| V2-G002 | Event Fabric v3 branch-head verified but unpromoted; runtime watermark unavailable from main | P0 | High | Very High | #39/#48 barrier | Bootstrap Issue #39 + repo events | Serial promotion only after release checklist; canonical multi-surface projector | event-fabric / PR#58 | replay/dedupe/conflict/preflight/cold-recovery | V2-P1 |
| V2-G003 | `main` lacks administrative protection/ruleset | P0-GOV | Medium | Very High | GitHub live `protected=false` | protocol + MERGE_SAFE discipline | Admin ruleset requiring MERGE_SAFE, no force push/deletion | operator/admin | ruleset readback + prohibited direct-push drill | V2-P8 |
| V2-G004 | RC09E physical artifact/hash unavailable in inspected GitHub surfaces | P0-PRODUCT | High | Very High | temporal-critic handoff | RC06 rollback remains registered | Recover/version RC09E in artifact authority with SHA + manifest | product/artifact owner | hash-bound recovery + ffprobe + registry proof | V2-P6 |
| V2-G005 | Full-video temporal multimodal critic contract exists but provider run unqualified | P0-PRODUCT | High | Very High | PR#65 authority boundary | fail-closed provider attestation | Trusted provider run on exact RC media + timestamped evidence | temporal-critic / PR#65 | full-video samples + provider identity + evidence hash | V2-P6 |
| V2-G006 | Creative convergence < release threshold / no current authoritative RC score | P0-PRODUCT | High | Very High | product scorecards | release blocked | Candidate tournament bound to exact artifact + critic evidence | creative tournament | semantic≥9, motion≥9, type≥9, transitions≥8.8, finish≥9, P0/P1=0 | V2-P7 |
| V2-G007 | HyperFrames physical runtime not on main | P1 | Medium | High | PR#62 | compiler-ready path | exact pinned runtime render + partial render + artifact verifier | HyperFrames / PR#62 | frame_count/fps, hash, lint/render evidence | V2-P5 |
| V2-G008 | Lottie player proof blocked by workflow mutation authority | P1 | Medium | Medium | PR#66 | compiler subset fail-closed | CI-authorized browser verifier with pinned lottie-web bundle integrity | Lottie / PR#66 | DOMLoaded, frame seeks, PNG hashes, totalFrames | V2-P5 |
| V2-G009 | Multi-render audio/alpha/color contracts are separate branch workstreams | P1 | Medium | High | PR#61/#63/#69 | isolated contracts | serial integration + physical heterogeneous master | render integration | global clock/z/audio/alpha/color artifact proof | V2-P5 |
| V2-G010 | Primitive historical 15/30 aggregate not ID-bound | P1 | High | Medium | PR#67 | aggregate has no authority effect | 135 primitive×renderer qualification ledger | primitive QA / PR#67 | per-fixture artifact SHA + visual duration | V2-P7 |
| V2-G011 | 25 benchmark briefs not rendered/labeled authoritatively | P1 | High | High | TASKS/GOAL | benchmark definition only | render + label all 25 with artifact-bound score evidence | product benchmark | APSR/GSR + per-brief manifests | V2-P9 |
| V2-G012 | Visual DNA corpus <10 heterogeneous refs and retrieval quality unqualified | P1 | High | Medium | TASKS | physical extraction foundation | analyze ≥10, persist signatures, evaluate retrieval, render ≥3 | visual-dna | taxonomy/evidence coverage + retrieval precision + renders | V2-P7 |
| V2-G013 | Phase06 CAL2 performance learning lacks ≥30 real productions / ≥5 topics | P1 | High | High | Phase06 policy | no causal authority from observation | empirical corpus + separation correlation/causation | content learning | production lineage + performance evidence | V2-P9 |
| V2-G014 | Spend authorization historically accepted malformed numeric/domain inputs | P1-SEC | Medium | High | PR#74 | explicit auth/preflight | finite/nonnegative domain validation + exact bool authority | spend policy / PR#74 | NaN/inf/negative/bool/retry adversarial suite | V2-P4 |
| V2-G015 | TTS numeric semantic class historically reducible to digit survival | P1 | Medium | High | PR#71 | branch regression suite | semantic class/value preservation and locale-safe ambiguity | TTS / PR#71 | percentage/currency/decimal/version/name families | V2-P4 |
| V2-G016 | Claim normalization historically could fabricate verification timestamp | P1-AUTH | Medium | High | PR#73 | branch fail-closed invariant | timestamp+evidence attestation at construction/factory | claim authority / PR#73 | direct-constructor bypass + stable claim identity | V2-P4 |
| V2-G017 | Graph QA/repair run identity and mutation semantics historically misleading | P1 | Medium | Medium | PR#59 | branch fix | run-scoped QA/Defect; ADDRESSES defect; MUTATES actual target | graph QA / PR#59 | multi-run history + mutation-target tests | V2-P4 |
| V2-G018 | Skill executor exceptions historically could escape without durable FAILED trace | P1 | Medium | Medium | PR#57 | strict/non-strict runtime | persist sanitized FAILED + downstream BLOCKED | skills / PR#57 | secret-bearing exception regression + graph projection | V2-P4 |
| V2-G019 | Recovery depends on Drive plane whose availability is not always proven | P1 | Medium | High | explicit DEGRADED_EXTERNAL | GitHub + event cold recovery | versioned artifact manifests + Drive bridge qualification | recovery | cold rebuild with/without Drive, identical authority subset | V2-P8 |
| V2-G020 | ACTIVE_AGENTS/AGENT_PROTOCOL contain historical topology statements | P1 | High | Medium | bootstrap authority label | live GitHub must override | projector-generated ownership/topology + stale-claim TTL | coordination | zero-context stale-bootstrap adversarial drill | V2-P2 |
| V2-G021 | npm renderer reproducibility incomplete in some runtime paths | P1-SUPPLY | Medium | Medium | PR#70 | pinned package versions in some jobs | lockfiles + `npm ci` + integrity evidence where applicable | renderer owners | clean install reproducibility + dependency audit | V2-P8 |
| V2-G022 | ContextPack revision unavailable for this V2 session from promoted authority | P2 | High | Low | explicit null | scope limited to additive files | promote Event Fabric and compile sealed fresh ContextPack | event-fabric | context hash bound to main+watermark | V2-P2 |
| V2-G023 | Graph database/vector database not required but remains architectural temptation | P2-COST | Medium | Medium | anti-overengineering rules | NetworkX+SQLite | measured scale triggers only | architecture | benchmark trigger evidence before migration | V2-P10 |
| V2-G024 | Documentation lacks uniform authority/scope/owner/source_revision metadata | P2 | High | Medium | manual review | canonical files + issue history | documentation header contract and projection rules | docs | doc metadata validator | V2-P3 |
| V2-G025 | Accidental duplicate/no-op issue creation can pollute operator surfaces | P2-OPS | Low | Low | live lifecycle | immediate close/not_planned | operator tooling guard: validate intended action/resource before mutation | agent tooling | mutation-preflight test for issue/branch actions | V2-P8 |

## Hard promotion blockers

Any one of these keeps V2/release promotion blocked irrespective of weighted scores:

- false current-state authority;
- unresolved P0 security/correctness;
- Event Fabric contradictory duplicate not failing closed;
- exact-head/combined-head proof invalidated by main drift;
- RC artifact/evidence identity mismatch;
- full-video critic not bound to the release artifact;
- PRV/MNF/Beat/content identity mutation;
- provider timeout-after-accept retried without reconciliation;
- unrecoverable authoritative state;
- hidden second source of truth.

## Current executable frontier

Parallel safe lanes after scope reconciliation:

1. **Truth/Event lane:** #56 + #58, then barrier release decision.
2. **Core correctness lane:** #57 + #59 + #71 + #73 + #74.
3. **Renderer lane:** #61 + #63 + #69 + #62 + #66, then heterogeneous master proof.
4. **Product assurance lane:** #64 + #65 + #67, then RC artifact recovery and creative tournament.
5. **Security/recovery lane:** #70 + #58 cold recovery + admin branch protection.

Serial convergence is required before irreversible promotion; open branches are not composable authority by declaration.
