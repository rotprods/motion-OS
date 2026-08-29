# MOTION.OS V2 — Gap / Risk Matrix

Authority: PROPOSED_V2_CANDIDATE
Source revision: `main@a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d`
Scoring: priority ≈ impact × probability × blast radius × strategic importance ÷ cost. P0/P1 correctness/security/false-authority override score.

| ID | Gap / risk | Sev | Probability | Blast radius | Detection today | Current mitigation | Target fix / owner | Evidence required | Phase |
|---|---|---:|---:|---:|---|---|---|---|---|
| G01 | Canonical current-state surfaces contradict live topology/runtime history | P0 | High | Project-wide | Manual audit; #56 | Live GitHub supersession rules | Canonical projector/validator; PR #56 owner | exact lifecycle/state parity test + main proof | V2-P1 |
| G02 | `ACTIVE_AGENTS.yaml` lists merged #44 as active | P1 | Certain | Agent coordination | Manual/live diff | File declares itself bootstrap-only | Generate/validate active read model from live state; #56/#58 coordination | zero-context agent returns correct owners | V2-P1 |
| G03 | Bootstrap Bus #39 body is historically stale and can be mistaken for current truth | P1 | High | Agent coordination | Newer comments override socially | Event Fabric/current-watermark rules | Treat issue body as historical bootstrap only; projector consumes supersession/live GitHub | stale-body adversarial test | V2-P2 |
| G04 | `main` lacks GitHub-native branch/ruleset protection | P1 | Certain | Release/integrity | Live admin read | Protocol + MERGE_SAFE discipline | Apply ruleset externally; PR #70 target spec | live ruleset/protection read + adversarial blocked merge | V2-P11 |
| G05 | Event Fabric remains branch-qualified, not promoted | P1 | High | All multi-agent work | PR #58 tests | Bus #39 + main contracts | Qualify/reconcile/promote #58 after barrier | combined-head MERGE_SAFE + zero-context/recovery | V2-P2 |
| G06 | Autonomous next-wave compiler depends on unpromoted Event Fabric | P1 | High | Autonomous execution | PR #68 dependency explicit | Kept draft/disabled | Promote only after #58 and barrier release | stacked + post-promotion exact-head evidence | V2-P12 |
| G07 | QA graph can preserve misleading/colliding historical identities unless #59 converges stronger #60 invariants | P1 | Medium | Repair/replay | Regression audit | #59 draft | Atomic full collision preflight + non-Run alias rejection | adversarial replay/collision tests | V2-P4 |
| G08 | `RECONSTRUCT_EXACT` can imply more frame authority than evidence provides | P0 | Medium | Reverse engineering / fidelity | Manual audit #64 | Draft/not promoted | Require decoded frame count/time base authority or fail closed; approximate modes explicit | real-video frame clock tests | V2-P6 |
| G09 | Temporal critic contract is not yet empirically bound to a real recoverable master | P0 | Certain | Release quality | #65 states artifact unavailable/provider unqualified | Release blocked | Recover/hash master, execute provider through contract, bind defects to valid frame/time evidence | full-video provider result + manifest | V2-P7 |
| G10 | Temporal evidence causality can drift across provider run/frame clock/defect interval | P0 | Medium | QA/release | Red-team findings | #65 draft | exact `provider_run_id`, timestamp≈frame/fps, defect evidence intersects interval | adversarial causality suite | V2-P7 |
| G11 | HyperFrames physical proof needs exact source/spec/runtime/run/artifact provenance binding | P1 | Medium | Renderer authority | T4 review | physical render evidence exists | Bind manifest root + runtime version + run ID + artifact hash; #62 | clean-runner physical evidence | V2-P5 |
| G12 | Alpha plane presence does not prove semantic transparency survives real composite | P1 | Medium | Visual correctness | #63 physical plane proof | explicit partial authority | composite fixtures with expected alpha pixels/edges + output inspection | physical compositor alpha evidence | V2-P5 |
| G13 | Cross-render color contract not yet integrated/empirically measured | P1 | Medium | Visual fidelity | #69 | fail-closed profile contract | integrate after assembly ownership; measure ΔE/metadata | physical heterogeneous render composite | V2-P5 |
| G14 | Lottie compiler is not physically browser-player qualified | P1 | High | Renderer diversity | #66 | compiler_ready only | CI-authorized official lottie-web player proof | player evidence + sampled PNG hashes | V2-P5 |
| G15 | Node/Remotion dependency resolution is non-reproducible without lockfile | P1 | High | CI/render supply chain | T8.4 | package/version assumptions | Generate valid lockfile by renderer owner; use `npm ci`; bind dependency identity | clean runner install/render repeatability | V2-P10 |
| G16 | Static/dependency security scans do not cover all boundary-specific attacks | P1 | Medium | Security | #70 explicit boundary | manual threat review | boundary-specific SSRF/path/media/prompt/provider tests; full scanner when available | security gauntlet evidence | V2-P10 |
| G17 | Provider telemetry DNS rebinding risk exists downstream of literal URL validation | P1 | Low/Med | Network fetch | #76 explicit residual | no fetch in adapter | downstream fetch allowlist or resolve-and-revalidate | controlled SSRF tests | Triggered when fetcher exists |
| G18 | Aggregate primitive claim `15 verified / 30 quarantined` lacks per-ID surviving evidence | P1 | Certain | Qualification | #67 | authority_effect=NONE proposed | ID-bound ledger + physical 135 renderer cases | per-case artifacts/test runs | V2-P8 |
| G19 | Aggregate benchmark `25 briefs / 5 styles` is not empirical APSR/GSR authority | P1 | Certain | Product claims | #75 | mechanical-only proof + legacy claim none | Exact suite manifest + real style/creative evidence | per-brief artifact + creative scores | V2-P8 |
| G20 | Mechanical benchmark renders show generic runtime-proof grammar, not style generalization | P1 | Certain | Product quality | manual frame review in #75 | creative authority blocked | upgrade creative generation path + authoritative style critic | unseen brief style fidelity evidence | V2-P8 |
| G21 | Performance learning can be poisoned by caller assertions/duplicate evidence without #77 | P1 | Medium | Learning loop | #77 audit | draft | evidence-bound support IDs + controlled-test identity | contract/adversarial tests | V2-P9 |
| G22 | Claim verification historically fabricated verification timestamp from normalization | P1 | Medium | Research/content trust | #73 | branch fix | evidence+timestamp atomic attestation | exact-head tests + later promotion | V2-P3 |
| G23 | TTS normalization can preserve digits while changing semantic class | P1 | Medium | Script integrity | #71 escaped-bug tests | branch fix | semantic-class-aware protected claims | adversarial semantic integrity corpus | V2-P3 |
| G24 | Spend guard can be bypassed by non-finite/truthy/stale authorization values | P0 | Low/Med | Cost/provider | #74 | branch fix | literal booleans, finite budgets, current retry authorization | security/adversarial tests | V2-P3 |
| G25 | Provider telemetry can carry malformed/secret-bearing/untrusted values | P1 | Medium | Security/data | #76 | branch fix | fail-closed typed telemetry boundary | adversarial tests | V2-P3 |
| G26 | Renderer artifact/evidence can belong to a different source if provenance is partial | P0 | Medium | Release correctness | scattered verifiers | hashes exist but not universally chained | canonical EvidenceEnvelope binds source→spec→runtime→run→artifact→critic→release | mutation/cross-attachment tests | V2-P4/P7 |
| G27 | Multiple docs/ADRs/plans can become competing architecture authorities | P1 | High | Human/agent decisions | manual | historical naming | V2 canonical docs metadata + SUPERSEDED registry + doc validation | documentation authority test | V2-P1/P13 |
| G28 | Semantic collision detection can miss file-disjoint same-authority/root-cause changes in weak consumers | P1 | Medium | Multi-agent | REG-017 | #58 canonical semantics | every selector/agent SDK imports one conflict engine; no duplicate implementation | parity/property tests | V2-P2 |
| G29 | Main may advance after a candidate’s green CI | P0 | Medium | Merge correctness | REG-006 | combined-head rule | irreversible preflight + merge queue/current-main proof | race simulation | V2-P11 |
| G30 | Cancelled/skipped CI can be overclaimed as verified | P1 | Medium | Assurance | policy/docs | explicit statuses | evidence model stores PASS/FAIL/SKIPPED/CANCELLED/NOT_RUN separately | evidence parser tests | V2-P10 |
| G31 | Chat/agent death can still lose latest branch-only context/evidence | P1 | Medium | Continuity | zero-context branch tests | Bus/checkpoints | session handoff bundle + durable Event Fabric + live topology projection | 5-minute death drill | V2-P12 |
| G32 | Drive unavailability can break artifact recovery | P1 | Medium | Recovery | cold recovery proof | DEGRADED_EXTERNAL semantics | manifest every missing external artifact; local/GitHub rebuild of state remains deterministic | disaster drill | V2-P11 |
| G33 | COS graph could become hidden authority if consumers reverse-write from projection | P0 | Low | Architecture-wide | constitutional rule | one-way adapters | enforce no reverse-authority APIs + tests | projection rebuild/no-write tests | V2-P2 |
| G34 | Overengineering risk: premature Postgres/queues/CDN/vector DB | P2 | Medium | Complexity/cost | ADR trigger policy | defer | explicit measured triggers only | decision ledger with reconsideration thresholds | continuous |
| G35 | Product can become architecturally correct but creatively mediocre | P0 Product | High | North Star | #75 mechanical artifacts exposed this | quality gate >=9 | real creative tournament + unseen briefs + benchmark diversity + human/critic evidence | empirical suite | V2-P8/P14 |

## Highest-value critical path

`G01/G05 -> G07/G08/G10 -> G11/G12/G13/G14/G15 -> G09 -> G18/G19/G20 -> G21 -> G04 -> final migration/release`

Parallelizable security/content hardening (#70/#71/#73/#74/#76/#77) may proceed while renderer/temporal owners work, provided semantic scopes do not collide.

## Hard-stop rules

Any of the following means `NO_PROMOTION` regardless of score:

- false authority or current-state contradiction;
- P0 security/correctness finding;
- stale combined-head evidence;
- unresolved event/semantic ownership collision;
- artifact/evidence identity mismatch;
- inability to reproduce/recover critical state;
- temporal/product release claim without real full-video evidence;
- administrative irreversible action without required authority.