export const S14_SPEC={
  schemaVersion:'motion-os.golden-scene/v2',
  sceneId:'S14_AUDIO_VISUAL_TEXTO',
  compositionId:'GoldenS14AudioVisualTexto',
  overlayCompositionId:'GoldenS14Overlay',
  source:{sha256:'9b3076cb542e358386942a0fb6b160f1345564d4326738f9a340e2b5b38e199d',startFrame:561,endFrameExclusive:655,frameCount:94,fps:30,width:512,height:1108},
  state:{audio:{start:0},visual:{transitionStart:11,activate:17,settle:20},texto:{transitionStart:47,activate:54,settle:60}},
  colors:{bg0:'#780000',bg1:'#B20B0B',grid:'rgba(235,225,215,.34)',heading:'#D6D1C9',card:'#8B8582',red:'#B71318',yellow:'#D6C61A'},
  authority:{sourceTiming:'MEASURED_DECODE',visibleGeometry:'MEASURED_VISIBLE_KEYFRAME_PROJECTION_V2',headingFont:'FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN',annotationPath:'MEASURED_VISIBLE_BBOX_PROXY_EXACT_VECTOR_PATH_UNKNOWN',nestedMedia:'SOURCE_LOCK_SLOT',audioTransientTiming:'MEASURED_MIXED_TRACK_TRANSIENT_PROXY',sfxIdentity:'UNKNOWN_FROM_MIXED_MASTER',sourceFidelity:'BLOCKED_UNTIL_SOURCE_BOUND_DIFF'},
  sourceTransientProxyFrames:[10.05,14.40,16.80,45.75,50.25,56.25,62.85],
  transientLocalFrames:[10,14,17,46,50,56,63],
  rendererCalibration:{
    // Physical AAC/H.264 render at head ebe8eedf showed the generated transient
    // peak ~1 frame after Sequence start. This is an adapter calibration only:
    // canonical source event frames above are NOT shifted.
    syntheticHitLeadFrames:1,
    authority:'MEASURED_RENDERER_PEAK_LATENCY_CALIBRATION',
    baselineArtifactId:9781244633,
    baselineMaxPeakErrorFrames:1.5425170068027256,
  },
} as const;
export type S14Props={showDebug:boolean;enableSyntheticHits:boolean};
export const S14_DEFAULT_PROPS:S14Props={showDebug:false,enableSyntheticHits:true};
