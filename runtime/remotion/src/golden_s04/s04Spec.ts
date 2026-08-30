export const S04_SPEC = {
  schemaVersion: 'motion-os.golden-scene/v1',
  sceneId: 'S04_CIENTIFICAMENTE',
  compositionId: 'GoldenS04Cientificamente',
  source: {
    sha256: '9b3076cb542e358386942a0fb6b160f1345564d4326738f9a340e2b5b38e199d',
    startFrame: 145,
    endFrameExclusive: 216,
    fps: 30,
    width: 512,
    height: 1108,
  },
  local: {
    frameCount: 71,
    setup: {start: 0, phraseSwap: 5},
    hero: {start: 11, overshoot: 15, settle: 20},
    tail: {start: 38, impact: 43, settle: 50},
    phoneBridge: {start: 60, impact: 67, end: 71},
    sfxImpact: 15,
  },
  caption: {
    setup: 'que sea',
    hero: 'CIENTÍFICAMENTE',
    tail: 'imposible',
    setupColor: '#F3F1EC',
    heroColor: '#C90D18',
    tailColor: '#F3F1EC',
    fontAuthority: 'FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN',
  },
  authority: {
    sourceTiming: 'MEASURED_DECODE',
    motionCurves: 'EVIDENCE_BOUND_INFERENCE',
    fontIdentity: 'UNKNOWN',
    proceduralPlate: 'STRUCTURAL_FIXTURE_ONLY',
    exactImageSequence: 'EXTERNAL_DRIVE_ASSET_REQUIRED',
    sourceFidelity: 'BLOCKED_UNTIL_9D_DIFF',
  },
} as const;

export type S04PlateMode = 'procedural' | 'image-sequence';

export type S04CientificamenteProps = {
  plateMode: S04PlateMode;
  plateFolder: string;
  plateIncludesEditorialReframe: boolean;
  enableProceduralImpact: boolean;
  showDebugOverlay: boolean;
};

export const S04_DEFAULT_PROPS: S04CientificamenteProps = {
  plateMode: 'procedural',
  plateFolder: 'golden_s04/clean_frames',
  plateIncludesEditorialReframe: false,
  enableProceduralImpact: true,
  showDebugOverlay: false,
};
