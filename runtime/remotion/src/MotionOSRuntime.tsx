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
type RuntimeLayer = {
  id: string;
  layerClass: string;
  z: number;
  semanticRole?: string | null;
  attentionRole?: string | null;
  assetRef?: string | null;
  data?: Record<string, unknown>;
};
type RuntimeScene = {
  id: string;
  from: number;
  durationInFrames: number;
  camera?: {motion?: string; [key: string]: unknown} | null;
  depth: Record<string, unknown>;
  transition?: {type?: string; [key: string]: unknown} | null;
  events: RuntimeEvent[];
  layers?: RuntimeLayer[];
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
    panel: `hsl(${hue} 16% 15%)`,
  };
};

const asText = (value: unknown): string | null => {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
};

const textForLayer = (layer: RuntimeLayer | undefined): string | null => {
  return asText(layer?.data?.text);
};

const cuesForLayer = (layer: RuntimeLayer | undefined): string[] => {
  const value = layer?.data?.edit_cues;
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === 'string' && Boolean(item.trim()));
};

const compactRef = (value: string | null | undefined) => {
  if (!value) return 'NO ASSET REF';
  return value.length <= 48 ? value : `${value.slice(0, 45)}…`;
};

const Scene: React.FC<{scene: RuntimeScene; index: number}> = ({scene, index}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const palette = scenePalette(scene.id);
  const layers = [...(scene.layers ?? [])].sort((a, b) => a.z - b.z || a.id.localeCompare(b.id));
  const typography = layers.find((layer) => layer.layerClass === 'TYPOGRAPHY');
  const primary =
    layers.find((layer) => layer.attentionRole === 'primary') ??
    layers.find((layer) => layer.layerClass === 'PRIMARY_UI' || layer.layerClass === 'SUBJECT');
  const headline = textForLayer(typography) ?? scene.id;
  const primaryCues = cuesForLayer(primary);
  const transitionType = scene.transition?.type ?? 'cut';
  const cameraMotion = scene.camera?.motion ?? 'static';

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
          inset: 0,
          opacity: 0.13,
          backgroundImage:
            'linear-gradient(rgba(255,255,255,.13) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.13) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }}
      />
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
        MOTION.OS / STUDIO RUNTIME / {String(index + 1).padStart(2, '0')}
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
        data-layer-id={typography?.id}
        data-layer-class={typography?.layerClass}
        style={{
          position: 'absolute',
          left: 46,
          top: 112,
          width: 330,
          opacity: enter,
          translate: `${interpolate(enter, [0, 1], [-18, 0])}px 0px`,
        }}
      >
        <div
          style={{
            fontSize: headline.length > 34 ? 34 : headline.length > 22 ? 44 : 58,
            fontWeight: 680,
            lineHeight: 0.96,
            letterSpacing: -1.8,
          }}
        >
          {headline}
        </div>
        <div style={{marginTop: 18, fontSize: 12, letterSpacing: 1.1, opacity: 0.7}}>
          {transitionType.toUpperCase()} · {cameraMotion.toUpperCase()}
        </div>
      </div>

      <div
        data-layer-id={primary?.id}
        data-layer-class={primary?.layerClass}
        style={{
          position: 'absolute',
          right: 44,
          top: 98,
          width: 190,
          minHeight: 156,
          padding: '18px 18px 16px',
          border: `1px solid ${palette.accent}`,
          borderRadius: 18,
          backgroundColor: palette.panel,
          boxShadow: `0 18px 60px rgba(0,0,0,.22)`,
          opacity: 0.82 + eventPulse * 0.18,
          transform: `scale(${interpolate(progress, [0, 0.5, 1], [0.96, 1, 0.98])})`,
        }}
      >
        <div style={{fontSize: 9, letterSpacing: 1.7, opacity: 0.55}}>PRIMARY STUDIO LAYER</div>
        <div style={{fontSize: 20, fontWeight: 700, marginTop: 10}}>{primary?.layerClass ?? 'UNSET'}</div>
        <div style={{fontSize: 11, marginTop: 5, opacity: 0.68}}>{primary?.semanticRole ?? 'primary'}</div>
        <div style={{fontSize: 9, marginTop: 14, opacity: 0.5, wordBreak: 'break-word'}}>
          {compactRef(primary?.assetRef)}
        </div>
        {primaryCues.slice(0, 2).map((cue) => (
          <div key={cue} style={{fontSize: 9, marginTop: 5, opacity: 0.58}}>
            • {cue}
          </div>
        ))}
      </div>

      <div
        style={{
          position: 'absolute',
          left: 44,
          right: 44,
          bottom: 70,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 6,
        }}
      >
        {layers.map((layer) => (
          <div
            key={layer.id}
            data-layer-id={layer.id}
            style={{
              fontSize: 8,
              letterSpacing: 0.7,
              padding: '5px 8px',
              borderRadius: 999,
              border: '1px solid rgba(255,255,255,.14)',
              backgroundColor: 'rgba(255,255,255,.04)',
              opacity: layer.attentionRole === 'primary' ? 0.9 : 0.52,
            }}
          >
            {layer.layerClass} / Z{layer.z}
          </div>
        ))}
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
