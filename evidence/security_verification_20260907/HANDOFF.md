# Security verification integration — PR132

## Verified scope
Continue from PR132, stacked on PR131. Implementation `82f1eb8ecd524f3e514e1b1d32c078e2d1bf7601`; tested synthetic merge `e685d630c5a11697c1b0dcb130adbac8b0ff3af4`; Merge Safe `34149794390` SUCCESS. Read `verification.json` for exact evidence and limits. This is branch qualification, not main, CP1, production or PROJECT_DONE authority.

## What changed
Required same-interpreter audit and reused donor70 scanner are wired to one local/CI verifier. Missing checks cannot produce PASS. RUNNING invalidates an old PASS before work; step/failure receipts use atomic replacement. Actual child errors retain exit codes. Reused donor103 destination guard runs before the current NUL Git classifier. Required security CI saves its receipt even on failure. Remotion uses npx --no-install and preserves the existing frozen installation verifier.

## Evidence
Local scoped mirror: 288 passed (45 new,24 donor,219 inherited). Full CI: 582 passed,1 skipped,5 inherited warnings. All seven jobs PASS; 11 native events valid. Downloaded security receipt confirms scanner and pip-audit exit0. Artifact archives and media were independently hash-verified; ffprobe counted90frames at30fps,640x360. Self-review5134478165 is not independent approval.

## Recovery and next safe work
1. Re-read live main, PR132/base heads, Bus39 watermark, #48 and active claims. Existing snapshots grant no mutation authority.
2. Inspect PR132 final head and its own CI after this evidence-only commit. Do not silently inherit implementation CI to a changed tree.
3. Reuse this code; do not build a parallel verifier or re-import donor70/103 over it.
4. Continue remaining CP1 work: Python/toolchain and npm audit coverage, release-lineage donor104 and required review. Begin/continue the actual UI/CLI-to-backend/persistence product mapping rather than treating CI as product completion.
5. Preserve the #131 classifier/frozen Node installation and #130 final gate when integrating further donors. #128/#129 remain outside the scope.

## Rollback and boundaries
Use a bounded revert of this implementation on an owned branch, preserving evidence. Never reset main or force-update donor branches. Missing scanners or failed receipt writes must not be weakened to warnings to obtain green CI. Local hooks are bypassable; native main protection is still unapplied. No merge, deploy, provider/spend or #68 activation. Disk failure/SIGKILL or hostile concurrent filesystem is not fully handled by receipt replacement; uncompleted RUNNING evidence is not PASS. See verification.json for remaining scanner and audit limitations.
