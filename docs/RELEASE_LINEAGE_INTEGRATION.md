# Release lineage integration (PR132 successor)

## Scope and lineage
This candidate integrates the #102 sentinel and #104 release-state/current-main contract into PR132. Their evaluators are adapted to require explicit lifecycle and repository identity; their network reads share one fixed-origin bounded transport. Existing #132 atomic receipt writing is reused. No second verifier, registry or release authority is introduced.

## Commands (from repository root)
```bash
python -m scripts.main_lineage_sentinel --repository rotprods/motion-OS --sha <commit> --json-out .artifacts/main-lineage.json
python -m scripts.release_authority_guard --repository rotprods/motion-OS --release-sha <commit> --state state/project_state.json --json-out .artifacts/release-lineage.json
```
The token comes only from GITHUB_TOKEN. No token argument or credential persistence. Module invocation is intentional: these scripts share repository modules and do not require an editable installation.

## Contract
The release preflight requires an explicit RELEASED state with an empty, typed p0_blockers array, exact working-file/Git-blob identity at the checked-out release commit, stable live main, and an exact merged PR targeting this repository/main. It rechecks local state after metadata reads. Matching an associated but different merge commit is insufficient.

A successful result is RELEASE_LINEAGE_VERIFIED, not the donor's broader RELEASE_AUTHORIZED label. Every receipt says promotion_authorized=false. Callers must still obtain explicit #39/#48 release authorization, native protection, exact-candidate CI, semantic/creative acceptance and deployment approval. This is a necessary sub-gate, never a standalone publishing permission. No publishing command is present.

## Failure behavior
Both commands invalidate an earlier receipt with RUNNING and reuse the atomic writer from local_verify. CLI0 means this scoped check passed, CLI2 means a validly assessed denial, CLI3 means malformed/unavailable evidence or receipt failure. RUNNING is never approval. Invalid release-state data currently uses CLI3. Fixed errors do not echo arbitrary metadata, tokens or exception messages.

GitHub requests use HTTPS to the fixed API origin only, reject redirects, reject incomplete pagination rather than silently taking its first page, cap response bytes and JSON nesting, reject duplicate keys/nonfinite numbers and require finite socket timeouts. No environment proxy inheritance. Repository moves, proxies or larger association sets need explicit adaptation; automatic trust expansion is forbidden.

## Limits and execution status
The predicate is not a whole-history audit: it verifies the exact tip's PR lineage, not that every ancestor was introduced through a verified PR. It does not certify media hashes, P1 absence, all dependencies, build evidence, account settings or product quality. The final metadata read is an observation, not a transactional lock against a later main advance. The trusted-checkout/single-writer assumptions and disk/SIGKILL limitations of #132 receipts remain.

The new main-push sentinel and tag guard are read-only workflow definitions, not executions on main. Eventual-consistency/API failure blocks this check; there is no retry-until-green. CI tests run the module entrypoints, actual Git/state operations, and injected network boundaries. Network fixtures are not live API evidence. Local full clone was DNS-blocked; the repository-complete proof must come from the exact clean runner.

Continue from this isolated candidate. Do not merge under open #48, edit donor branches, switch on #68 or mistake CI completion for frontend/backend/product completion.
