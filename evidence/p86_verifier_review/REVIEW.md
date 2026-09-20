# P8.6 — Verifier code / security / QA review

Date: 2026-09-14. Repository: rotprods/motion-OS. PR: #162. Base: `45cf9c43740996abf399861cbb22ed779abb5ead`.
Session: `motion://session/chatgpt/cgev2/20260914-p86-verifier-review`.
Bus #39 claim: `5671406324`. Program: #93. Workstream: #158. #48 remains a promotion barrier.

## Scope and baseline
This is a bounded review of the workflow policy, receipt lifecycle and its CI connections, not an independent whole-repository or production certification. The base had seven successful CI workflows; that did not demonstrate that the new policy rejected hostile configurations. The exact original script was reconstructed locally and verified as Git blob `05a11c7e2128f2f07e66ea2582a37933b27f192f`.

`red_baseline.json` records ten unsafe outcomes: eight policy false negatives (permission comments/quotes, inline privileged trigger, quoted action key, fake credential comment, cross-step credential borrowing, step/job timeout confusion, missing executable structure) and two real CLI filesystem outcomes (predictable temporary symlink overwrite; stale PASS after invalid UTF8). The eleventh attempted case already failed and is NOT counted as another bypass. These fixtures were never uploaded as executable workflows.

The initial 46 new regression cases ran against the original code: **36 failed, 10 passed**. The final local suite is **76 passed**: all 21 original tests (exact blob `82ba9a1a1b0863c0f9e6b760895eb4a7cd9f8a1c`) plus 55 new cases. Unit count is not vulnerability count.

## Decision and repair
Keep the existing stdlib-only policy as a bounded companion to mandatory actionlint and independent zizmor. Do not pretend regex over arbitrary YAML is a semantic security verifier. The policy now constructs scoped entries for the repository's canonical two-space block syntax. Quoted scalar values/comments are handled; literal/folded block bodies remain data. Checkout/upload settings must belong to the same step's `with`; job timeout must belong to that job. Unknown matrix versions, unreviewed local actions, malformed Docker digests and ambiguous/missing structures reject.

Unsupported YAML is explicitly rejected: quoted keys, flow mappings, aliases/tags/merge keys, multiple documents, multiline quoted scalars and noncanonical indentation. This intentionally rejects some valid YAML. A future requirement for those forms calls for a reviewed, pinned semantic parser integration, not another silent fallback. This policy does not parse arbitrary shell programs, recursively audit action code or replace actionlint/zizmor.

Receipt schema v2 preserves status/findings/count semantics, adds workflow input SHA256 and `promotion_authorized=false`, and distinguishes FAIL from BLOCKED. Output is relative to `--root`, must be JSON, cannot target configuration/code or observed symlinks. RUNNING replaces an old report before audit; random exclusive same-directory temporary files plus fsync/replace prevent the reproduced predictable-name overwrite. Missing/unreadable/oversized/unsafe inputs fail; FIFO reads do not wait for a writer. Errors do not echo arbitrary input or exception messages.

The implementation assumes a trusted single-writer workspace. It is not a hostile concurrent parent-directory/TOCTOU defense. SIGKILL or disk failure can prevent final persistence; RUNNING or exit != 0 cannot authorize anything. A PASS file alone is not authority: require a successful current invocation, matching input hashes and CI revision binding. OS runner labels and FFmpeg package resolution remain non-content-addressed residuals.

## QA / connections
The existing required Merge Safe quick job already invokes this same policy; no parallel promotion engine is added. The policy workflow runs both regression modules, records JUnit results and retains exactly the scanned workflow source files with the report for independent replay. It does not upload arbitrary workspace files.

The frozen Product E2E/replay filter omitted `scripts/local_verify.py` and `scripts/verify_node_lock.py` despite executing them. Both are now covered, as are policy source/tests. New tests validate these trigger edges, preserve the separate independent analyzer and ensure destruction precedes archive-only recovery. The physical fixture and all renderer semantics are unchanged.

## Executed locally / pending remotely at this commit
- New regression baseline: RED as above.
- Final scoped pytest: 76 PASS, no skips/failures.
- compileall: PASS.
- Exact changed-workflow policy and existing test blob checks: PASS.
- Full local clone: DNS-blocked. Full local repository pytest, actionlint, zizmor and physical render are NOT claimed here.
- Required next acceptance: actual candidate Merge Safe, Workflow Supply-Chain Security (both jobs), Frozen Product E2E and archive-only recovery; inspect artifacts, not just workflow colors.

## Rollback / next safe action
Revert this bounded change on the feature branch only if required; do not reset history or main. Restoring the prior verifier also restores known defects and therefore cannot justify qualification. Retain RED fixtures. Refresh live head/main/claims, require applicable checks, inspect report inputs/JUnit/media manifests, then persist exact results to #162/#158/#93/#39. Do not merge, release, deploy, spend provider credits or infer creative quality from the technical fixture.
