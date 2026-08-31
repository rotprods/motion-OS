export const S14_SPEC={
  schemaVersion:'motion-os.golden-scene/v1',
  sceneId:'S14_AUDIO_VISUAL_TEXTO',
  compositionId:'GoldenS14AudioVisualTexto',
  overlayCompositionId:'GoldenS14Overlay',
  source:{sha256:'9b3076cb542e358386942a0fb6b160f1345564d4326738f9a340e2b5b38e199d',startFrame:561,endFrameExclusive:655,frameCount:94,fps:30,width:512,height:1108},
  state:{audio:{start:0},visual:{transitionStart:11,activate:17,settle:20},texto:{transitionStart:47,activate:54,settle:60}},
  colors:{bg0:'#780000',bg1:'#B20B0B',grid:'rgba(235,225,215,.34)',heading:'#D6D1C9',card:'#8B8582',red:'#B71318',yellow:'#D6C61A'},
  authority:{sourceTiming:'MEASURED_DECODE',visibleGeometry:'MEASURED_VISIBLE_KEYFRAME_PROJECTION',headingFont:'FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN',annotationPath:'EVIDENCE_BOUND_INFERENCE',nestedMedia:'SOURCE_LOCK_SLOT',audioTransientTiming:'MEASURED_MIXED_TRACK_PROXY',sfxIdentity:'UNKNOWN_FROM_MIXED_MASTER',sourceFidelity:'BLOCKED_UNTIL_SOURCE_BOUND_DIFF'},
  transientLocalFrames:[10,14,17,46,50,56,63],
} as const;
export type S14Props={showDebug:boolean;enableSyntheticHits:boolean};
export const S14_DEFAULT_PROPS:S14Props={showDebug:false,enableSyntheticHits:true};
