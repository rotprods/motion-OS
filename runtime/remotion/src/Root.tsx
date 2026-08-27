import React from 'react';
import {Composition} from 'remotion';
import spec from './runtimeSpec.json';
import {MotionOSRuntime} from './MotionOSRuntime';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MotionOSRuntime"
      component={MotionOSRuntime}
      durationInFrames={spec.project.duration_frames}
      fps={spec.project.fps}
      width={spec.project.width}
      height={spec.project.height}
    />
  );
};
