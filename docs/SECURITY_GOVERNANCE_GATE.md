# MOTION.OS — Security + Governance Gate

Status: T8 hardening contract under Issue #48.

## Purpose
Separate three different claims that must never be conflated:

1. repository code is statically free of known high-risk patterns;
2. dependencies were audited on the exact candidate;
3. GitHub itself enforces the merge policy on `main`.

A PASS in one layer does not grant authority in another.

## Repo-native security gate

Run locally:

```bash
python scripts/security_gauntlet.py --json-out .artifacts/security-gauntlet.json
python scripts/local_verify.py security --json-out .artifacts/security-verify.json
```

`security_gauntlet.py` fails closed on:
- Python `eval`, `exec`, `os.system`;
- `pickle.load(s)` and unsafe `yaml.load`;
- subprocess execution with `shell=True`;
- GitHub Actions using mutable refs instead of 40-character commit SHAs;
- credential-like OpenAI/GitHub/AWS/private-key material in repository text.

Dynamic `shell=` is emitted as MEDIUM review-required evidence, not silently ignored.

The local `security` and `merge` profiles require `pip-audit` to exist. Missing dependency-audit tooling is no longer a WARN that can masquerade as a full security PASS.

## CI routing invariant
Changes to the security gauntlet, its tests, governance policy, or this gate document force the full MERGE_SAFE classifier so the security and compatibility jobs cannot be skipped merely because the changed path was previously unknown.

## GitHub governance target
`config/security_governance_policy.json` defines the desired target for `main`:
- protected branch / active ruleset;
- PR-only change path;
- no force pushes;
- no branch deletion;
- required checks include `MERGE_SAFE` and `Coordination Contracts`.

This policy file is declarative. It is NOT evidence that GitHub admin controls are actually enabled.

## Live audit — 2026-08-28
Observed through the GitHub API immediately before this workstream:

```text
main SHA: a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d
repository rulesets: []
main protected: false
required status checks at branch protection: none
```

Therefore T8.3 remains `BLOCKED_ADMIN_CONFIGURATION` until live GitHub returns an enforcing ruleset/branch protection matching the target policy. The connector used by this agent can read repository governance but does not expose an authorized admin mutation for creating rulesets or branch protection, so this branch deliberately does not pretend to configure it.

## Promotion invariant
Immediately before any merge/promotion:

```text
READ latest Event Fabric watermark
+ READ live main SHA
+ READ live rulesets/branch protection
+ VERIFY exact candidate checks
+ VERIFY no unresolved security blocker
```

If live governance is absent, the system must report the gap. It must not promote a repository-level test into a claim of platform enforcement.

## Current authority
- Static security gauntlet: IMPLEMENTED on this branch; requires exact-head CI before VERIFIED_BRANCH.
- Dependency audit: existing scheduled/merge CI capability; local security profile is hardened to fail on missing `pip-audit`.
- GitHub main protection: NOT IMPLEMENTED externally as of the live audit above.
