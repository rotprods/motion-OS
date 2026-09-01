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
    // Historical summary used local 15. Source-bound onset evidence places the
    // emphasis near local 9; this sound's generated transient peaks ~1 frame
    // after Sequence start, so local 8 is the measured renderer calibration.
    sfxImpact: 8,
  },
  caption: {
    setup: 'que sea',
    hero: 'CIENTÍFICAMENTE',
    tail: 'imposible',
    setupColor: '#F3F1EC',
    heroColor: '#C90D18',
    tailColor: '#F3F1EC',
    fontAuthority: 'FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN',
    visibleBoundsAuthority: 'MEASURED_SOURCE_VISIBLE_BBOX_WITH_RENDERER_CALIBRATION',
  },
  structure: {
    captionParentHypothesis: {
      value: 'SHARED_SCREEN_SPACE_PARENT_AFTER_HERO_ENTRY',
      authority: 'EVIDENCE_BOUND_INFERENCE',
      setupHeroWidthScaleCorrelation: 0.9975202500257605,
      setupTailWidthScaleCorrelation: 0.9939963827123907,
      heroTailWidthScaleCorrelation: 0.9968121946478035,
      caveat: 'does not prove original After Effects parenting or precomp topology',
    },
  },
  authority: {
    sourceTiming: 'MEASURED_DECODE',
    motionCurves: 'EVIDENCE_BOUND_INFERENCE',
    fontIdentity: 'UNKNOWN',
    proceduralPlate: 'STRUCTURAL_FIXTURE_ONLY',
    exactImageSequence: 'EXTERNAL_DRIVE_ASSET_REQUIRED',
    sourceFidelity: 'BLOCKED_UNTIL_9D_DIFF_REPAIR_PASS',
    audioOnsetTiming: 'MEASURED_SOURCE_BOUND',
    sfxIdentity: 'INFERRED_FROM_MIXED_AUDIO',
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
