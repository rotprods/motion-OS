# HANDOFF.md — MOTION.OS

## Start here
1. Use GitHub `rotprods/motion-OS` → `main`.
2. Read `AGENTS.md`.
3. Read `GOAL.md`.
4. Read `STATE.md`.
5. Read `TASKS.md`.
6. Inspect `state/project_state.json`, `state/github_sync.json`, `state/drive_sync.json`.
7. Inspect `registry/artifact_registry.json`.
8. Read the latest Drive reconciliation attestation.
9. Continue the highest-priority open product P0.

## Canonical infrastructure
GitHub `main` now contains the canonical software/control plane. PR #10 passed:
- CI Python 3.11
- CI Python 3.12
- Repo Health
- Security Baseline

Heavy/generated media does not belong in Git and remains in Drive.

## Drive
Root: `MOTION.OS_CANONICAL`
Folder ID: `1RsHZbf6yGE92L3wnbyxriCMx47HeBAOB`

Reconciliation vault: `07_RECONCILIATION`
Folder ID: `1xItu4yHyi-D4bRCt_W0XrIcbxzZEkHMb`

Latest GitHub canonical attestation:
`GITHUB_CANONICAL_ATTESTATION.json`
Drive ID: `1wrX8eE7lBBzitYmB2VcHmIcb-bXJyWz6`

## Creative truth
RC05 is working master. RC06 is still a candidate until formal promote/rollback evidence is completed.

## Do not
- redesign the persistence architecture;
- call fixture/contact-sheet QA authoritative full-video QA;
- claim HyperFrames/Remotion verified until a real runtime render exists;
- move heavy rendered media into Git.
