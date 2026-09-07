# CI convergence — isolated integration candidate

## Scope and lineage

Base: PR130 `9a7b7435d6b884785c41a7e21212581f0dd80c1d`.
This candidate combines PR130's strict final verdict with the exact npm lock from
PR95, PR58's immutable Coordination Actions, and PR56's shared-authority impact
coverage. Donor branches are not rewritten or merged wholesale. This is not a
production release; Issue48 and native-protection gates remain independent.

## Execution

1. Local hook and cloud classifier call the same `change_impact.py --git-base`
   transport. Git refs resolve to commits before diff. NUL-delimited paths preserve
   path boundaries; rename detection is disabled to include old and new paths.
2. Unknown history, malformed paths, unrecognized execution surfaces and shared
   contracts force full checks. Known extraction/Remotion paths retain selective
   routing; plain README/documentation changes remain cheap.
3. Every workflow checkout disables persistent credentials. Remote Actions are
   pinned; workflow default permissions remain read-only. No privileged PR trigger
   or production self-hosted runner is introduced.
4. The existing required Remotion job invokes `verify_node_lock.py`: two `npm ci`
   installs, exact lock/manifest byte stability and a dependency-tree receipt.
   Approved locks are never deleted/re-resolved by verification. Updating a lock
   is a separately reviewed operation. The same verifier serves manual rendering.
5. The quick job verifies actionlint 1.7.12's upstream archive SHA256 before
   extraction/execution. It validates the repository's workflow files. Download,
   digest or lint failure blocks quick and therefore MERGE_SAFE.
6. The existing final gate still consumes actual `needs` results and classifier
   outputs. It has not been replaced by a second verdict implementation.

## Local checks

```bash
python -m pytest -q tests/test_change_impact.py tests/test_merge_safe_gate.py tests/test_ci_convergence.py
python scripts/change_impact.py --git-base origin/main
python scripts/verify_node_lock.py --json-out .artifacts/node-lock-verification.json
python scripts/local_verify.py merge
```

The node verifier requires a full checkout with the imported lock and registry
access. The isolated authoring mirror proves only its negative contracts, not a
real installation. Clean-runner proofs must identify their exact tested SHA.

## Risks and remaining work

This does not freeze Python transitive packages, exact Node minor, OS image or
media binaries, audit all npm vulnerabilities, qualify a provider, authorize main
or close CP1. Unintegrated branch-only workflows require the same inspection when
imported. Existing `local_verify.py` warning-only scanner behavior, the #103 local
main-push guard and #104 release-lineage guard remain separate integration work.
The test role is same-agent adversarial review, not independent approval.

## Rollback and continuation

Revert only the candidate commits on an owned branch; never reset donors or main.
Keep PR130's fail-closed gate. Re-read live main, Issue39, Issue48 and PR topology
before further mutation. Use `evidence/ci_convergence_20260907/inventory.json` for
scoped lineage, not current project authority. After clean-runner proof, persist
its IDs, tested SHA, report hashes, residuals and a new native handoff event.
