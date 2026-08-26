# Phase 05 — Physical Multi-render / Repair / Recovery Evidence — 2026-08-26

Authority: physical runtime evidence from current execution environment. It does not claim Remotion or HyperFrames execution because those CLIs are unavailable in this runtime.

## Runtime capabilities observed
- Node `v22.16.0`
- npm `10.9.2`
- FFmpeg available
- FFprobe available
- Chromium available
- Python Playwright available
- Remotion CLI unavailable
- HyperFrames CLI unavailable
- npm network package resolution unavailable during the run
- no cached Remotion/HyperFrames package found

## Physical `chromium_web` render
A deterministic HTML/SVG/CSS scene was evaluated at sampled frame states using one headless Chromium process through Playwright, expanded deterministically to a 30 fps frame sequence, and encoded with FFmpeg.

Artifact:
- renderer: `chromium_web`
- resolution: 640×360
- fps: 30/1
- frames: 60
- duration: 2.000000 s
- SHA256: `db6825bc75cf4ccf199eda31bfd83ad37010e73751a0a9d3aceae39bf7d9d178`

This proves a physical web-render backend in the active runtime. It is NOT evidence that HyperFrames executed.

## Physical second renderer artifact
A separate `video_plate` artifact was produced through the FFmpeg/native media backend:
- duration: 2 s
- resolution: 640×360
- SHA256: `03ee0b7f904ee0f39c791969fc8de29d3f19b047d4997f340efd69f424ca4546`

## Physical multi-render assembly
`chromium_web` + `video_plate` were composited through FFmpeg on a shared global clock.

Final master probe:
```json
{
  "width": 640,
  "height": 360,
  "r_frame_rate": "30/1",
  "nb_frames": "60",
  "duration": "2.000000"
}
```

Master SHA256:
`37b62e596fbabbf6373360dd24a911ee652f5f31331942781eaa44ef5594ef66`

Result: physical multi-backend assembly substrate PASS. E26 is now physically demonstrated for `chromium_web + video_plate`; full Remotion×HyperFrames×Lottie benchmark remains pending.

## Localized defect + repair proof
A deliberate high-salience competing-primary defect was introduced ONLY in frames 25–37.

Defect fixture SHA256:
`ea1e48e822ff22b9255ca66e0b8c84aae5041b8b555e278e10ef831d1b1cea24`

Repair strategy:
- affected frames: 25–37
- protected frames: all frames outside that interval
- repair: replace only affected frame states from known-good evidence
- no full timeline mutation permitted

Frame-level comparison result:
```json
{
  "defect_frames": [25,26,27,28,29,30,31,32,33,34,35,36,37],
  "repair_interval_frames": [25,37],
  "protected_frame_count": 47,
  "protected_mismatches": [],
  "repaired_interval_mismatches": [],
  "protected_region_exact": true,
  "repair_exact": true
}
```

Repaired master:
- 640×360
- 30 fps
- 60 frames
- 2.000000 s
- SHA256 `8b861425fb34979243b79ab3417a497e584d03edd80fff3c13651d5182a52e01`

Interpretation: E28 now has a physical localized-repair proof with byte-identical PNG protected regions. The next authority upgrade is running the same contract through a real Studio Engine renderer and graph-generated defect/candidate path.

## Zero-context local recovery rehearsal
A recovery manifest was generated containing artifact roles, paths, SHA256, dimensions/timing and recovery instruction. A fresh rehearsal consumed only that manifest, verified every artifact hash, selected the canonical `repaired_master`, and reconstructed the output without re-encoding.

Recovered artifact SHA256:
`8b861425fb34979243b79ab3417a497e584d03edd80fff3c13651d5182a52e01`

Result: byte-identical to the canonical repaired master.

Interpretation: local manifest-based recovery PASS. E29 remains open until this proof includes canonical Git SHA + Drive artifact IDs and succeeds from a zero-context external workspace.

## Remaining authority boundaries
- E23 Remotion: compiler-ready only; physical CLI/render missing.
- E24 HyperFrames: compiler-ready only; physical CLI/render missing.
- E25 Lottie: compiler/subset-ready; actual lottie-web/player roundtrip missing.
- E26: physical multi-backend assembly PASS for Chromium web + native video plate; target Remotion/HyperFrames/Lottie mix pending.
- E27: graph critic core implemented; authoritative temporal multimodal critic pending.
- E28: physical localized repair demonstrated; Studio-graph-driven renderer repair still pending.
- E29: local recovery rehearsal demonstrated; Git+Drive zero-context recovery pending.
