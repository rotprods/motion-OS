# Remotion semantic relations — handoff

Status: VERIFIED BRANCH CANDIDATE / NOT PROMOTED

Base PR #135: `5cc07346b2e4199eccaef3543e52e2ef18b08668`
Implementation: `9ae6cd8220981907b3d83d199a49438ce4727f98`
Merge Safe: `34158290757` SUCCESS; 701 passed / 1 skipped / 5 inherited warnings.

## Fixed

The Remotion graph compiler now consumes the canonical EditingGraph relationships it previously ignored:
- `Scene --USES--> CameraRig`
- `Scene --ENTERS_VIA--> Transition`
- `Scene --EXITS_VIA--> Transition`

Historical `CONTAINS` camera/transition forms remain compatibility fallback. Ambiguous or wrong-kind relations fail closed.

The physical runtime evidence v3 binds the exact runtimeSpec SHA and records scene/transition lineage. The authorized Studio fixture now reaches physical Remotion with transition types `cut, match_geometry_or_existing_element, match_geometry_or_existing_element, match_geometry_or_existing_element`; encoded output is 90 frames at 30 fps, 640x360, SHA256 `ef2c2b4f50a555157021865f07a67364cf01d65991282b905a6af1bfc1c93d2a`.

## Next

`runtime/remotion/src/MotionOSRuntime.tsx` still ignores the `layers` carried by runtimeSpec. Close that separately with a physical differential test: mutate Studio typography input, render a second candidate and prove the affected raw frame changes. Do not call the route content-faithful before that evidence exists.

Keep #48 OPEN, main untouched and #68 inactive.
