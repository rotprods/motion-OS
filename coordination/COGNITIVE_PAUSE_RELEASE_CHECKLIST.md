# MOTION.OS Cognitive-Pause Release Checklist

Status: ACTIVE GATE
Canonical coordination bus: Issue #39
Regression control: Issue #48
Current Event Fabric PR: #58

This checklist defines the minimum conditions for explicitly releasing the MOTION.OS cognitive-pause / sync barrier. It is a gate, not a progress summary. A high average score cannot override a failed hard blocker.

## A. Live truth convergence
- [ ] Live `main` SHA reconciled immediately before release.
- [ ] Open/merged/closed PR lifecycle reconstructed from live GitHub.
- [ ] `state/project_state.json`, `STATE.md`, `TASKS.md`, `state/checkpoints.json`, `coordination/ACTIVE_AGENTS.yaml` and the latest projected state contain no contradictory *current* lifecycle/candidate claims.
- [ ] Historical/stale facts remain preserved as history and are not silently rewritten into current truth.
- [ ] Current release candidate identity is singular and hash-bound.

## B. Event Fabric / session convergence
- [ ] Every active mutating workstream has a unique `session_id`, `workstream_id`, `correlation_id` and declared resource scopes.
- [ ] Latest Issue #39 watermark, immutable repo events and runtime EventStore reconcile to one semantic event fabric.
- [ ] Cross-surface duplicate logical events dedupe when payload-identical.
- [ ] Cross-surface duplicate logical events fail closed when payload-conflicting.
- [ ] Semantic collision scopes (`contract:`, `architecture:`, `adr:`, `root-cause:`, `authority:`) are checked in addition to file/tree overlap.
- [ ] A zero-context agent can reconstruct current state and next safe action without chat history.

## C. Candidate evidence authority
- [ ] Release evidence binds exact `candidate_id`, artifact/media hashes, renderer identity and evidence revision.
- [ ] Historical fixtures cannot satisfy current-candidate release gates.
- [ ] Visual duration authority is `frame_count / fps`; mux/audio padding remains separate evidence.
- [ ] PRV, MNF and semantic beat identity remain fail-closed at Studio boundary.
- [ ] No skipped/cancelled workflow is interpreted as VERIFIED.

## D. Regression closure
- [ ] Every escaped bug in `docs/HISTORICAL_REGRESSION_MATRIX.md` has an implemented invariant and regression test or an explicit external/deferred classification.
- [ ] REG-006 combined-head freshness is enforced before merge.
- [ ] REG-017 semantic/root-cause collision detection is executable, not documentation-only.
- [ ] #59/#60 duplicate QA-history root cause has one canonical implementation path; the other is explicitly superseded/closed-unmerged.
- [ ] No unresolved P0/P1 correctness or false-authority finding remains.

## E. CI / merge train
- [ ] Candidate exact head passes `Coordination Contracts` where applicable.
- [ ] Candidate exact/combined head passes `Merge Safe / MERGE_SAFE`.
- [ ] Code review for the exact candidate head is complete.
- [ ] Security review for the exact candidate head is complete; scanner claims accurately state what actually ran.
- [ ] Any `main` advance after proof invalidates that proof and triggers reconciliation + rerun.
- [ ] Merge order/dependencies for active candidates are explicit and one-PR-at-a-time.
- [ ] Post-merge main verification plan is explicit.

## F. Product-critical gates
- [ ] Canonical truth/release evidence workstream is verified.
- [ ] SkillRuntime + QA graph integrity convergence is verified.
- [ ] Master-audio timing authority and alpha integrity are verified.
- [ ] HyperFrames physical runtime is either VERIFIED or explicitly non-blocking/deferred with evidence.
- [ ] Temporal multimodal critic gate is implemented/verified to the release tier required by the current candidate.
- [ ] Current creative candidate has candidate-bound quality evidence; no stale benchmark is promoted as current proof.

## G. Security / recovery / administration
- [ ] Cold restore/replay can reconstruct operational state from GitHub + canonical events + available evidence.
- [ ] Missing Drive/provider evidence degrades explicitly; it never fabricates recovery authority.
- [ ] Supply-chain critical Actions are SHA-pinned and dependency policy is reproducible at the required tier.
- [ ] Main branch protection/ruleset gap is either administratively closed or explicitly retained as a release blocker.
- [ ] No unresolved secret/PII, unsafe URL/SSRF, path traversal, subprocess/media parser, provider-poisoning or authority-escalation P0/P1 finding remains.

## H. Explicit release transaction
The barrier is released only by an explicit canonical event after all hard blockers above are satisfied or deliberately classified as non-release-blocking.

Immediately before release:
1. read latest Issue #39/Event Fabric watermark;
2. read live GitHub main/PR lifecycle;
3. invalidate any stale ContextPack;
4. recompute current state;
5. verify exact candidate evidence;
6. emit a release event containing exact main SHA, event watermark, verified candidate/PRs, deferred items and next promotion action.

No implicit release is allowed. A merged PR, green historical run, Todoist completion or chat instruction alone cannot release this barrier.
