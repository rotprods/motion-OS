# MOTION.OS — GitHub `main` Protection Target

Status: DESIRED STATE / NOT APPLIED BY THIS DOCUMENT
Owner gate: T8.3

## Live audit at definition time

The repository administration read surface reported:

- `main.protected = false`;
- branch-protection enforcement disabled;
- repository rulesets = `[]`.

Those facts are blockers, not permission to claim administrative assurance. The current ChatGPT GitHub integration can read these surfaces but cannot apply branch-protection/ruleset mutations.

## Required target

`main` must eventually enforce all of the following through GitHub-native branch protection or a repository ruleset:

1. Changes enter `main` through a pull request; direct push is not an accepted promotion path.
2. Required status check: `MERGE_SAFE` from the `Merge Safe` workflow.
3. Candidate must be tested against current `main`; an advance of `main` invalidates stale promotion evidence and requires combined-head revalidation.
4. Force pushes to `main` are disabled.
5. Branch deletion is disabled.
6. Required conversation resolution is enabled when supported by the repository plan/ruleset surface.
7. Stale approvals are dismissed or a fresh approval is required when the candidate changes materially, when supported.
8. Administrative bypass is minimized and any intentional bypass must remain visible/auditable; routine agent operation must not depend on bypass.
9. Merge queue may be enabled only if the resulting merge-group execution runs `MERGE_SAFE` and preserves the repository's exact-head/combined-head invariant.
10. A green historical check, cancelled check, skipped required check, or check from a stale SHA never counts as promotion authority.

## Verification procedure

T8.3 may become VERIFIED only after a fresh live read demonstrates the administrative controls are actually active. At minimum record:

- repository;
- protected branch/ruleset ID;
- enforcement state;
- target branch selector;
- required status check names/integration IDs where exposed;
- force-push/deletion settings;
- PR requirement;
- conversation/approval settings if used;
- live `main` SHA at verification time;
- verifier session/event ID.

Then exercise an adversarial promotion check where feasible:

- an unverified PR cannot merge;
- a stale candidate cannot merge without fresh current-main evidence;
- direct/force update to `main` is rejected by GitHub policy rather than merely discouraged by documentation.

## Authority boundary

This document is an executable target specification, not evidence that GitHub currently enforces it. Until the live administration API reports the controls installed, T8.3 remains `BLOCKED_EXTERNAL / ADMIN_CONTROL_UNAPPLIED` and the #39/#48 release barrier must treat lack of main protection as a promotion risk.
