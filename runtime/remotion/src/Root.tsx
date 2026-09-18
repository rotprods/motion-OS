import React from 'react';
import {Composition} from 'remotion';
import spec from './runtimeSpec.json';
import {MotionOSRuntime} from './MotionOSRuntime';
import {S16FactorX,S16Overlay,S16_SPEC} from './golden_s16';

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
        id={S16_SPEC.compositionId}
        component={S16FactorX}
        durationInFrames={S16_SPEC.source.frameCount}
        fps={S16_SPEC.source.fps}
        width={S16_SPEC.source.width}
        height={S16_SPEC.source.height}
      />
      <Composition
        id={S16_SPEC.overlayCompositionId}
        component={S16Overlay}
        durationInFrames={S16_SPEC.source.frameCount}
        fps={S16_SPEC.source.fps}
        width={S16_SPEC.source.width}
        height={S16_SPEC.source.height}
      />
    </>
  );
};
