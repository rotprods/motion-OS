# CI convergence — qualified stacked candidate, not promotion

PR131 builds on PR130 without rewriting donors or main. Implementation:
`eb0f104caf6efad5113a322210d676721fde0266`. Tested synthetic merge:
`5ae1d4715ab20eb27969ff248c315e2e62d93ab6`.

## Proof
Merge Safe 34146588775 and Coordination Contracts 34146588637: SUCCESS.
Full Python3.12 suite: 513 passed, 1 skipped, 5 inherited warnings.
Local exact-file mirror: 219 passed, including 77 new regression cases.
Actual actionlint1.7.12 executed after archive digest verification.
Actual two npm ci installs kept approved manifest/lock byte-identical;
Remotion typecheck, composition discovery, physical render and media verifier passed.
Downloaded runtime and verdict ZIPs were independently SHA256 checked.
Local ffprobe counted90 frames at30fps, 640x360; video SHA matches prior SC06 fixture.

## Scope
Existing shared classifier + NUL Git transport + local hook + all8 current workflows
+ exact PR95 lock + frozen-install receipt required by the existing Remotion job.
PR58 pinning and PR56 authority coverage selectively reconciled, not duplicated.
PR130 final verdict remains unchanged. No production/provider/spend/automation change.

## Resume
Re-read live main, Issue39, Issue48 and PR130/131 heads first. Do not repeat this fix.
Reconcile Python/toolchain locks, missing-scanner fail-closed behavior, donor103 local
push protection and donor104 release-lineage before final CP1 acceptance. Inspect
foreign branch-only workflows when imported. Then proceed to bounded backend/UI
integration and real product E2E. Shared CI scope is released by the final Bus handoff.

## Limits
CP1, release, whole-product integration and independent acceptance remain incomplete.
The first verification.json records the tested implementation, not a later commit's
CI by implication. Query any later evidence-only head separately before promotion.
Rollback means reverting owned candidate commits, never resetting donors or main.
