import React from 'react';
import {AbsoluteFill} from 'remotion';
import {MeasuredCaptionSystem} from './MeasuredCaptionSystem';

/**
 * Transparent visual-only overlay for local composition over the private clean plate.
 * Audio remains in the full composition and source media never enters public CI.
 */
export const S04Overlay: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      <MeasuredCaptionSystem />
    </AbsoluteFill>
  );
};
