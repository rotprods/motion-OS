# PR145 — Integrated Product + Pixel + Recovery qualification

Status: `INTEGRATED_PRODUCT_PIXEL_RECOVERY_VERIFIED_BRANCH_NOT_PROMOTED`
Date: 2026-09-09
Tracker: #144 · PCE: #93 · promotion barrier: #48 OPEN

## Exact integration
- integration commit: `0499fa9bba3a36514b4ff2b9eafc87378278321a`
- tree: `66c8b5636163f5a6d705b882ad81aa9df8b8d0fb`
- parent 1 / PR143: `2d3bf35f11dc77bec4fb953c13ff2af43a5200e7`
- parent 2 / PR137: `4c1aa1c4813318778558abb06769881c13199b3b`
- common verified base / PR136: `8946f34ede9ab96a16f330d5a8304111dc668037`
- synthetic merge tested by all combined gates: `a320694dd9abc3451a3b09d12401809f057fc18c`

PR137 donor blobs are preserved exactly, including `MotionOSRuntime.tsx=543414f4f56031474f2a1bd9e18af8867352bfa6`, `local_verify.py=900299626ac6b868d888041181dfdb5839ae14c9`, sensitivity verifier `8a846d984b28092556efa97844937c51cdb5e40e` and test `bdc2fa759bf0f19df20fbc5c6bbb715b6d8221d9`.

## Combined-tree gates
- Merge Safe `34355003912` / #530: **SUCCESS**
- Product E2E `34355003940` / #8: **SUCCESS**
- Offline Replay `34355003966` / #3: **SUCCESS**
- Python 3.12/3.11, repo-health, event validation, dependency security, physical analysis and physical Remotion: PASS
- full suite: `738 passed, 1 skipped, 5 inherited warnings`

## Shared physical/product evidence
- run id: `RUN_77BB7458918C653AFF1B`
- product manifest hash: `a1e52b1f1ba8752c52500ef4e1ecd86cda9ff5714d131ded8d92007594cdeaf9`
- runtime evidence hash: `2766a22c930c61d3646895642833838905b778a44df3ec55a9de0ce97304baf3`
- Studio bundle hash: `f83d8f1be574e368fa3df04b8f89ff29589763fe7c9580f3ffd7baa03f9b0564`
- recovery-ready: `true`
- offline replay: `OFFLINE_REPLAY_VERIFIED`
- offline replay report hash: `fe918a754a211f072fdebb7d62cbeea128a8121955362fa7c42efe0107a5b379`
- MP4 SHA256: `e221eea3d9a66d20ba3c5d8cbf89a7e864fbe32f9319791cabb9c595d8826552`
- MP4: 370181 bytes · 90 frames · 30 fps · 640x360 · audio present
- runtimeSpec file SHA256: `175abd483b99c9fed9b7e18e8324c47186311856e94e99c80ef0e4674e2f1e94`

Independent post-CI recomputation matched the product-manifest self-hash, replay-report self-hash, runtime-evidence canonical hash and Studio-bundle canonical hash exactly.

## Studio input → rendered pixels
The same integrated runtime evidence reports:
- `input_sensitivity.gate=PASS`
- scene `scene:B00_HOOK`, layer `layer:B00_HOOK:typography`, frame 11
- changed RGB bytes: `191614 / 691200` = `0.2772193287037037`
- baseline frame SHA256 `8a593990899114f7ba05d4fedd85096c98361a28dd065bbf96e702712d8a5b11`
- variant frame SHA256 `130de208c043284a5c36462617714a1e5c12895f46506c64fd3901613f16d7c6`
- variant MP4 SHA256 `87fa177781cefcd6c20218e83758b4c586ddb21ddc504806c852990b0929d221`
- runtimeSpec restored byte-exact: `true`

Thus the same tree proves Studio input→pixel causality, technical Product E2E and destruction/offline physical recovery.

## Durable integrated evidence
Combined package: `MOTION_OS_PR145_INTEGRATED_PRODUCT_PIXEL_RECOVERY.zip`
- bytes: `771777`
- SHA256: `64144d56b9d82b8b8d27bf4f1af6cc1645f4ef0a4f092d75e679495dcb9ddd68`
- contains the original Product E2E (`a88c1da9...ff40f`), Offline Replay (`5ea48bbf...2411e`) and Merge Safe Remotion (`756ac146...99140`) evidence ZIPs plus `INTEGRATION_EVIDENCE.json`.

Drive mirror:
- folder `08_INFRA_BACKUPS_EXPORTS` / `1t8Y34fkpBos2KIbIQgz9gWkj2-o3hcoX`
- file id `1YvDQXRXWSX4sszCHZuD6osWlWXoIRDkx`
- downloaded again after upload: 771777 bytes, same SHA256 `64144d56b9d82b8b8d27bf4f1af6cc1645f4ef0a4f092d75e679495dcb9ddd68`
- `DRIVE_ROUNDTRIP_EXACT=true`

## Authority boundary
This is bounded technical branch authority only. It does **not** prove creative quality, real full-video semantic-provider qualification, provenance-bound real asset pixels, distinct transition animation semantics, production deployment, native main protection, #48 exit, merge/release authority or PROJECT_DONE.

Explicit: `production_authority=false`, `creative_authority=false`, `provider_authority=false`, `project_done=false`.

Next: final-head revalidation → close #144 if green → re-score #48 and attack remaining non-external P0/P1 gates before any promotion train.