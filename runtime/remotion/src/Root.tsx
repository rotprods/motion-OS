import React from 'react';
import {Composition} from 'remotion';
import spec from './runtimeSpec.json';
import {MotionOSRuntime} from './MotionOSRuntime';
import {S14AudioVisualTexto,S14Overlay,S14_SPEC} from './golden_s14';

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
        id={S14_SPEC.compositionId}
        component={S14AudioVisualTexto}
        durationInFrames={S14_SPEC.source.frameCount}
        fps={S14_SPEC.source.fps}
        width={S14_SPEC.source.width}
        height={S14_SPEC.source.height}
      />
      <Composition
        id={S14_SPEC.overlayCompositionId}
        component={S14Overlay}
        durationInFrames={S14_SPEC.source.frameCount}
        fps={S14_SPEC.source.fps}
        width={S14_SPEC.source.width}
        height={S14_SPEC.source.height}
      />
    </>
  );
};
