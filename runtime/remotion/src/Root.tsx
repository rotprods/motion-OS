import React from 'react';
import {Composition} from 'remotion';
import spec from './runtimeSpec.json';
import {MotionOSRuntime} from './MotionOSRuntime';
import {S11Overlay, S11_SPEC, S11UiList} from './golden_s11';

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
        id={S11_SPEC.compositionId}
        component={S11UiList}
        durationInFrames={S11_SPEC.source.frameCount}
        fps={S11_SPEC.source.fps}
        width={S11_SPEC.source.width}
        height={S11_SPEC.source.height}
      />
      <Composition
        id={S11_SPEC.overlayCompositionId}
        component={S11Overlay}
        durationInFrames={S11_SPEC.source.frameCount}
        fps={S11_SPEC.source.fps}
        width={S11_SPEC.source.width}
        height={S11_SPEC.source.height}
      />
    </>
  );
};
