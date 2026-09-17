## Mission
Recover a real P0 from Reel production: a visually valid export reached the operator with audio effectively lost. Reconcile the still-unmerged PR #61 single-master-audio mux contract onto current `main`, then add a second fail-closed gate over the **final encoded bytes** so a correct FFmpeg command cannot masquerade as a successful master.

## Live base
- base: `main@d4e628a1aef0cd382c3c2f1ea327a8ff70c41bd9`
- Issue #48: OPEN
- donor PR #61 exact head: `91bc6c8c121d84cad3a6e6a170b8c8cbe890f2ec`

## Delivered
- ports #61's explicit single-master audio mapping onto current main;
- renderer-local audio is never mapped into the final master;
- master audio is reset to t=0, padded if short and trimmed to the exact project duration;
- silent projects explicitly use `-an`;
- plan records `audio_integrity_policy=post_render_master_audio_required` whenever a master audio path exists;
- new post-render verifier probes the final file and requires exactly one audio stream, expected sample rate, channel count and duration;
- optional declared speech windows are physically decoded to PCM and must exceed a configurable silence floor, preventing a present-but-silent AAC stream from qualifying.

## Regression family
Missing final audio stream, duplicate/multiple audio streams, renderer-local audio leakage, sample-rate/channel drift, duration drift, present-but-silent speech windows, unsafe path/shell interpolation.

## Verification executed
Isolated exact changed-file mirror:
- `py_compile`: PASS
- `pytest`: **9 passed**

Full repository, clean-runner MERGE_SAFE and independent review: **NOT RUN / NOT CLAIMED**.

## Authority
`IMPLEMENTED_SCOPED_TESTS_PASS_NOT_PROMOTED`.

Keep DRAFT. No merge while Issue #48 remains open or until current-head full repository qualification + code/security/QA review is complete. Do not infer release or production authority from the successful real Reel V3 export; the media incident is the regression source, not repository CI authority.
