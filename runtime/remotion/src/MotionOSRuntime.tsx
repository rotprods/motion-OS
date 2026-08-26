import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import rawSpec from './runtimeSpec.json';

type RuntimeEvent = {at_frame?: number; id?: string; action?: string};
type RuntimeScene = {
  id: string;
  from: number;
  durationInFrames: number;
  camera: {motion: string; [key: string]: unknown};
  depth: Record<string, unknown>;
  transition: {type: string; [key: string]: unknown};
  events: RuntimeEvent[];
};
type RuntimeSpec = {
  project: {fps: number; width: number; height: number; duration_frames: number};
  zOrder: string[];
  scenes: RuntimeScene[];
};

const spec = rawSpec as unknown as RuntimeSpec;

const hashScene = (value: string) => {
  let h = 2166136261;
  for (let i = 0; i < value.length; i++) {
    h ^= value.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
};

const scenePalette = (id: string) => {
  const h = hashScene(id);
  const hue = h % 360;
  return {
    background: `hsl(${hue} 18% 10%)`,
    accent: `hsl(${(hue + 155) % 360} 78% 62%)`,
    soft: `hsl(${hue} 24% 88%)`,
  };
};

const Scene: React.FC<{scene: RuntimeScene; index: number}> = ({scene, index}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const palette = scenePalette(scene.id);
  const progress = interpolate(
    frame,
    [0, Math.max(1, scene.durationInFrames - 1)],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const enter = interpolate(frame, [0, Math.min(10, scene.durationInFrames - 1)], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const eventPulse = scene.events.length
    ? Math.max(
        ...scene.events.map((event) => {
          const local = Number(event.at_frame ?? scene.from) - scene.from;
          return interpolate(frame, [local - 2, local, local + 5], [0, 1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
        }),
      )
    : 0;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: palette.background,
        color: palette.soft,
        fontFamily: 'Arial, Helvetica, sans-serif',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: 34,
          top: 28,
          fontSize: 12,
          letterSpacing: 2.4,
          opacity: 0.65,
        }}
      >
        MOTION.OS / RUNTIME PROOF / {String(index + 1).padStart(2, '0')}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 34,
          right: 34,
          top: 70,
          height: 1,
          backgroundColor: palette.soft,
          opacity: 0.18,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 46,
          top: 130,
          width: 250,
          opacity: enter,
          translate: `${interpolate(enter, [0, 1], [-18, 0])}px 0px`,
        }}
      >
        <div style={{fontSize: 62, fontWeight: 650, lineHeight: 0.92}}>{scene.id}</div>
        <div style={{marginTop: 18, fontSize: 13, opacity: 0.72}}>
          {scene.transition.type.toUpperCase()} · {scene.camera.motion.toUpperCase()}
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          width: 176,
          height: 176,
          borderRadius: 999,
          right: 62,
          top: 90,
          border: `2px solid ${palette.accent}`,
          scale: interpolate(progress, [0, 0.5, 1], [0.72, 1.02, 0.88]),
          rotate: `${interpolate(progress, [0, 1], [0, 120])}deg`,
          opacity: 0.85,
        }}
      >
        <div
          style={{
            position: 'absolute',
            width: 20,
            height: 20,
            borderRadius: 999,
            left: 76,
            top: -11,
            backgroundColor: palette.accent,
            boxShadow: `0 0 ${18 + eventPulse * 35}px ${palette.accent}`,
          }}
        />
      </div>
      <div
        style={{
          position: 'absolute',
          left: 34,
          right: 34,
          bottom: 34,
          height: 5,
          borderRadius: 999,
          backgroundColor: 'rgba(255,255,255,0.12)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${Math.max(0.5, progress * 100)}%`,
            height: '100%',
            borderRadius: 999,
            backgroundColor: palette.accent,
          }}
        />
      </div>
      <div
        style={{
          position: 'absolute',
          right: 36,
          bottom: 52,
          fontSize: 10,
          letterSpacing: 1.4,
          opacity: 0.55,
        }}
      >
        FRAME {scene.from + frame} / {(spec.project.duration_frames - 1).toString()} · {fps} FPS
      </div>
    </AbsoluteFill>
  );
};

export const MotionOSRuntime: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: '#070707'}}>
      {spec.scenes.map((scene, index) => (
        <Sequence
          key={scene.id}
          from={scene.from}
          durationInFrames={scene.durationInFrames}
          layout="absolute-fill"
        >
          <Scene scene={scene} index={index} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
