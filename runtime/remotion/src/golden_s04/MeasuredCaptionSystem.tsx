import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {measuredS04Layout, type MeasuredBox} from './measuredTrack';
import {S04_SPEC} from './s04Spec';

type MeasuredTextProps = {
  box: MeasuredBox | null;
  text: string;
  fill: string;
  family: string;
  weight: number;
  shadow: boolean;
};

const MeasuredText: React.FC<MeasuredTextProps> = ({
  box,
  text,
  fill,
  family,
  weight,
  shadow,
}) => {
  if (!box) return null;
  return (
    <text
      x={box.x}
      y={box.y + box.height}
      fill={fill}
      fillOpacity={box.opacity}
      fontFamily={family}
      fontSize={box.height * 1.32}
      fontWeight={weight}
      lengthAdjust="spacingAndGlyphs"
      textLength={box.width}
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
          box={layout.setup}
          text={setupText}
          fill={S04_SPEC.caption.setupColor}
          family="Arial, Helvetica, sans-serif"
          weight={800}
          shadow
        />
        <MeasuredText
          box={layout.hero}
          text={S04_SPEC.caption.hero}
          fill={S04_SPEC.caption.heroColor}
          family="Impact, Arial Narrow, Arial, sans-serif"
          weight={900}
          shadow
        />
        <MeasuredText
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
