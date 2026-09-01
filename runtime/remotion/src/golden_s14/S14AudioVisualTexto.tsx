import React,{useMemo}from'react';
import{Audio}from'@remotion/media';
import{AbsoluteFill,Sequence,useCurrentFrame}from'remotion';
import{measuredS14,type Box}from'./sourceMeasuredTrack';
import{S14_SPEC}from'./s14Spec';
import{makeS14Hit}from'./proceduralSfx';

type State='audio'|'visual'|'texto';
const tiles=Array.from({length:12},(_,i)=>i);
const measurementCard:Record<State,string>={audio:'#00F36D',visual:'#00A8FF',texto:'#EA00FF'};
const measurementHeading:Record<State,string>={audio:'#FFF200',visual:'#00FFF0',texto:'#FF7A00'};
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
   {state==='audio'?<>
      <div style={{position:'absolute',left:'13%',right:'12%',top:'43%',height:3,background:S14_SPEC.colors.red}}/>
      <div style={{position:'absolute',left:'19%',top:'34%',height:'23%',width:3,background:S14_SPEC.colors.red}}/>
      <div style={{position:'absolute',left:'15%',right:'13%',top:'42%',height:'5%',background:'repeating-linear-gradient(90deg,transparent 0 4px,#b71318 4px 6px,transparent 6px 10px)',opacity:.9}}/>
   </>:null}
   {isVisual?<div style={{position:'absolute',left:'12%',right:'9%',top:'22%',height:'28%',display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'3%'}}>{tiles.map(i=><div key={i} style={{background:i%3===0?'#9b6f6f':'#777',border:'1px solid rgba(255,255,255,.22)',borderRadius:4}}/>)}</div>:null}
   {isTexto?<div style={{position:'absolute',left:'14%',right:'10%',top:'25%',height:'28%',display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'3%'}}>{tiles.slice(0,9).map(i=><div key={i} style={{background:i%2?'#777':'#999',border:'1px solid rgba(255,255,255,.18)',borderRadius:3}}/>)}</div>:null}
   <div style={{position:'absolute',left:'8%',right:'8%',bottom:'8%',height:'36%',borderTop:'3px solid rgba(240,240,240,.55)',background:'linear-gradient(180deg,transparent,rgba(225,225,225,.18))'}}/>
   <div style={{position:'absolute',left:'36%',bottom:'31%',width:'28%',height:'31%',borderRadius:'50% 50% 38% 38%',background:'linear-gradient(180deg,#696969,#bbb)',opacity:.68}}/>
 </AbsoluteFill>;
};

const Annotation:React.FC<{state:State}> =({state})=>{
 if(state==='audio')return null;
 if(state==='visual')return <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{position:'absolute',left:'3%',top:'18%',width:'95%',height:'36%',overflow:'visible'}}><ellipse cx="51" cy="49" rx="48" ry="45" fill="none" stroke={S14_SPEC.colors.red} strokeWidth="2.5"/></svg>;
 return <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{position:'absolute',left:'5%',top:'4%',width:'90%',height:'27%',overflow:'visible'}}><ellipse cx="50" cy="50" rx="48" ry="43" fill="none" stroke={S14_SPEC.colors.red} strokeWidth="2.5"/></svg>;
};

const Card:React.FC<{state:State;box:Box|null;measurement?:boolean}> =({state,box,measurement=false})=>{
 if(!box)return null;
 return <div data-card={state} style={{position:'absolute',left:box.x,top:box.y,width:box.width,height:box.height,borderRadius:Math.max(18,box.width*.085),overflow:'hidden',boxShadow:measurement?'none':'0 16px 26px rgba(0,0,0,.28)',background:measurement?measurementCard[state]:'#777'}}>
   {measurement?null:<><NestedMedia state={state}/><Annotation state={state}/></>}
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
 const frame=useCurrentFrame();const m=measuredS14(frame);
 return <AbsoluteFill style={{background:transparent||measurement?'transparent':`radial-gradient(circle at 50% 42%,${S14_SPEC.colors.bg1},${S14_SPEC.colors.bg0} 68%,#4d0000)`,overflow:'hidden'}}>
   {!transparent&&!measurement?<div style={{position:'absolute',inset:0,backgroundImage:`linear-gradient(${S14_SPEC.colors.grid} 1px,transparent 1px),linear-gradient(90deg,${S14_SPEC.colors.grid} 1px,transparent 1px)`,backgroundSize:'100% 286px, 136px 100%',backgroundPosition:'0 252px, 126px 0',opacity:.68}}/>:null}
   <Card state="audio" box={m.cards.audio} measurement={measurement}/><Card state="visual" box={m.cards.visual} measurement={measurement}/><Card state="texto" box={m.cards.texto} measurement={measurement}/>
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

/** Target-isolated QA render. Colors identify entities but geometry is driven by the same measured tracks as the production structural render. */
export const S14Overlay:React.FC=()=> <EditorialLayer transparent measurement/>;

export const S14AudioVisualTexto:React.FC=()=>{
 const hits=useMemo(()=>S14_SPEC.transientLocalFrames.map((frame,i)=>({frame,src:makeS14Hit(0x1400+i,460+i*35)})),[]);
 return <AbsoluteFill style={{background:'#650000'}}><EditorialLayer/><SourceChrome/>{hits.map((h,i)=><Sequence key={i} from={h.frame} layout="none"><Audio src={h.src} volume={i===2||i===5?.48:.3}/></Sequence>)}</AbsoluteFill>;
};

export const S14_HEADING_VISIBLE_BOUNDS_CALIBRATION=headingVisibleBoundsCalibration;
