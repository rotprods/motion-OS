export const S16_SPEC={
 schemaVersion:'motion-os.golden-scene/v1',
 sceneId:'S16_FACTOR_X',
 compositionId:'GoldenS16FactorX',
 overlayCompositionId:'GoldenS16Overlay',
 source:{sha256:'9b3076cb542e358386942a0fb6b160f1345564d4326738f9a340e2b5b38e199d',startFrame:727,endFrameExclusive:819,frameCount:92,fps:30,width:512,height:1108,contentBottom:1014},
 anchors:{column:{start:2,impact:5,settle:23},question:{start:9,impact:10,settle:25},factor:{start:19,impact:23,settle:54},calmHold:{start:54,end:87},sourceUi:{start:87,end:92}},
 colors:{bg0:'#230000',bg1:'#8F0808',column:'#D7D3CE',columnShadow:'#393333',question:'#C90D18',factor:'#D9D4CE'},
 sourceTransientProxyFrames:[0.37,4.64,9.73,14.44,20.95,23.20,36.37],
 structuralHitFrames:[0,5,10,14,21,23,36],
 rendererCalibration:{
  syntheticHitLeadFrames:1,
  authority:'INHERITED_HYPOTHESIS_FROM_S14_MUST_BE_PHYSICALLY_QUALIFIED_IN_S16',
  columnOpacityByY:{
   input:[792,807,828,858],
   output:[1,.86,.52,.20],
   authority:'STRUCTURAL_VISIBLE_OPACITY_APPROXIMATION_EXACT_SOURCE_ALPHA_UNKNOWN'
  }
 },
 authority:{sourceTiming:'MEASURED_DECODE',foregroundGeometry:'MEASURED_SOURCE_BOUND_PROJECTION_V1',cameraBeforeUi:'PHYSICALLY_MEASURED_STATIC_PROXY',cameraAfterUi:'GLOBAL_REFLOW_CAUSE_UNKNOWN_SOURCE_LOCK_BY_DEFAULT',factorFont:'FONT_CLASS_ONLY_EXACT_FONT_UNKNOWN',columnAsset:'STRUCTURAL_APPROXIMATION_OR_SOURCE_LOCK',questionAsset:'STRUCTURAL_APPROXIMATION_OR_SOURCE_LOCK',sfxIdentity:'UNKNOWN_FROM_MIXED_MASTER',sourceFidelity:'BLOCKED_UNTIL_SOURCE_BOUND_DIFF'},
} as const;
