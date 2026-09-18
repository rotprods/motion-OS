# MOTION.OS — PR CONVERGENCE MASTERPLAN — 2026-09-16

Status: **PLAN / NO PROMOTION AUTHORITY**  
Scope: converge all valid open-PR work into a small set of exact, reviewable promotion candidates without losing good work or merging stale/superseded branches blindly.

## 0. North Star

The goal is **not** “merge every open PR”.

The goal is:

```text
ALL VALID WORK
→ inventory
→ ancestry / overlap / supersession graph
→ repair incorporation
→ minimal converged candidate set
→ /codereview
→ /securityreview
→ /QAreview
→ exact-head local + clean-runner gates
→ serial merge
→ exact combined-main verification
→ canonical truth reconciliation
```

Success means the useful capabilities now stranded in branches become reproducible `main` truth with zero known P0/P1 and no false authority.

## 1. Live hard facts at plan creation

- `main`: `d4e628a1aef0cd382c3c2f1ea327a8ff70c41bd9`.
- `main.protected = false`; native branch protection is not enabled.
- Issue #48 is OPEN and explicitly blocks promotion while its exit criteria are unmet.
- Issue #39 remains the bootstrap coordination bus.
- `docs/MERGE_SAFE_TRAIN.md` requires serial merge / merge-group proof, no blind batch merges, and post-merge combined-head verification.
- Historical green CI on an old head is not current promotion evidence.
- Open PRs contain capabilities newer than `main`; therefore capability archaeology must inspect live PR heads.

### Immediate governance blocker

No product PR should be promoted while `main` is administratively unprotected. Existing Issue #7 already tracks this requirement.

Required repository setting before the train can claim production-safe governance:

- PR required for `main`;
- `Merge Safe / MERGE_SAFE` required;
- branch up-to-date / merge queue if available;
- force-push and deletion disabled;
- stale approvals dismissed on head mutation where human review is required.

The connected GitHub tool can observe but cannot reliably enforce all repository-admin protection settings. Until an admin applies them, operational discipline is not equivalent to native protection.

## 2. Promotion object: the graph, not the PR list

For every open PR create one node with:

```yaml
pr: 0
head_sha: ...
base_ref: ...
base_sha: ...
state: open|draft|ready
scope: []
changed_paths: []
authority_claim: ...
ci_evidence: []
physical_evidence: []
code_review: UNKNOWN|PASS|FAIL
security_review: UNKNOWN|PASS|FAIL
qa_review: UNKNOWN|PASS|FAIL
p0: []
p1: []
parents_or_donors: []
repairs: []
supersedes: []
superseded_by: []
overlaps: []
external_blockers: []
promotion_class: ...
```

Allowed `promotion_class` values:

- `TERMINAL_CANDIDATE` — candidate that should be requalified and may eventually merge.
- `STACK_ANCESTOR` — already contained in a terminal stacked candidate; do not merge independently unless ancestry proof fails.
- `REPAIR_REQUIRED` — fixes a demonstrated defect in a candidate; candidate cannot promote without it.
- `DONOR_ONLY` — contains unique valid deltas to transplant into a converged candidate.
- `QUALIFICATION_ONLY` — tests/evidence/projection; may remain separate from product promotion.
- `BLOCKED_EMPIRICAL` — implementation exists but required real-world/provider/corpus qualification is absent.
- `HISTORICAL_SUPERSEDED` — no unique valid delta after convergence; close unmerged with evidence.
- `REJECTED` — invalid/unsafe/no longer desired.

No PR is classified by title or age alone. Classification requires exact ancestry + diff evidence.

## 3. Known dependency / repair lines already proven

These relationships are current factual anchors, not the complete final graph.

### A. Product / recovery / release-hardening stack

A long stacked integration line culminates in PR #162 and then PR #165:

```text
... integration ancestors
→ #145 integrated product pixel + recovery
→ #147 operator hardening
→ #149 release rehearsal
→ #151 npm vulnerability gate
→ #153 frozen Python CI environments
→ #162 workflow supply-chain hardening
→ #165 recovery + SourcePack P1 repair
```

Critical finding: PR #165 physically reproduced `RECOVERY-REVISION-SPLICE` as P1 on frozen #162 and contains the repair. Therefore:

- unchanged #162 is **NOT promotable** even though prior exact-head checks were green;
- #165 is `REPAIR_REQUIRED` relative to #162;
- the eventual terminal candidate must contain both #162's valid stack and #165's repair, then receive its own exact combined qualification;
- do not borrow #165 evidence to approve unchanged #162.

Before promotion, compute exact ancestry for every earlier stack member. Any ancestor fully contained by the terminal candidate becomes `STACK_ANCESTOR`, not a separately merged PR.

### B. Semantic retrieval line

```text
#128 semantic knowledge plane
→ #163 evaluation-integrity repair
```

#163 fixes benchmark leakage and invalid target-group NDCG semantics. It does **not** prove real retrieval quality. The previous full-corpus run failed the target metrics.

Therefore:

- #163 is `REPAIR_REQUIRED` for the #128 semantic line;
- the repaired line remains `BLOCKED_EMPIRICAL` until physical reindex/graphify/evaluate passes the frozen corpus gates;
- do not merge an implementation whose evaluation was repaired but whose actual quality remains unknown merely because unit tests pass.

### C. Reverse-engineering / professional-edit line

```text
#64 frame-accurate video reverse engineering + EditingTemplate v1
├─ #96 S04 golden scene
├─ #107 S11 golden scene
├─ #124 S14 golden scene
├─ #125 S16 golden scene
└─ #157 active cross-golden 9D qualification
```

#64 contains the recovered system required for reference-conditioned professional editing. The current evidence includes a real physical reference specimen, 18 scenes, 98 parent actions, 32 subevents and 121 leaf operations.

#157 explicitly identifies #129 as an older overlapping T08 implementation usable as READ-ONLY donor evidence, while #157 is the active qualification line. Therefore #129 must not be merged as an independent competing qualification authority unless unique deltas are proven and deliberately transplanted.

#157 remains `QUALIFICATION_ONLY / BLOCKED_EMPIRICAL` while W2+ dimensions and full 9D/generalization are incomplete. This does not automatically prevent separately promoting the bounded #64 core after its own current-head reviews/gates and Issue #48 release.

### D. Renderer / media hardening candidates

Important candidate capabilities include, at minimum:

- #61 master-audio/mux authority;
- #62 physical HyperFrames runtime + provenance proof;
- #63 alpha qualification;
- #66 Lottie runtime;
- #69 color normalization;
- #70 static security gauntlet;
- #71 TTS semantic integrity;
- #73 claim verification;
- #76 provider telemetry trust;
- #77 performance-learning authority.

These must first be tested for ancestry/containment in later integration candidates. Do **not** assume they all require separate merges.

### E. Control-plane / truth / skill / QA candidates

At minimum:

- #56 canonical truth consistency;
- #57 skill failure-trace semantics;
- #58 session-native Event Fabric / truth consistency;
- #59 graph QA integrity.

These modify shared authority contracts. Before product promotion they require an overlap/contract-impact analysis against the terminal integration stack. If the stack already contains exact or successor implementations, mark the older PR `STACK_ANCESTOR` or `HISTORICAL_SUPERSEDED`; otherwise transplant/merge in a controlled order and rerun the whole combined candidate.

## 4. `/codereview` gate

For each terminal candidate or material donor delta, review the actual diff against the exact current base/synthetic merge.

Mandatory review axes:

- correctness and invariants;
- state/authority semantics;
- error paths and fail-closed behavior;
- hidden fallbacks / fake success;
- duplicate or competing implementations;
- schema/API compatibility;
- temporal/timebase correctness;
- idempotency/retry/recovery;
- mutable global state;
- concurrency/stale-writer behavior;
- deterministic replay;
- backwards compatibility / migration;
- dead code and stale docs that can misdirect future agents;
- oversized scope requiring split or stronger evidence.

Every finding must contain:

```yaml
finding_id: ...
severity: P0|P1|P2|P3
path: ...
line_or_contract: ...
failure_mode: ...
evidence: ...
repair: ...
verification: ...
status: OPEN|FIXED|ACCEPTED_RISK
```

Promotion gate: `P0=0 AND P1=0`.

A prior review on a different head does not transfer automatically.

## 5. `/securityreview` gate

Issue #48 R5 is authoritative for threat classes. Review at least:

- untrusted source files / media parser surfaces;
- prompt/source injection;
- secret/PII persistence;
- SSRF / URL / redirect / DNS-rebinding boundaries;
- subprocess/command construction;
- archive/path traversal and decompression/resource ceilings;
- artifact/hash/provenance forgery;
- stale writer / capability escalation;
- provider-spend authorization and timeout-after-accept ambiguity;
- auth/token/RBAC boundaries;
- dependency vulnerabilities;
- GitHub Actions supply chain, pinned Actions and least permissions;
- npm/Python reproducibility;
- external CDN/runtime integrity;
- unsafe deserialization / non-finite values / malformed evidence;
- recovery evidence laundering.

Promotion gate:

```text
security P0 = 0
security P1 = 0
required supply-chain workflows = PASS
remaining P2/P3 = explicit, bounded, non-promotional
```

The #165 repair demonstrates why green historic security/CI evidence is not enough: adversarial review can invalidate a prior candidate and must force requalification.

## 6. `/QAreview` gate

QA must test the capability claimed by the PR, not merely syntax/unit coverage.

Required layers, selected by impact:

- unit + contract tests;
- integration tests;
- regression tests for every escaped bug;
- adversarial/mutation tests where the boundary is security/authority critical;
- clean-checkout / cold-start test;
- exact-head reproducibility;
- physical media/runtime tests for rendering/extraction/audio/color paths;
- frame count/FPS/duration/hash validation;
- full-video temporal QA for creative release claims;
- recovery/replay/hash equivalence;
- cross-platform/runtime matrix where claimed;
- no skipped test is counted as executed evidence.

Promotion gate requires all applicable tests PASS on the exact candidate/synthetic merge. `SKIPPED_NOT_APPLICABLE` is evidence only that the gate did not run; it is not a PASS.

## 7. Exact promotion wave

### Wave 0 — Freeze and native governance

1. Keep Issue #48 promotion pause active.
2. Enable native `main` protection / required `MERGE_SAFE` under Issue #7.
3. Freeze direct main writes.
4. Snapshot live `main`, Issue #39 watermark, Issue #48 state, all open PR heads and CI associations.
5. Emit one `work.started` event for the convergence workstream with explicit scopes.

Exit: `main.protected=true` and no ambiguous writer.

### Wave 1 — Compile the complete PR graph

For every open PR:

1. record exact base/head;
2. determine merge-base / ancestor relationships;
3. compare changed paths and semantic contracts;
4. inspect explicit `supersedes`, `repair`, `stacked on`, `donor`, `historical` claims;
5. validate those claims against actual diff/ancestry;
6. assign `promotion_class`;
7. list unique valid deltas not present in any successor.

Exit: every open PR is classified; every unique valid delta has exactly one intended destination.

### Wave 2 — Build minimal convergence candidates

Do **not** modify donor history merely to make it look tidy.

Construct bounded convergence branches from latest protected `main` by:

- merging/cherry-picking terminal lines only when ancestry semantics require it;
- transplanting unique donor deltas with provenance;
- incorporating mandatory repairs (#165 over #162; #163 over #128 if semantic line is selected);
- excluding superseded duplicate implementations;
- resolving contract collisions explicitly rather than “ours/theirs” mechanically.

Likely candidate families:

1. **Control / truth / execution substrate** — canonical truth, event fabric, skill failure semantics, graph QA and any successor-equivalent implementations.
2. **Studio / renderer / reverse-engineering substrate** — qualified renderer/media capabilities plus #64 core where independent promotion is justified.
3. **Product / recovery / CI / security integration** — terminal stack culminating in the #162+#165 repaired convergence candidate.
4. **Semantic knowledge plane** — #128+#163 only after physical corpus requalification.
5. **T08 9D qualification** — evidence/qualification line; not product authority until its independent dimensions close.

This family map is provisional until Wave 1 proves actual ancestry/overlap.

### Wave 3 — Independent tri-review on frozen candidate heads

Freeze each candidate SHA.

Run independently:

```text
/CODEREVIEW
/securityreview
/QAreview
```

Then repair findings on a successor head; never mutate evidence to keep an old PASS label. Any material code/workflow change invalidates exact-head review/CI authority and restarts the relevant gates.

Exit: zero unresolved P0/P1 and signed/bound review receipt for exact head.

### Wave 4 — Local + clean-runner qualification

On each frozen candidate:

```text
python scripts/local_verify.py merge
→ MERGE_SAFE clean runner
→ Python 3.11 + 3.12
→ analysis physical gate
→ Remotion physical gate
→ dependency security
→ workflow supply-chain gate
→ domain-specific runtime/physical tests
```

Use only gates actually available and record unavailable ones explicitly. Never fabricate local/CI parity.

Exit: exact-head full-impact evidence green.

### Wave 5 — Synthetic merge / combined-head proof

Reconcile one candidate against the **current** `main` after all previous promotions.

Run the complete merge-group/full-impact suite on the actual synthetic result that would land.

If `main` advances during review, candidate proof becomes stale. Recompute and rerun.

Exit: exact synthetic merge has no regression or authority drift.

### Wave 6 — Merge exactly one candidate

1. merge one PR/convergence PR only;
2. read back `main` exact SHA;
3. full post-merge verification;
4. reconcile canonical state/read models;
5. emit immutable `pr.merged` and `main.verified`;
6. only then advance the next candidate.

No second merge while current main is `MERGED_NOT_VERIFIED`.

### Wave 7 — Close superseded branches safely

For each old PR marked superseded:

- prove its valid unique blobs/semantic deltas are present in `main` or explicitly rejected;
- persist a closure comment pointing to replacement commit/PR;
- close unmerged.

Never delete history needed for provenance.

### Wave 8 — Close Issue #48 only from evidence

Re-evaluate every #48 exit criterion against final main.

Required before closing the barrier:

- zero stale lifecycle facts in canonical docs/read models;
- one event semantics / deterministic projections;
- escaped-bug regression coverage;
- exact merge candidate and post-merge main full gates;
- P0/P1 code/security = 0;
- Phase06→Studio lineage proof;
- zero-context recovery proof;
- authority score/remaining deferrals honestly bounded;
- protected and verified `main`.

Only after these conditions hold can the global pause be released.

## 8. Decision rules that prevent another infinite loop

- Review and consolidation are bounded by promotion decisions, not by producing more architecture.
- If two PRs solve the same problem, choose/converge; do not maintain two authorities.
- If a PR is a strict ancestor of a qualified terminal candidate, do not review/merge it twice unless its semantics need independent promotion.
- If a line is empirically blocked, do the missing empirical test rather than writing another plan.
- If a review finds P1, fix that P1 before polishing P2/P3.
- Maximum three materially equivalent repair attempts; after that change strategy/root cause.
- Every session must reduce at least one of: unclassified PR count, open P0/P1 count, unverified candidate count, blocked empirical gate count, or unprotected-main risk.

## 9. Current next executable action

**Do not merge anything yet.**

Run Wave 1 and produce the machine-readable promotion graph from the live open PR set. Start with high-risk terminal lines:

```text
#162 → #165
#128 → #163
#64 → #157 (+ golden dependencies)
#56/#57/#58/#59 shared authority contracts
```

Then determine which older PRs are true ancestors/donors versus independent capabilities. After that, build the first convergence candidate and subject it to the exact tri-review.

## 10. Definition of Done

```text
MAIN_PROTECTED = TRUE
ISSUE_48 = CLOSED_BY_EVIDENCE
UNCLASSIFIED_OPEN_PRS = 0
UNACCOUNTED_VALID_DELTAS = 0
UNRESOLVED_P0 = 0
UNRESOLVED_P1 = 0
MERGED_NOT_VERIFIED = 0
CANONICAL_STATE_DRIFT = 0
POST_MERGE_MAIN_FULL_GATE = PASS
ZERO_CONTEXT_RECOVERY = PASS
```

Only then is the branch backlog considered converged rather than merely “merged”.
