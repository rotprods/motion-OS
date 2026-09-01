import React,{useMemo}from'react';
import{Audio}from'@remotion/media';
import{AbsoluteFill,Sequence,interpolate,useCurrentFrame}from'remotion';
import{measuredS16,type S16Box}from'./sourceMeasuredTrack';
import{S16_SPEC}from'./s16Spec';
import{makeS16Hit}from'./proceduralSfx';

const clamp={extrapolateLeft:'clamp' as const,extrapolateRight:'clamp' as const};
const measurement={column:'#00F36D',question:'#00A8FF',factor:'#FFF200'};

export const columnOpacityFromY=(y:number)=>{
 const calibration=S16_SPEC.rendererCalibration.columnOpacityByY;
 return interpolate(y,[...calibration.input],[...calibration.output],clamp);
};

const SubjectProxy:React.FC=()=>{
 const frame=useCurrentFrame();
 const uiShift=interpolate(frame,[87,91],[0,-18],clamp);
 return <AbsoluteFill style={{transform:`translateY(${uiShift}px)`,background:'radial-gradient(circle at 28% 45%,#B11216 0%,#65070A 28%,#260002 68%,#080000 100%)',overflow:'hidden'}}>
   <div style={{position:'absolute',left:62,top:170,width:340,height:500,borderRadius:'48% 52% 44% 46%',background:'radial-gradient(circle at 54% 35%,#9D775F 0%,#74432F 33%,#2E1511 65%,#110807 100%)',boxShadow:'0 20px 80px rgba(0,0,0,.52)',opacity:.92}}/>
   <div style={{position:'absolute',left:38,top:620,width:430,height:360,borderRadius:'50% 50% 0 0',background:'linear-gradient(135deg,#080707,#1A1010 52%,#050404)',opacity:.95}}/>
   <div style={{position:'absolute',inset:0,background:'radial-gradient(circle at 50% 50%,transparent 44%,rgba(0,0,0,.48) 100%)'}}/>
 </AbsoluteFill>;
};

const ColumnGraphic:React.FC<{box:S16Box}> =({box})=>{
 const opacity=columnOpacityFromY(box.y);
 return <div data-layer="column" style={{position:'absolute',left:box.x,top:box.y,width:230,height:224,opacity,filter:'drop-shadow(10px 9px 7px rgba(0,0,0,.32))'}}>
  <svg viewBox="0 0 230 224" width="230" height="224">
   <defs><linearGradient id="stone" x1="0" x2="1"><stop offset="0" stopColor="#AAA5A1"/><stop offset=".22" stopColor="#F1EDE8"/><stop offset=".55" stopColor="#C9C4BF"/><stop offset=".8" stopColor="#F1EDE8"/><stop offset="1" stopColor="#8C8885"/></linearGradient></defs>
   <rect x="48" y="45" width="132" height="179" rx="4" fill="url(#stone)"/>
   <path d="M42 46h144l-16 24H58z" fill="url(#stone)"/>
   <rect x="22" y="18" width="186" height="29" rx="3" fill="url(#stone)"/>
   <path d="M24 18 Q43 0 59 18 Q77 0 94 18 Q112 0 129 18 Q147 0 164 18 Q182 0 207 18Z" fill="url(#stone)"/>
   {[70,88,106,124,142,160].map(x=><path key={x} d={`M${x} 66V224`} stroke="rgba(80,74,70,.28)" strokeWidth="5"/>)}
  </svg>
 </div>;
};

const QuestionGraphic:React.FC<{box:S16Box}> =({box})=>{
 const opacity=interpolate(box.height,[70,145,180],[.40,.88,1],clamp);
 return <svg data-layer="question" viewBox="0 0 100 240" preserveAspectRatio="none" style={{position:'absolute',left:box.x,top:box.y,width:box.width,height:box.height,overflow:'visible',filter:'drop-shadow(5px 6px 4px rgba(0,0,0,.28))',opacity}}>
   <text x="50" y="190" textAnchor="middle" fill={S16_SPEC.colors.question} fontFamily="Georgia,Times New Roman,serif" fontWeight={700} fontSize="225" transform="scale(.92,1)">?</text>
 </svg>;
};

const FactorText:React.FC<{box:S16Box&{relativeLuma:number};measurementMode?:boolean}> =({box,measurementMode=false})=>{
 const opacity=Math.max(0,Math.min(1,box.relativeLuma));
 return <svg data-layer="factor-x" width="512" height="1108" viewBox="0 0 512 1108" style={{position:'absolute',inset:0,overflow:'visible',opacity}}>
   <text x={box.x} y={box.y+58} fill={measurementMode?measurement.factor:S16_SPEC.colors.factor} fontFamily="Arial Black,Arial,sans-serif" fontSize="72" fontWeight={900} textLength={box.width} lengthAdjust="spacingAndGlyphs" style={{filter:measurementMode?undefined:'drop-shadow(0 5px 3px rgba(0,0,0,.30))'}}>Factor X</text>
 </svg>;
};

const EditorialLayers:React.FC<{measurementMode?:boolean}> =({measurementMode=false})=>{
 const frame=useCurrentFrame();const m=measuredS16(frame);
 if(measurementMode)return <AbsoluteFill style={{background:'transparent'}}>
   {m.column?<div style={{position:'absolute',left:m.column.x,top:m.column.y,width:m.column.width,height:m.column.height,background:measurement.column}}/>:null}
   {m.questionMark?<div style={{position:'absolute',left:m.questionMark.x,top:m.questionMark.y,width:m.questionMark.width,height:m.questionMark.height,background:measurement.question}}/>:null}
   {m.factorX?<FactorText box={m.factorX} measurementMode/>:null}
 </AbsoluteFill>;
 return <AbsoluteFill style={{overflow:'hidden'}}>
   {m.questionMark?<QuestionGraphic box={m.questionMark}/>:null}
   {m.column?<ColumnGraphic box={m.column}/>:null}
   {m.factorX?<FactorText box={m.factorX}/>:null}
 </AbsoluteFill>;
};

const SourceUiProxy:React.FC=()=>{
 const frame=useCurrentFrame();if(frame<87)return null;
 const p=interpolate(frame,[87,89,91],[0,.8,1],clamp);
 return <AbsoluteFill style={{pointerEvents:'none',opacity:p,color:'#fff',fontFamily:'Arial,Helvetica,sans-serif'}}>
   <div style={{position:'absolute',top:88,left:32,fontWeight:900,fontSize:21}}>Reels</div>
   <div style={{position:'absolute',right:21,top:370,fontSize:35,lineHeight:2.25,textAlign:'center'}}>♡<br/>◯<br/>⌁<br/>⋮</div>
   <div style={{position:'absolute',left:11,right:11,bottom:87,fontSize:14,fontWeight:800}}>lemonde_by_ondray ✦</div>
   <div style={{position:'absolute',left:11,right:60,bottom:58,fontSize:13,opacity:.9}}>High quality video tip · original audio</div>
 </AbsoluteFill>;
};

const StructuralAudio:React.FC=()=>{
 const hits=useMemo(()=>S16_SPEC.structuralHitFrames.map((frame,i)=>({frame,playFrame:Math.max(0,frame-S16_SPEC.rendererCalibration.syntheticHitLeadFrames),src:makeS16Hit(0x1600+i,390+i*35)})),[]);
 return <>{hits.map((h,i)=><Sequence key={i} from={h.playFrame} layout="none"><Audio src={h.src} volume={i===2||i===5?.52:.34}/></Sequence>)}</>;
};

export const S16Overlay:React.FC=()=> <AbsoluteFill style={{background:'transparent',overflow:'hidden'}}><EditorialLayers measurementMode/></AbsoluteFill>;

export const S16FactorX:React.FC=()=> <AbsoluteFill style={{background:'#080000',overflow:'hidden'}}>
 <div style={{position:'absolute',left:0,right:0,top:0,height:S16_SPEC.source.contentBottom,overflow:'hidden',borderRadius:'0 0 42px 42px'}}>
   <SubjectProxy/><EditorialLayers/>
 </div>
 <SourceUiProxy/>
 <StructuralAudio/>
</AbsoluteFill>;
