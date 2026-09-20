# PR143 — Offline Product E2E destruction/replay qualification

Status: `OFFLINE_REPLAY_VERIFIED_BRANCH_NOT_PROMOTED`
Date: 2026-09-09
Tracker: #142
Parent capability: PR #141 / Issue #138
Project Completion Engine: #93
Promotion barrier: #48 OPEN

## Exact lineage

- base PR141: `9d3c5becc2ef420515fb5a3bdd50125c208c1fea`
- PR143 evidence-producing head: `6b55d4f685d1c47dcbd6d181e47616f90812d1b2`
- synthetic merge candidate tested by all initial PR143 workflows: `d3da7adb353d147040004da13b630c3685950ce0`

## Independent gates on the implementation head

- Merge Safe `34353315223`: `SUCCESS`
- Product E2E `34353315162`: `SUCCESS`
- Offline Replay `34353315455`: `SUCCESS`

Offline Replay job: `Destroy workspace evidence → restore ZIP → verify physical replay` = `SUCCESS`.

## Adversarial/recovery contract

The dedicated replay regression suite completed `14 passed` and covers:

- logical replay of an exact persisted product run;
- `../` path traversal rejection;
- absolute archive path rejection;
- symlink member rejection;
- duplicate member rejection;
- file-count and uncompressed-size limits;
- required-member absence;
- MP4 substitution;
- Studio bundle tampering;
- persisted product-manifest tampering;
- final replay-report hash integrity;
- fresh physical-probe identity mismatch;
- logical-only replay authority separation;
- direct CLI execution.

## Destruction drill

The clean runner produced one authorized technical Phase06 → Studio → Remotion run, then sealed a product run manifest.

It created an evidence ZIP containing only these five required files:

1. `.artifacts/product-run-manifest.json`
2. `runtime/remotion/studio_execution_bundle.json`
3. `runtime/remotion/render_evidence.local.json`
4. `runtime/remotion/src/runtimeSpec.json`
5. `runtime/remotion/out/runtime-local.mp4`

The workflow then deleted all five producer copies outside the ZIP and explicitly asserted that they no longer existed.

Only after that destruction step did `scripts/studio_replay_verify.py` extract the ZIP into a fresh temporary directory, reconstruct the product-run manifest, validate recovery linkage and run a fresh physical ffprobe verification against the restored MP4/runtimeSpec.

Result: `OFFLINE_REPLAY_VERIFIED`.

## Replay identities

- replay run id: `RUN_BCA01EC9882C9D659C49`
- replay Git authority: synthetic merge `d3da7adb353d147040004da13b630c3685950ce0`
- product manifest hash: `b9501fb4a1563d28c196fd352567c6389c3b3519785c98e109661230633b4d2f`
- bundle hash: `f83d8f1be574e368fa3df04b8f89ff29589763fe7c9580f3ffd7baa03f9b0564`
- runtime evidence hash: `c5cf56b6dbe2427a6f19876e5e3c7f08a2d49c5c3de0f328b1952ccf31683bf0`
- runtimeSpec file SHA256: `175abd483b99c9fed9b7e18e8324c47186311856e94e99c80ef0e4674e2f1e94`
- physical MP4 SHA256: `ef2c2b4f50a555157021865f07a67364cf01d65991282b905a6af1bfc1c93d2a`
- physical MP4 bytes: `371706`
- recovery manifest hash: `c7fcae0a45cf1587f21c4597f4d2e38715bd5f62cdb5da9da7354c376d48a1ab`
- `recovery_ready=true`
- replay report hash: `45a12c797e27d5332f692643d74c8a0cd7bc46591c5bf8b4308dbeeec96fb2d1`
- replay `physical_authority=true` only for this technical archive replay
- `production_authority=false`
- `creative_authority=false`
- `provider_authority=false`
- `project_done=false`

## Restored physical probe

Independent post-workflow inspection of the downloaded artifact reconfirmed:

- video stream: 640x360
- frame rate: `30/1`
- counted video frames: `90`
- audio stream: present
- container duration: `3.050667s`
- bytes: `371706`
- MP4 SHA256: `ef2c2b4f50a555157021865f07a67364cf01d65991282b905a6af1bfc1c93d2a`
- runtimeSpec SHA256: `175abd483b99c9fed9b7e18e8324c47186311856e94e99c80ef0e4674e2f1e94`

The replay report self-hash was independently recomputed after download and matched exactly.

## Evidence archives

Archive that survived producer-evidence destruction inside the workflow:

- `offline-product-evidence.zip`
- bytes: `258375`
- SHA256: `c8b44806fc4d25ecd31714375e41b02359dbef95b9a21ebb0792d18a0bf9c2d0`

GitHub Actions outer evidence artifact:

- artifact id: `10104674541`
- artifact name: `offline-replay-evidence`
- bytes: `260484`
- SHA256: `185d32fda188fee3162aeefa217c17bf7f58977ca0ab7dda33a78e8759f80f5d`

The outer package contains:

- `offline-replay-node-lock.json`
- `offline-replay-remotion-verify.json`
- `offline-product-evidence.zip`
- `offline-replay-report.json`

## Durable Drive mirror + round-trip

Canonical backup folder: `08_INFRA_BACKUPS_EXPORTS`

- parent folder id: `1t8Y34fkpBos2KIbIQgz9gWkj2-o3hcoX`
- Drive file id: `196T9aopKKl9tE5Iy35UuKmhi7-9hBpQ9`
- file: `MOTION_OS_PR143_OFFLINE_REPLAY_RUN_BCA01EC9882C9D659C49.zip`
- bytes: `260484`

The uploaded Drive file was downloaded again after persistence:

- original GitHub artifact SHA256: `185d32fda188fee3162aeefa217c17bf7f58977ca0ab7dda33a78e8759f80f5d`
- Drive-downloaded SHA256: `185d32fda188fee3162aeefa217c17bf7f58977ca0ab7dda33a78e8759f80f5d`
- bytes on both sides: `260484`
- `DRIVE_ROUNDTRIP_EXACT=true`

## Authority boundary

This qualification proves that the bounded technical product evidence can survive loss of its producer workspace and be reconstructed/physically reverified from a content-addressed archive.

It does NOT prove:

- creative-quality qualification;
- real full-video semantic-provider qualification;
- deployment/production operation;
- native main protection;
- Issue #48 exit;
- merge/release authority;
- PROJECT_DONE.

## Next safe frontier

1. revalidate this evidence-only commit on its exact final head;
2. persist Bus #39 / #93 / #142 handoff and close scoped P8.1 if final gates stay green;
3. reconcile the concurrent non-overlapping rendered-pixel sensitivity candidate;
4. build a single integration/promotion candidate and execute the remaining #48 security/governance/whole-product gates;
5. keep real provider/creative qualification and native-main protection as explicit blockers rather than fabricating PASS states.
