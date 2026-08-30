import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {measuredS04Layout, type MeasuredBox} from './measuredTrack';
import {S04_SPEC} from './s04Spec';

type TextRole = 'setup' | 'hero' | 'tail';

type VisibleBoundsCalibration = {
  xOffset: number;
  baselineOffsetY: number;
  textLengthDelta: number;
  fontSizeMultiplier: number;
};

const VISIBLE_BOUNDS_CALIBRATION: Record<TextRole, VisibleBoundsCalibration> = {
  // Exact-head source-bound measurement at 85c45c6 found that SVG font metrics,
  // not the measured screen-space boxes, were creating the dominant P1 mismatch.
  // These values correct renderer glyph bounds; they are not claims about the
  // unknown original font metrics or After Effects source project.
  setup: {
    xOffset: -1.2,
    baselineOffsetY: -6.8,
    textLengthDelta: 2.1,
    fontSizeMultiplier: 1.32,
  },
  hero: {
    xOffset: -1.6,
    baselineOffsetY: -0.8,
    textLengthDelta: 2.7,
    fontSizeMultiplier: 1.11,
  },
  tail: {
    xOffset: -1.8,
    baselineOffsetY: -7.5,
    textLengthDelta: 2.8,
    fontSizeMultiplier: 1.066,
  },
};

type MeasuredTextProps = {
  role: TextRole;
  box: MeasuredBox | null;
  text: string;
  fill: string;
  family: string;
  weight: number;
  shadow: boolean;
};

const MeasuredText: React.FC<MeasuredTextProps> = ({
  role,
  box,
  text,
  fill,
  family,
  weight,
  shadow,
}) => {
  if (!box) return null;
  const calibration = VISIBLE_BOUNDS_CALIBRATION[role];
  return (
    <text
      x={box.x + calibration.xOffset}
      y={box.y + box.height + calibration.baselineOffsetY}
      fill={fill}
      fillOpacity={box.opacity}
      fontFamily={family}
      fontSize={box.height * calibration.fontSizeMultiplier}
      fontWeight={weight}
      lengthAdjust="spacingAndGlyphs"
      textLength={Math.max(1, box.width + calibration.textLengthDelta)}
      style={{
        filter: shadow ? 'drop-shadow(0px 3px 2px rgba(0,0,0,.72))' : undefined,
        paintOrder: 'stroke fill',
      }}
    >
      {text}
    </text>
  );
};

export const MeasuredCaptionSystem: React.FC = () => {
  const frame = useCurrentFrame();
  const layout = measuredS04Layout(frame);
  const setupText = frame < S04_SPEC.local.setup.phraseSwap ? 'que' : S04_SPEC.caption.setup;

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <svg
        viewBox={`0 0 ${S04_SPEC.source.width} ${S04_SPEC.source.height}`}
        width={S04_SPEC.source.width}
        height={S04_SPEC.source.height}
        style={{position: 'absolute', inset: 0, overflow: 'visible'}}
      >
        <MeasuredText
          role="setup"
          box={layout.setup}
          text={setupText}
          fill={S04_SPEC.caption.setupColor}
          family="Arial, Helvetica, sans-serif"
          weight={800}
          shadow
        />
        <MeasuredText
          role="hero"
          box={layout.hero}
          text={S04_SPEC.caption.hero}
          fill={S04_SPEC.caption.heroColor}
          family="Impact, Arial Narrow, Arial, sans-serif"
          weight={900}
          shadow
        />
        <MeasuredText
          role="tail"
          box={layout.tail}
          text={S04_SPEC.caption.tail}
          fill={S04_SPEC.caption.tailColor}
          family="Arial, Helvetica, sans-serif"
          weight={800}
          shadow
        />
      </svg>
    </AbsoluteFill>
  );
};

export const S04_VISIBLE_BOUNDS_CALIBRATION = VISIBLE_BOUNDS_CALIBRATION;
