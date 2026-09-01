import React,{useMemo}from'react';
import{Audio}from'@remotion/media';
import{AbsoluteFill,Sequence,useCurrentFrame}from'remotion';
import{measuredS14,type Box}from'./sourceMeasuredTrack';
import{measuredS14Annotation}from'./annotationMeasuredTrack';
import{S14_SPEC}from'./s14Spec';
import{makeS14Hit}from'./proceduralSfx';

type State='audio'|'visual'|'texto';
const tiles=Array.from({length:12},(_,i)=>i);
const measurementCard:Record<State,string>={audio:'#00F36D',visual:'#00A8FF',texto:'#EA00FF'};
const measurementHeading:Record<State,string>={audio:'#FFF200',visual:'#00FFF0',texto:'#FF7A00'};
const measurementAnnotation:Record<State,string>={audio:'#FF1A66',visual:'#6DFF00',texto:'#A66CFF'};
const headingVisibleBoundsCalibration:Record<State,{fontSizeMultiplier:number;baselineFactor:number;textLengthDelta:number;xOffset:number}>={
  // Calibrates this clean-runner fallback font to source-visible bounds. It does
  // not identify the unknown original font or claim original AE text metrics.
  audio:{fontSizeMultiplier:1.36,baselineFactor:1.0,textLengthDelta:5,xOffset:-2},
  visual:{fontSizeMultiplier:1.33,baselineFactor:1.0,textLengthDelta:7,xOffset:0},
  texto:{fontSizeMultiplier:1.51,baselineFactor:1.0,textLengthDelta:5,xOffset:-2},
};

const NestedMedia:React.FC<{state:State}> =({state})=>{
 const isVisual=state==='visual',isTexto=state==='texto';
 return <AbsoluteFill style={{background:'linear-gradient(180deg,#5e5b58,#9b9792)',filter:'grayscale(.72)',overflow:'hidden'}}>
   <div style={{position:'absolute',inset:0,background:'radial-gradient(circle at 50% 20%,rgba(255,255,255,.13),transparent 42%),repeating-linear-gradient(90deg,rgba(0,0,0,.12) 0 1px,transparent 1px 29px)',opacity:.65}}/>
   <div style={{position:'absolute',left:'10%',right:'8%',top:'8%',fontFamily:'Arial,Helvetica,sans-serif',fontWeight:700,color:'#ddd',fontSize:'5.8%'}}>How to Create a</div>
   <div style={{position:'absolute',left:'10%',right:'3%',top:'12%',fontFamily:'Arial Black,Arial,sans-serif',fontWeight:900,color:isTexto?S14_SPEC.colors.yellow:'#d8d5d0',fontSize:'10.2%',whiteSpace:'nowrap'}}>VIRAL SERIES</div>
   {isVisual?<div style={{position:'absolute',left:'12%',right:'9%',top:'22%',height:'28%',display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'3%'}}>{tiles.map(i=><div key={i} style={{background:i%3===0?'#9b6f6f':'#777',border:'1px solid rgba(255,255,255,.22)',borderRadius:4}}/>)}</div>:null}
   {isTexto?<div style={{position:'absolute',left:'14%',right:'10%',top:'25%',height:'28%',display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'3%'}}>{tiles.slice(0,9).map(i=><div key={i} style={{background:i%2?'#777':'#999',border:'1px solid rgba(255,255,255,.18)',borderRadius:3}}/>)}</div>:null}
   <div style={{position:'absolute',left:'8%',right:'8%',bottom:'8%',height:'36%',borderTop:'3px solid rgba(240,240,240,.55)',background:'linear-gradient(180deg,transparent,rgba(225,225,225,.18))'}}/>
   <div style={{position:'absolute',left:'36%',bottom:'31%',width:'28%',height:'31%',borderRadius:'50% 50% 38% 38%',background:'linear-gradient(180deg,#696969,#bbb)',opacity:.68}}/>
 </AbsoluteFill>;
};

const Annotation:React.FC<{state:State;box:Box|null;measurement?:boolean}> =({state,box,measurement=false})=>{
 if(!box)return null;
 const color=measurement?measurementAnnotation[state]:S14_SPEC.colors.red;
 // The measurement surface intentionally fills the measured bbox with a unique
 // identity color. It validates the source-bound screen-space trajectory only;
 // original vector-path morphology remains a separate unqualified dimension.
 if(measurement)return <div data-annotation={state} style={{position:'absolute',left:box.x,top:box.y,width:box.width,height:box.height,background:color}}/>;
 if(state==='audio')return <div data-annotation={state} style={{position:'absolute',left:box.x,top:box.y,width:box.width,height:box.height}}>
   <div style={{position:'absolute',left:0,right:0,top:'50%',height:Math.max(2,Math.min(4,box.height*.18)),background:color}}/>
   <div style={{position:'absolute',left:'17%',top:0,bottom:0,width:Math.max(2,Math.min(4,box.width*.015)),background:color}}/>
   <div style={{position:'absolute',left:0,right:0,top:'38%',height:'24%',background:`repeating-linear-gradient(90deg,transparent 0 4px,${color} 4px 6px,transparent 6px 10px)`,opacity:.92}}/>
 </div>;
 return <svg data-annotation={state} viewBox="0 0 100 100" preserveAspectRatio="none" style={{position:'absolute',left:box.x,top:box.y,width:box.width,height:box.height,overflow:'visible'}}><ellipse cx="50" cy="50" rx="49" ry="46" fill="none" stroke={color} strokeWidth="2.8"/></svg>;
};

const Card:React.FC<{state:State;box:Box|null;measurement?:boolean}> =({state,box,measurement=false})=>{
 if(!box)return null;
 return <div data-card={state} style={{position:'absolute',left:box.x,top:box.y,width:box.width,height:box.height,borderRadius:Math.max(18,box.width*.085),overflow:'hidden',boxShadow:measurement?'none':'0 16px 26px rgba(0,0,0,.28)',background:measurement?measurementCard[state]:'#777'}}>
   {measurement?null:<NestedMedia state={state}/>} 
 </div>;
};

const Heading:React.FC<{state:State;box:Box|null;measurement?:boolean}> =({state,box,measurement=false})=>{
 if(!box)return null;
 const c=headingVisibleBoundsCalibration[state];
 return <svg data-heading={state} width={512} height={1108} viewBox="0 0 512 1108" style={{position:'absolute',inset:0,overflow:'visible'}}>
   <text x={box.x+c.xOffset} y={box.y+box.height*c.baselineFactor} fill={measurement?measurementHeading[state]:S14_SPEC.colors.heading} fontFamily="Arial Black,Arial,sans-serif" fontWeight={900} fontSize={box.height*c.fontSizeMultiplier} textLength={Math.max(1,box.width+c.textLengthDelta)} lengthAdjust="spacingAndGlyphs" style={{filter:measurement?undefined:'drop-shadow(0 3px 2px rgba(0,0,0,.18))'}}>{state}</text>
 </svg>;
};

const EditorialLayer:React.FC<{transparent?:boolean;measurement?:boolean}> =({transparent=false,measurement=false})=>{
 const frame=useCurrentFrame();const m=measuredS14(frame);const a=measuredS14Annotation(frame);
 return <AbsoluteFill style={{background:transparent||measurement?'transparent':`radial-gradient(circle at 50% 42%,${S14_SPEC.colors.bg1},${S14_SPEC.colors.bg0} 68%,#4d0000)`,overflow:'hidden'}}>
   {!transparent&&!measurement?<div style={{position:'absolute',inset:0,backgroundImage:`linear-gradient(${S14_SPEC.colors.grid} 1px,transparent 1px),linear-gradient(90deg,${S14_SPEC.colors.grid} 1px,transparent 1px)`,backgroundSize:'100% 286px, 136px 100%',backgroundPosition:'0 252px, 126px 0',opacity:.68}}/>:null}
   <Card state="audio" box={m.cards.audio} measurement={measurement}/><Card state="visual" box={m.cards.visual} measurement={measurement}/><Card state="texto" box={m.cards.texto} measurement={measurement}/>
   <Annotation state="audio" box={a.audio} measurement={measurement}/><Annotation state="visual" box={a.visual} measurement={measurement}/><Annotation state="texto" box={a.texto} measurement={measurement}/>
   <Heading state="audio" box={m.headings.audio} measurement={measurement}/><Heading state="visual" box={m.headings.visual} measurement={measurement}/><Heading state="texto" box={m.headings.texto} measurement={measurement}/>
 </AbsoluteFill>;
};

const SourceChrome:React.FC=()=> <>
 <div style={{position:'absolute',left:0,right:0,top:0,height:44,background:'#050505'}}/>
 <div style={{position:'absolute',top:18,left:49,color:'#fff',fontFamily:'Arial',fontWeight:700,fontSize:18}}>17:33</div>
 <div style={{position:'absolute',top:11,left:139,width:226,height:53,borderRadius:30,background:'#030303',border:'1px solid rgba(120,0,0,.6)'}}><div style={{position:'absolute',left:17,top:17,width:15,height:15,borderRadius:99,background:'#e12822'}}/></div>
 <div style={{position:'absolute',right:25,top:25,color:'#fff',fontFamily:'Arial',fontWeight:700,fontSize:14}}>▮▮  ◉  54</div>
 <div style={{position:'absolute',left:0,right:0,bottom:0,height:62,background:'#050505'}}/>
 </>;

/** Target-isolated QA render. Unique colors validate entity geometry without adjacent-component contamination. */
export const S14Overlay:React.FC=()=> <EditorialLayer transparent measurement/>;

export const S14AudioVisualTexto:React.FC=()=>{
 const hits=useMemo(()=>S14_SPEC.transientLocalFrames.map((frame,i)=>({frame,playFrame:Math.max(0,frame-S14_SPEC.rendererCalibration.syntheticHitLeadFrames),src:makeS14Hit(0x1400+i,460+i*35)})),[]);
 return <AbsoluteFill style={{background:'#650000'}}><EditorialLayer/><SourceChrome/>{hits.map((h,i)=><Sequence key={i} from={h.playFrame} layout="none"><Audio src={h.src} volume={i===2||i===5?.48:.3}/></Sequence>)}</AbsoluteFill>;
};

export const S14_HEADING_VISIBLE_BOUNDS_CALIBRATION=headingVisibleBoundsCalibration;
