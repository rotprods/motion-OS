# Reel V3 audio regression — 2026-09-17

## Real incident
A Reel edit path produced an apparently successful visual deliverable while the user-observed audio was lost. This is a P0 delivery defect: a video master that requires speech must never qualify from visual checks alone.

## Root gap in current `main`
`src/renderers/assembly.py` declares `audio_policy = single_master_audio_graph`, but current `main` only builds the video filter graph and contains no executable single-master audio mapping contract. Historical PR #61 already identified and repaired that first half, but remained unmerged on an older base.

A second gap remained even in the donor contract: a correct FFmpeg command is not evidence that the final encoded bytes still contain usable speech.

## V2 repair contract
This branch therefore:

1. ports the bounded #61 single-master-audio mux invariants onto current `main`;
2. makes post-render audio integrity an explicit plan policy when a master audio path exists;
3. probes the final encoded artifact, not the intended command;
4. requires exactly one audio stream under the single-master contract;
5. binds sample rate, channel count and audio duration to the expected master;
6. optionally decodes declared speech windows and rejects silent output even when an audio stream exists.

## Regression family
- missing final audio stream;
- multiple audio streams under the single-master contract;
- renderer-local audio accidentally surviving assembly;
- wrong sample rate / channel count;
- audio shorter or longer than the final timeline beyond tolerance;
- present-but-silent AAC stream at declared speech windows;
- unsafe shell interpolation remains forbidden by argv construction.

## Authority
Scoped exact changed-file mirror:
- `py_compile`: PASS;
- `pytest`: 9 PASS.

Full repository / Merge Safe: NOT RUN in this session.

Issue #48 remains OPEN. This branch is an implementation/recovery candidate only; no merge or promotion authority is claimed.
