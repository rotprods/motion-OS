# PR141 — Golden Product E2E technical qualification

Status: `TECHNICAL_PRODUCT_E2E_VERIFIED_BRANCH_NOT_PROMOTED`
Date: 2026-09-09
Tracker: #138
Project Completion Engine: #93
Promotion barrier: #48 OPEN

## Exact lineage

- base PR136: `8946f34ede9ab96a16f330d5a8304111dc668037`
- PR141 code/evidence-producing head: `5327e3872fe12e6b82a5bd8815074a29573c21cf`
- synthetic PR merge candidate tested by GitHub Actions: `96762d2f331ac5b219986b612005213f74de40dd`
- main remains outside this authority; no merge/promotion is claimed here.

## Independent gates

### Merge Safe

- workflow run: `34351881211`
- conclusion: `SUCCESS`
- Python 3.12 local contract: PASS
- Python 3.11 compatibility: PASS
- dependency security: PASS
- physical analysis: PASS
- physical Remotion: PASS
- MERGE_SAFE aggregate: PASS
- full Python suite observed in the clean runner: `716 passed, 1 skipped, 5 inherited warnings`
- immutable agent-event validation: PASS (`18` events at that synthetic candidate)

### Product E2E

- workflow run: `34351881220`
- conclusion: `SUCCESS`
- product run-manifest regression contract: PASS (`15` tests)
- two frozen Node installs: PASS
- authorized Phase06 → Studio → physical Remotion path: PASS
- exact physical run sealing: PASS
- evidence upload: PASS

## Canonical technical run

- run id: `RUN_0C1C6574F41DC3E0AADD`
- manifest status: `TECHNICAL_PRODUCT_E2E_VERIFIED`
- manifest Git authority: synthetic merge `96762d2f331ac5b219986b612005213f74de40dd`
- content id: `fixture-studio-runtime-001`
- provenance root: `PRV_3DEC5F1936B015BB624A56043681D8CC`
- replay fingerprint: `MNF_2C9EF5B709F84193446EE9C1`
- semantic beats: `B00_HOOK`, `B01_MECHANISM`, `B02_PROOF`, `B03_PAYOFF`
- execution hash: `a506e77a4ca9783006620d3e21e313bb9e00f054d0973d72ca90b989e1b5ee83`
- bundle hash: `f83d8f1be574e368fa3df04b8f89ff29589763fe7c9580f3ffd7baa03f9b0564`
- graph hash: `3c82b9598b020d4adab8d70edf6a74798bd20f5c4d008e53a5044c246e0b3827`
- asset manifest hash: `4ae6e5c5ed94232e3497683c9a565b482ff16bc7824931402348bf9e73b62dd0`
- render manifest hash: `085e1bcd0927219b23494ea8953faa26b1a4f5584bc28619310819a128945317`
- runtime-spec canonical hash: `31baf2cd99166da0de05077770c7f80fbbe5e96a7c4e981675b8c7b9a20ca40d`
- runtime-spec file SHA256: `175abd483b99c9fed9b7e18e8324c47186311856e94e99c80ef0e4674e2f1e94`
- runtime-evidence hash: `c5cf56b6dbe2427a6f19876e5e3c7f08a2d49c5c3de0f328b1952ccf31683bf0`
- recovery manifest hash: `550d87ed2d0c0261342bfccb0f70a0e4627263ae45c5dd7db220c681fc1fc1e2`
- product manifest hash: `0df5fa0e59e38565fdbf437c93b582855967b1e988608429bbc1340008067273`
- `recovery_ready=true`

## Physical artifact

- MP4 SHA256: `ef2c2b4f50a555157021865f07a67364cf01d65991282b905a6af1bfc1c93d2a`
- bytes: `371706`
- counted video frames: `90`
- frame rate: `30/1`
- raster: `640x360`
- expected visual duration: `3.0s`
- observed container duration: approximately `3.050667s`
- audio stream: present
- technical runtime gate: PASS
- runtime evidence errors: `[]`

## Independent artifact verification

GitHub Actions artifact:

- artifact id: `10104084387`
- artifact name: `product-e2e-evidence`
- ZIP SHA256: `5e2418992244a50e4d208aa7cffcce473f6bfcd99ba69dc93368f2089e56f32c`
- ZIP bytes: `260720`

The downloaded package was independently inspected after CI. The following content hashes were recomputed and matched their declared values exactly:

- product manifest canonical self-hash: PASS
- runtime-evidence canonical hash: PASS
- Studio bundle canonical hash: PASS
- MP4 SHA256/bytes: PASS
- ffprobe frame/raster/fps evidence: PASS

## Durable Drive mirror + round-trip

Canonical backup folder: `08_INFRA_BACKUPS_EXPORTS`

- folder id: `1t8Y34fkpBos2KIbIQgz9gWkj2-o3hcoX`
- Drive file id: `1iN1TWGqHPQg0Yoen3X58aJc1GRC8LPFh`
- file: `MOTION_OS_PR141_PRODUCT_E2E_RUN_0C1C6574F41DC3E0AADD.zip`
- uploaded bytes: `260720`

The Drive object was downloaded again after upload. Round-trip verification:

- original GitHub artifact ZIP SHA256: `5e2418992244a50e4d208aa7cffcce473f6bfcd99ba69dc93368f2089e56f32c`
- Drive-downloaded ZIP SHA256: `5e2418992244a50e4d208aa7cffcce473f6bfcd99ba69dc93368f2089e56f32c`
- byte length on both sides: `260720`
- result: `DRIVE_ROUNDTRIP_EXACT = true`

## Negative/adversarial contract covered

Permanent tests reject:

- graph tampering with stale graph hash;
- asset-manifest tampering;
- incomplete renderer assignments even when the render manifest is rehashed;
- physical runtime FAIL evidence;
- physical artifact hash mismatch;
- runtime-spec file hash mismatch;
- runtime scene lineage mismatch;
- runtime transition lineage mismatch;
- runtime-spec document drift;
- malformed Git SHA;
- persisted product manifest tampering;
- attempted self-promotion to creative/provider/production/PROJECT_DONE authority;
- a non-executable operator finalizer path.

Two pre-qualification Product E2E runs correctly failed and were repaired: first a direct-CLI import-path bug, then a brittle test oracle that asserted argparse wrapping rather than CLI semantics. Neither failure is being hidden or counted as product authority.

## Authority boundary

This evidence proves a technical combined-tree path:

`sealed Phase06 package → authorized Studio transition → graph/renderer/runtimeSpec lineage → physical Remotion MP4 → technical QA → content-addressed product run manifest → zero-context recovery manifest → durable artifact mirror`

It DOES NOT prove:

- creative quality qualification;
- real full-video semantic-provider qualification;
- production deployment;
- native branch protection;
- Issue #48 exit;
- merge or release authorization;
- `PROJECT_DONE`.

Explicit run fields remain:

- `production_authority=false`
- `creative_authority=false`
- `provider_authority=false`
- `project_done=false`

## Next safe frontier

1. verify this evidence-only commit with Merge Safe on its exact final PR head;
2. persist HANDOFF/checkpoint to Bus #39, #93 and #138;
3. qualify offline replay/reconstruction from the durable package as a separate conceptual unit;
4. converge non-overlapping runtime pixel-sensitivity work before building the final promotion candidate;
5. keep #48 and native-main protection as hard promotion gates.
