# MOTION.OS Historical Regression Matrix

Status: ACTIVE under Issue #48
Authority: regression evidence index; not runtime write authority.

| ID | Escaped defect / drift | Root cause | Permanent invariant | Regression evidence / required test | Adjacent family to hunt |
|---|---|---|---|---|---|
| REG-001 | Remotion 3.0s visual treated as 3.050667s failure | container mux duration used as visual authority | visual duration = frame_count/fps; mux/audio padding measured separately | physical Remotion proof + verifier tests | VFR, audio lead/tail, container metadata drift |
| REG-002 | fencing token reset after release | active lease row doubled as generation authority | fencing generation is durable and monotonically increasing | transactional-store reacquire test | revision counters, consumer generations, render intent generations |
| REG-003 | JSON `date-time` accepted `yesterday` | schema format declared without real FormatChecker | format constraints must be executable, not documentary | agent-event validator negative test | URI/email/UUID formats, schema validators in other modules |
| REG-004 | replica refresh semantics could imply write permission | detection and mutation authority conflated | drift detection never grants overwrite; writes require explicit authority | replica reconciliation tests | Drive/Library sync, generated docs, cache refresh |
| REG-005 | provider timeout could duplicate paid render | network ambiguity treated like pre-submit failure | timeout after possible acceptance => reconcile before retry | provider failure simulation + render ledger | webhooks, uploads, publication APIs, billing calls |
| REG-006 | main advanced between PR proof and merge | exact-head evidence assumed to cover later combined tree | any main advance after proof invalidates merge authority until combined-head revalidation | PR #47 / MERGE_SAFE regression | stacked PRs, merge queue, dependency train races |
| REG-007 | cancelled CI risked ambiguous interpretation | workflow lifecycle and authority state conflated | cancelled/skipped != PASS/VERIFIED | MERGE_SAFE state handling | superseded workflow runs, manual reruns, flaky retry |
| REG-008 | stale topology kept merged PRs active | append-only history consumed as current state | live GitHub lifecycle supersedes stale projection; history remains immutable | session fabric lifecycle test | branches deleted/reopened, force updates, superseded plans |
| REG-009 | coordination freeze on #39 was not consumed before #44 merge | communication existed but irreversible-action preflight did not require newest watermark | before irreversible action: refresh event watermark + live GitHub + invalidate stale ContextPack | EF8 mandatory preflight test | publish/spend/deploy/delete operations |
| REG-010 | same logical event can arrive through multiple surfaces | transport identity could become domain identity | one canonical event semantics; identical logical event dedupes; conflicting duplicate fails closed | session fabric cross-surface tests | webhook + polling duplication, repo + runtime replay |
| REG-011 | surface payload hash could be trusted without recomputation | adapter-provided integrity metadata trusted | declared hash must equal canonical payload hash | `SurfaceEvent` tamper test | artifact hashes, provider metadata, Drive evidence |
| REG-012 | session compiler accepted unrelated correlation | session identity enforced but task lineage not | session projection accepts only its session_id + correlation_id | cross-correlation test | workstream injection, project injection, parent from unrelated aggregate |
| REG-013 | canonical truth files disagree after capability promotion | hand-maintained state surfaces drift independently | current-state human/machine views must derive from or validate against one projected truth | `CanonicalTruthConsistency` gate REQUIRED | STATE/TASKS/HANDOFF/checkpoints/project_state/ACTIVE_AGENTS |
| REG-014 | historical release test can masquerade as current evidence | fixture not bound to current candidate/media hash | release evidence must bind candidate ID + media hash + evidence revision | audit current release tests | stale semantic reviews, benchmark fixtures, old scorecards |
| REG-015 | duplicate alignment weights JSON/YAML | duplicated machine authority | one canonical machine source or enforced semantic parity | parity/canonicalization test REQUIRED | schemas/config duplicated across JSON/YAML/MD |
| REG-016 | product score and regression-risk score can be conflated | one scalar used for different decision domains | maintain Product North Star and Promotion Risk as separate scorecards; hard blockers override both | scorecard contract REQUIRED | build/assurance/authority conflation |

## Canonical truth consistency target
The next gate must compare at least:
- live GitHub main/PR lifecycle;
- `state/project_state.json`;
- `STATE.md`;
- `TASKS.md`;
- `state/checkpoints.json`;
- `coordination/ACTIVE_AGENTS.yaml`;
- latest immutable agent events / event watermark;
- current release candidate evidence.

Contradictory current lifecycle/capability/candidate claims fail visible. Historical documents may remain historical only when explicitly labelled non-current.

## Current known truth drift on main@080dfd5
- `state/project_state.json` still identifies v0.9.1-rc06-working / RC07 candidate and old P0 wording.
- `coordination/ACTIVE_AGENTS.yaml` still lists PR #44 as FINAL_QUALIFICATION although #44 is merged.
- Issue #48 reports STATE/TASKS/checkpoints disagreement and duplicate alignment-weight policy sources.

These are regression inputs, not permission to overwrite another agent's active scope without preflight.