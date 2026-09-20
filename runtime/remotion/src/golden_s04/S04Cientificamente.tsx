import React, {useMemo} from 'react';
import {Audio} from '@remotion/media';
import {
  AbsoluteFill,
  Easing,
  Sequence,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {
  S04_DEFAULT_PROPS,
  S04_SPEC,
  type S04CientificamenteProps,
} from './s04Spec';
import {makeProceduralImpactDataUri} from './proceduralImpact';

const clamp = {
  extrapolateLeft: 'clamp' as const,
  extrapolateRight: 'clamp' as const,
};

const frameName = (frame: number) => `${String(frame + 1).padStart(4, '0')}.png`;

const ProceduralTalkingHead: React.FC<{applyEditorialReframe: boolean}> = ({
  applyEditorialReframe,
}) => {
  const frame = useCurrentFrame();
  const cameraScale = applyEditorialReframe
    ? interpolate(frame, [0, 45, 65, 70], [1, 1.095, 1.07, 1.06], {
        ...clamp,
        easing: Easing.bezier(0.4, 0, 0.2, 1),
      })
    : 1;
  const cameraX = applyEditorialReframe
    ? interpolate(frame, [0, 45, 70], [0, -4, -2], {...clamp})
    : 0;
  const cameraY = applyEditorialReframe
    ? interpolate(frame, [0, 45, 70], [0, -17, -12], {...clamp})
    : 0;
  const phoneEnter = interpolate(frame, [60, 67], [0, 1], {
    ...clamp,
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#050505', overflow: 'hidden'}}>
      <div
        style={{
          position: 'absolute',
          inset: 20,
          borderRadius: 21,
          overflow: 'hidden',
          background:
            'radial-gradient(circle at 13% 6%, rgba(255,50,23,.92) 0 8%, transparent 28%), radial-gradient(circle at 78% 38%, rgba(236,36,18,.72), transparent 27%), linear-gradient(135deg,#3e0a08 0%,#15110f 54%,#2c0807 100%)',
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: -42,
            scale: cameraScale,
            translate: `${cameraX}px ${cameraY}px`,
            transformOrigin: '50% 42%',
          }}
        >
          <div
            style={{
              position: 'absolute',
              left: 71,
              top: 122,
              width: 319,
              height: 350,
              borderRadius: '46% 46% 42% 42%',
              background:
                'radial-gradient(circle at 46% 36%,#b46b50 0 7%,transparent 8%), radial-gradient(circle at 66% 36%,#a95f49 0 7%,transparent 8%), linear-gradient(148deg,#522a23 0%,#a95d47 48%,#4a211d 100%)',
              boxShadow: '0 20px 65px rgba(0,0,0,.68)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              left: 66,
              top: 82,
              width: 335,
              height: 215,
              borderRadius: '48% 50% 30% 36%',
              background:
                'radial-gradient(circle at 55% 82%,rgba(100,58,43,.8),transparent 30%), linear-gradient(165deg,#090909,#21120f 60%,#080808)',
              rotate: '-2deg',
            }}
          />
          <div
            style={{
              position: 'absolute',
              left: 34,
              top: 421,
              width: 445,
              height: 645,
              borderRadius: '45% 45% 4% 4%',
              background: 'linear-gradient(152deg,#0b0b0b,#171717 55%,#080808)',
              boxShadow: '0 -12px 22px rgba(0,0,0,.38)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              left: 30,
              top: 773,
              width: 150,
              height: 210,
              borderRadius: 74,
              rotate: '-15deg',
              background: 'linear-gradient(140deg,#8e4a3b,#3b1c19)',
              opacity: 0.96,
            }}
          />
          <div
            style={{
              position: 'absolute',
              right: 24,
              bottom: 33,
              width: 212,
              height: 259,
              borderRadius: 42,
              rotate: '-8deg',
              translate: `${interpolate(phoneEnter, [0, 1], [92, 0])}px ${interpolate(
                phoneEnter,
                [0, 1],
                [105, 0],
              )}px`,
              opacity: phoneEnter,
              background: 'linear-gradient(145deg,#143c5a,#071c31)',
              border: '3px solid rgba(42,88,121,.75)',
              boxShadow: '0 24px 42px rgba(0,0,0,.65)',
            }}
          />
        </div>
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 0,
            height: 48,
            background: 'linear-gradient(#050505,rgba(5,5,5,.86))',
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: 8,
            left: 33,
            color: '#f6f6f6',
            fontFamily: 'Arial, sans-serif',
            fontWeight: 700,
            fontSize: 17,
          }}
        >
          17:32
        </div>
        <div
          style={{
            position: 'absolute',
            top: 6,
            left: 122,
            width: 232,
            height: 38,
            borderRadius: 24,
            backgroundColor: '#050505',
            border: '1px solid rgba(110,28,25,.64)',
          }}
        >
          <div
            style={{
              position: 'absolute',
              left: 18,
              top: 11,
              width: 15,
              height: 15,
              borderRadius: 99,
              backgroundColor: '#dc2d26',
            }}
          />
        </div>
        <div
          style={{
            position: 'absolute',
            right: 36,
            top: 13,
            width: 72,
            height: 14,
            opacity: 0.88,
            background:
              'linear-gradient(90deg,transparent 0 5%,#fff 5% 10%,transparent 10% 22%,#fff 22% 30%,transparent 30% 44%,#fff 44% 56%,transparent 56% 68%,#fff 68% 100%)',
          }}
        />
      </div>
      <div
        style={{
          position: 'absolute',
          inset: 20,
          borderRadius: 21,
          pointerEvents: 'none',
          opacity: 0.055,
          backgroundImage:
            'repeating-linear-gradient(0deg,rgba(255,255,255,.35) 0 1px,transparent 1px 3px), repeating-linear-gradient(90deg,rgba(255,255,255,.18) 0 1px,transparent 1px 4px)',
          backgroundPosition: `${frame % 4}px ${(frame * 3) % 5}px`,
          mixBlendMode: 'soft-light',
        }}
      />
    </AbsoluteFill>
  );
};

const Plate: React.FC<Pick<S04CientificamenteProps, 'plateMode' | 'plateFolder' | 'plateIncludesEditorialReframe'>> = ({
  plateMode,
  plateFolder,
  plateIncludesEditorialReframe,
}) => {
  const frame = useCurrentFrame();
  if (plateMode === 'image-sequence') {
    return (
      <AbsoluteFill>
        <Img
          src={staticFile(`${plateFolder}/${frameName(frame)}`)}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>
    );
  }
  return <ProceduralTalkingHead applyEditorialReframe={!plateIncludesEditorialReframe} />;
};

const CaptionSystem: React.FC = () => {
  const frame = useCurrentFrame();
  const setupText = frame < S04_SPEC.local.setup.phraseSwap ? 'que' : 'que sea';

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: 56,
          top: 579,
          color: S04_SPEC.caption.setupColor,
          fontFamily: 'Arial, Helvetica, sans-serif',
          fontSize: 28,
          lineHeight: 1,
          fontWeight: 800,
          letterSpacing: -0.8,
          opacity: interpolate(frame, [0, 3], [0.72, 1], {
            ...clamp,
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: `0px ${interpolate(frame, [0, 3], [4, 0], {
            ...clamp,
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          })}px`,
          textShadow: '0 2px 7px rgba(0,0,0,.72)',
        }}
      >
        {setupText}
      </div>

      <div
        style={{
          position: 'absolute',
          left: 56,
          top: 608,
          color: S04_SPEC.caption.heroColor,
          fontFamily: '"Arial Narrow", "Roboto Condensed", Arial, sans-serif',
          fontStretch: 'condensed',
          fontSize: 53,
          lineHeight: 0.92,
          fontWeight: 950,
          letterSpacing: -2.7,
          whiteSpace: 'nowrap',
          transformOrigin: 'left top',
          opacity: interpolate(frame, [11, 15], [0, 1], {
            ...clamp,
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          scale:
            frame <= 15
              ? interpolate(frame, [11, 15], [0.84, 1.12], {
                  ...clamp,
                  easing: Easing.bezier(0.16, 1, 0.3, 1),
                })
              : interpolate(frame, [15, 20], [1.12, 1], {
                  ...clamp,
                  easing: Easing.bezier(0.4, 0, 0.2, 1),
                }),
          translate: `0px ${interpolate(frame, [11, 15, 20], [10, -2, 0], {
            ...clamp,
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          })}px`,
          filter: `blur(${interpolate(frame, [11, 14, 15], [2.2, 0.4, 0], {
            ...clamp,
          })}px) drop-shadow(0 4px 3px rgba(26,0,0,.62))`,
        }}
      >
        {S04_SPEC.caption.hero}
      </div>

      <div
        style={{
          position: 'absolute',
          left: 329,
          top: 679,
          color: S04_SPEC.caption.tailColor,
          fontFamily: 'Arial, Helvetica, sans-serif',
          fontSize: 27,
          lineHeight: 1,
          fontWeight: 800,
          letterSpacing: -0.7,
          opacity: interpolate(frame, [38, 43], [0, 1], {
            ...clamp,
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: `${interpolate(frame, [38, 43], [12, 0], {
            ...clamp,
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          })}px 0px`,
          textShadow: '0 2px 7px rgba(0,0,0,.72)',
        }}
      >
        {S04_SPEC.caption.tail}
      </div>
    </AbsoluteFill>
  );
};

export const S04Cientificamente: React.FC<Partial<S04CientificamenteProps>> = (rawProps) => {
  const props = {...S04_DEFAULT_PROPS, ...rawProps};
  const frame = useCurrentFrame();
  const {fps, width, height, durationInFrames} = useVideoConfig();
  const impact = useMemo(() => makeProceduralImpactDataUri(), []);

  return (
    <AbsoluteFill style={{backgroundColor: '#050505', overflow: 'hidden'}}>
      <Plate
        plateMode={props.plateMode}
        plateFolder={props.plateFolder}
        plateIncludesEditorialReframe={props.plateIncludesEditorialReframe}
      />
      <CaptionSystem />
      {props.enableProceduralImpact ? (
        <Sequence from={S04_SPEC.local.sfxImpact} layout="none">
          <Audio src={impact} volume={0.72} />
        </Sequence>
      ) : null}
      {props.showDebugOverlay ? (
        <div
          style={{
            position: 'absolute',
            right: 8,
            bottom: 8,
            padding: '5px 7px',
            borderRadius: 6,
            backgroundColor: 'rgba(0,0,0,.72)',
            color: 'white',
            fontFamily: 'monospace',
            fontSize: 10,
          }}
        >
          S04 local {frame}/{durationInFrames - 1} · source {S04_SPEC.source.startFrame + frame} · {width}×{height} · {fps}fps
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
