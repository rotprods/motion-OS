import React from 'react';
import {Composition} from 'remotion';
import spec from './runtimeSpec.json';
import {MotionOSRuntime} from './MotionOSRuntime';
import {
  S04Cientificamente,
  S04Overlay,
  S04_DEFAULT_PROPS,
  S04_SPEC,
} from './golden_s04';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MotionOSRuntime"
        component={MotionOSRuntime}
        durationInFrames={spec.project.duration_frames}
        fps={spec.project.fps}
        width={spec.project.width}
        height={spec.project.height}
      />
      <Composition
        id="GoldenS04Cientificamente"
        component={S04Cientificamente}
        durationInFrames={S04_SPEC.local.frameCount}
        fps={S04_SPEC.source.fps}
        width={S04_SPEC.source.width}
        height={S04_SPEC.source.height}
        defaultProps={S04_DEFAULT_PROPS}
      />
      <Composition
        id="GoldenS04Overlay"
        component={S04Overlay}
        durationInFrames={S04_SPEC.local.frameCount}
        fps={S04_SPEC.source.fps}
        width={S04_SPEC.source.width}
        height={S04_SPEC.source.height}
      />
    </>
  );
};
