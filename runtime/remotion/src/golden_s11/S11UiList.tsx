import React, {useMemo} from 'react';
import {Audio} from '@remotion/media';
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame} from 'remotion';
import {S11_SPEC} from './s11Spec';
import {makeUiHitDataUri} from './proceduralSfx';
import {measuredS11, type S11MeasuredBox} from './sourceMeasuredTrack';

const clamp={extrapolateLeft:'clamp' as const,extrapolateRight:'clamp' as const};
const fade=(frame:number,start:number,end:number)=>interpolate(frame,[start,end],[0,1],clamp);

const HookMark:React.FC<{box:S11MeasuredBox}>=({box})=>(
  <div style={{position:'absolute',left:box.x,top:box.y,width:box.width,height:box.height}}>
    <svg width="100%" height="100%" viewBox="0 0 66 66">
      <circle cx="33" cy="33" r="31" fill="#E8E8E3"/>
      <path d="M26 21 C17 26 20 38 27 39 C34 40 37 32 32 27" fill="none" stroke="#1B1B1B" strokeWidth="5" strokeLinecap="round"/>
      <path d="M39 25 C48 29 46 42 38 44 C31 45 28 38 31 34" fill="none" stroke="#1B1B1B" strokeWidth="5" strokeLinecap="round"/>
    </svg>
  </div>
);

const RowIcon:React.FC<{kind:'x'|'diamond'|'megaphone';box:S11MeasuredBox}>=({kind,box})=>(
  <div style={{position:'absolute',left:box.x,top:box.y,width:box.width,height:box.height,borderRadius:999,background:'#ECECE6',display:'grid',placeItems:'center',boxShadow:'0 2px 5px rgba(0,0,0,.18)'}}>
    {kind==='x'?<div style={{fontSize:box.height*.64,fontFamily:'Arial',fontWeight:300,lineHeight:1,color:'#151515'}}>X</div>:null}
    {kind==='diamond'?<svg width="58%" height="58%" viewBox="0 0 44 44"><path d="M8 16 L14 9 H30 L36 16 L22 36 Z" fill="#171717"/><path d="M8 16 H36 M14 9 L18 16 L22 9 L26 16 L30 9" stroke="#ECECE6" strokeWidth="2" fill="none"/></svg>:null}
    {kind==='megaphone'?<svg width="56%" height="56%" viewBox="0 0 42 42"><path d="M8 20 L27 11 V31 L8 25 Z" fill="#171717"/><rect x="5" y="19" width="7" height="8" rx="2" fill="#171717"/><path d="M16 26 L20 35 H15 L11 27" fill="#171717"/></svg>:null}
  </div>
);

const Lines:React.FC<{box:S11MeasuredBox;kind:'x'|'diamond'|'megaphone'}>=({box,kind})=>{
  const ys=kind==='x'?[.38,.60]:kind==='diamond'?[.05,.27,.49,.71,.93,1.15]:[.39,.67];
  const widths=kind==='x'?[250,232]:kind==='diamond'?[250,232,250,232,250,184]:[251,232];
  const left=Math.max(184,box.x+box.width+20);
  return <>{ys.map((ratio,i)=><div key={i} style={{position:'absolute',left,top:box.y+box.height*ratio,width:widths[i],height:i%2===0?5:6,borderRadius:4,background:'#151515'}}/>)}</>;
};

const EditorialSystem:React.FC<{transparent?:boolean}>=({transparent=false})=>{
  const frame=useCurrentFrame();
  const m=measuredS11(frame);
  const abs=m.absolute;
  const pill=m.pill;
  const arrowProgress=fade(frame,7,28);
  const absEntry=fade(frame,50,54);
  const word=(start:number,end:number)=>fade(frame,start,end);

  const absProxy=abs??measuredS11(54).absolute!;
  const wordYOffset=absProxy.y-424;
  const wordXOffset=absProxy.x-190;
  const arrowDx=(pill?.x??64)-64;
  const arrowDy=(pill?.y??490)-490;

  return <AbsoluteFill style={{background:transparent?'transparent':'radial-gradient(circle at 50% 53%,#C70B0B 0%,#9D0000 38%,#620000 100%)',overflow:'hidden'}}>
    {pill?<>
      <div data-layer="hero-pill" style={{position:'absolute',left:pill.x,top:pill.y,width:pill.width,height:pill.height,borderRadius:Math.min(70,pill.height/2),background:'#252525',opacity:.985,boxShadow:'0 8px 18px rgba(0,0,0,.18)'}}/>
      {m.hook?<HookMark box={m.hook}/>:null}
      <div style={{position:'absolute',left:pill.x+pill.width*.33,top:pill.y+pill.height*.35,width:pill.width*.54,height:4,borderRadius:4,background:'#AF1012',opacity:fade(frame,5,21)}}/>
      <div style={{position:'absolute',left:pill.x+pill.width*.33,top:pill.y+pill.height*.57,width:pill.width*.56,height:6,borderRadius:5,background:'#EAEAE5',opacity:fade(frame,5,21)}}/>
    </>:null}

    <svg width="512" height="1108" viewBox="0 0 512 1108" style={{position:'absolute',inset:0,pointerEvents:'none'}}>
      <g transform={`translate(${arrowDx} ${arrowDy})`}>
        <path d="M326 592 C317 626 257 628 250 586 C246 558 270 548 293 559" fill="none" stroke="#B8B8B6" strokeWidth="6" strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1-arrowProgress}/>
        <path d="M291 559 L278 553 M291 559 L284 571" fill="none" stroke="#B8B8B6" strokeWidth="6" strokeLinecap="round" opacity={arrowProgress}/>
      </g>
    </svg>

    <div data-word="debe" style={{position:'absolute',left:60+wordXOffset,top:398+wordYOffset,color:'#E9E7E2',fontFamily:'Arial,Helvetica,sans-serif',fontWeight:700,fontSize:17,opacity:word(36,39)}}>debe</div>
    <div data-word="dejar" style={{position:'absolute',left:140+wordXOffset,top:420+wordYOffset,color:'#E9E7E2',fontFamily:'Arial,Helvetica,sans-serif',fontWeight:700,fontSize:17,opacity:word(43,46)}}>dejar</div>
    <div data-word="absolutamente" style={{position:'absolute',left:absProxy.x,top:absProxy.y,width:absProxy.width,height:absProxy.height,background:'#EDECE6',color:'#A9070B',fontFamily:'Arial,Helvetica,sans-serif',fontWeight:900,fontSize:Math.max(12,absProxy.height*.57),lineHeight:`${absProxy.height}px`,textAlign:'center',overflow:'hidden',opacity:abs?1:absEntry}}>absolutamente</div>
    <div data-word="claro" style={{position:'absolute',left:absProxy.x+absProxy.width+8,top:absProxy.y+absProxy.height+5,color:'#E9E7E2',fontFamily:'Arial,Helvetica,sans-serif',fontWeight:700,fontSize:17,opacity:word(68,73)}}>claro</div>

    {m.xRow?<><RowIcon kind="x" box={m.xRow}/><Lines kind="x" box={m.xRow}/></>:null}
    {m.diamondRow?<><RowIcon kind="diamond" box={m.diamondRow}/><Lines kind="diamond" box={m.diamondRow}/></>:null}
    {m.megaphoneRow?<><RowIcon kind="megaphone" box={m.megaphoneRow}/><Lines kind="megaphone" box={m.megaphoneRow}/></>:null}
  </AbsoluteFill>;
};

const SourceChromeProxy:React.FC=()=> <>
  <div style={{position:'absolute',left:0,right:0,top:0,height:52,background:'#050505'}}/>
  <div style={{position:'absolute',top:9,left:26,color:'#F4F4F4',fontFamily:'Arial',fontSize:16,fontWeight:700}}>17:33</div>
  <div style={{position:'absolute',top:7,left:151,width:211,height:38,borderRadius:28,background:'#030303',border:'1px solid #1E0505'}}><div style={{position:'absolute',left:18,top:13,width:12,height:12,borderRadius:99,background:'#E02019'}}/></div>
  <div style={{position:'absolute',top:12,right:25,width:78,height:12,opacity:.88,background:'linear-gradient(90deg,#fff 0 10%,transparent 10% 24%,#fff 24% 34%,transparent 34% 48%,#fff 48% 60%,transparent 60% 72%,#fff 72% 100%)'}}/>
  <div style={{position:'absolute',left:0,right:0,bottom:0,height:63,background:'#050505'}}/>
</>;

export const S11Overlay:React.FC=()=> <EditorialSystem transparent/>;
export const S11UiList:React.FC=()=>{
  const hit54=useMemo(()=>makeUiHitDataUri(0x1154,460),[]);
  const hit85=useMemo(()=>makeUiHitDataUri(0x1185,620),[]);
  const hit93=useMemo(()=>makeUiHitDataUri(0x1193,680),[]);
  const hit102=useMemo(()=>makeUiHitDataUri(0x1102,740),[]);
  return <AbsoluteFill style={{background:'#750000'}}>
    <EditorialSystem/><SourceChromeProxy/>
    <Sequence from={54} layout="none"><Audio src={hit54} volume={0.52}/></Sequence>
    <Sequence from={85} layout="none"><Audio src={hit85} volume={0.46}/></Sequence>
    <Sequence from={93} layout="none"><Audio src={hit93} volume={0.46}/></Sequence>
    <Sequence from={102} layout="none"><Audio src={hit102} volume={0.5}/></Sequence>
  </AbsoluteFill>;
};
