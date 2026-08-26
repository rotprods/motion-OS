# Phase 05 Runtime Superwave Evidence — 2026-08-26

Authority: runtime smoke evidence from active execution environment. This is not a substitute for GitHub CI or authoritative creative QA.

## Capability probe
Observed:
- Node: `v22.16.0`
- npm: `10.9.2`
- FFmpeg: available at `/usr/bin/ffmpeg`
- Chromium: available at `/usr/bin/chromium`
- Remotion CLI: unavailable
- HyperFrames CLI: unavailable
- npm offline cache contained no Remotion/HyperFrames package entries

Conclusion:
- Remotion and HyperFrames compilers can be tested structurally, but physical renderer execution is currently capability-blocked in this runtime.
- No network install is assumed or silently performed.
- E23/E24 remain open until a runtime with those dependencies is available.

## Physical FFmpeg compositor smoke
Created:
1. 2-second 320×180 black H.264 base at 30 fps.
2. 1-second 120×60 overlay source.
3. Composite with overlay active from 0.5s to 1.5s.
4. Encoded final H.264 master and probed it with FFprobe.

FFprobe result:
```json
{
  "width": 320,
  "height": 180,
  "r_frame_rate": "30/1",
  "nb_frames": "60",
  "duration": "2.000000"
}
```

Gate result:
- exact duration: PASS
- exact fps: PASS
- exact frame count: PASS
- expected resolution: PASS
- physical FFmpeg composition: PASS

Interpretation:
E26 has real evidence for the FFmpeg assembly substrate. The full checkpoint still remains open until at least two distinct Studio Engine renderer artifacts are produced, composed, provenance-linked and regression-checked.

## Structural renderer/compiler smoke
Executed in isolated Python harness:
- new Remotion graph compiler syntax: PASS
- EditingGraph one-scene/three-layer → Remotion spec: PASS
- new HyperFrames graph compiler syntax: PASS
- same graph → HyperFrames spec: PASS
- Lottie supported shape subset validation: PASS
- renderer assignment SUBJECT→Remotion, TYPOGRAPHY→HyperFrames: PASS
- deterministic composite-plan construction: PASS

Authority boundary:
These results prove compiler/contract behavior, not visual renderer output quality.
