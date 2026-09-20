# Release-lineage integration — zero-context handoff

## Exact scope
PR133 on PR132, implementation `7dc42a1035ad380ed6b9391f56635cf553b76677`, tested synthetic `672848cd7527323a215b007fe350c4ba6150b821`, Merge Safe34153730274 SUCCESS. Reuse existing strict verdict/NUL classifier/frozen Node install/shared security verifier. Do not rebuild the stack or overwrite donors102/104.

## What changed
Strict release-state types and committed Git-blob identity; exact target-main merged-PR/repository lifecycle; repeated live/local drift checks; bounded fixed-origin GitHub GET with no redirects; module entrypoints and failed receipts. PASS is lineage-only, with promotion_authorized=false, never publishing permission. Both new workflow definitions are read-only, not actual main/tag executions.

## Executed
87 new local tests; 374 scoped regression pass/1 deselected (full-checkout-only test, executed in CI); full CI669pass/1skip/5inherited warnings. Actual actionlint over9 workflows and static scanner/auditor passed. Downloaded security/verdict/runtime ZIPs match API SHA and size. Physical ffprobe90frames/30fps/640x360; video hash identical to prior technical fixture. Review5134729871 is same-agent, not independent approval. See verification.json for exact hashes and commands/surface boundaries.

## Live context must refresh
At capture main=d4e628a1aef0cd382c3c2f1ea327a8ff70c41bd9 and native protection absent. Bus39 claim5574579575; parent handoff5574290739. Reread newest main, #39 watermark, #48, PR133/base and claims before mutation. This snapshot never grants current authority. Keep DRAFT, no merge/deploy/spend/#68 activation. Evidence-only head must receive its own CI; its final identity belongs in the live PR/Bus checkpoint, not assumed here.

## Concrete next functional work
src/studio/inspector.py blob60e00e65f96790696516e67147aa215daa67f986 has a reproduced missing-manifest false recovery-ready result. One Layer with no render manifest yields true; same graph with empty assignments yields false. See studio_recovery_gap.json. This is the actual function with a synthetic graph-protocol fixture, not full product E2E. NOT repaired in this release PR. Check current callers/donor integrations/ownership (including QA/recovery branches) before a bounded regression+fix. Do not treat the P7.2 agent recovery drill as this separate inspector surface.

## Remaining terminal gates
Python/toolchain freeze, npm audit, zizmor, cache/retention completeness and independent CP1 acceptance remain. Native GitHub protection and #48 authorization remain separate. Product UI/CLI-backend-persistence-render/semantic QA needs its own real journeys. Last-read checks are not a lock; trusted single-run filesystem assumptions persist. Never declare PROJECT_DONE from this wave.
