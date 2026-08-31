import React, {useMemo} from 'react';
import {Audio} from '@remotion/media';
import {AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame} from 'remotion';
import {S11_SPEC} from './s11Spec';
import {makeUiHitDataUri} from './proceduralSfx';

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const easeOut = Easing.bezier(0.16, 1, 0.3, 1);
const easeStd = Easing.bezier(0.4, 0, 0.2, 1);

const reveal = (frame: number, start: number, impact: number, from = 0) =>
  interpolate(frame, [start, impact], [from, 1], {...clamp, easing: easeOut});

const HookMark: React.FC<{size?: number}> = ({size = 66}) => (
  <svg width={size} height={size} viewBox="0 0 66 66">
    <circle cx="33" cy="33" r="31" fill="#E8E8E3" />
    <path d="M26 21 C17 26 20 38 27 39 C34 40 37 32 32 27" fill="none" stroke="#1B1B1B" strokeWidth="5" strokeLinecap="round"/>
    <path d="M39 25 C48 29 46 42 38 44 C31 45 28 38 31 34" fill="none" stroke="#1B1B1B" strokeWidth="5" strokeLinecap="round"/>
  </svg>
);

const RowIcon: React.FC<{kind: 'x'|'diamond'|'megaphone'}> = ({kind}) => (
  <div style={{width:68,height:68,borderRadius:999,background:'#ECECE6',display:'grid',placeItems:'center',boxShadow:'0 2px 5px rgba(0,0,0,.18)'}}>
    {kind === 'x' ? <div style={{fontSize:52,fontFamily:'Arial',fontWeight:300,lineHeight:1,color:'#151515'}}>X</div> : null}
    {kind === 'diamond' ? (
      <svg width="44" height="44" viewBox="0 0 44 44"><path d="M8 16 L14 9 H30 L36 16 L22 36 Z" fill="#171717"/><path d="M8 16 H36 M14 9 L18 16 L22 9 L26 16 L30 9" stroke="#ECECE6" strokeWidth="2" fill="none"/></svg>
    ) : null}
    {kind === 'megaphone' ? (
      <svg width="42" height="42" viewBox="0 0 42 42"><path d="M8 20 L27 11 V31 L8 25 Z" fill="#171717"/><rect x="5" y="19" width="7" height="8" rx="2" fill="#171717"/><path d="M16 26 L20 35 H15 L11 27" fill="#171717"/></svg>
    ) : null}
  </div>
);

const FakeCopyLines: React.FC<{variant:number}> = ({variant}) => {
  const widths = variant === 0 ? [246,216,194] : variant === 1 ? [244,232,206,162] : [248,222,178];
  return <div style={{display:'flex',flexDirection:'column',gap:8}}>{widths.map((w,i)=><div key={i} style={{width:w,height:5,borderRadius:4,background:'#161616'}} />)}</div>;
};

const EditorialSystem: React.FC<{transparent?:boolean}> = ({transparent=false}) => {
  const frame = useCurrentFrame();
  const lift = interpolate(frame,[S11_SPEC.anchors.groupLift.start,S11_SPEC.anchors.groupLift.impact,S11_SPEC.anchors.groupLift.end],[0,-88,-88],{...clamp,easing:easeStd});
  const pillProgress = reveal(frame,0,8,0);
  const pillWidth = interpolate(frame,[0,8,16,54,85,129],[336,344,362,402,426,438],clamp);
  const pillHeight = interpolate(frame,[0,8,16,54,85,129],[32,96,103,114,82,82],clamp);
  const pillTopBase = interpolate(frame,[0,8,16,54],[530,498,496,492],clamp);
  const pillX = (512-pillWidth)/2;
  const lineProgress = reveal(frame,5,21,0);
  const arrowProgress = reveal(frame,7,28,0);
  const rowState = (start:number,impact:number) => ({opacity:reveal(frame,start,impact,0),y:interpolate(frame,[start,impact],[35,0],{...clamp,easing:easeOut})});
  const rowX=rowState(82,85), rowD=rowState(90,93), rowM=rowState(99,102);
  const word = (start:number,impact:number,dx=-12,dy=9) => ({opacity:reveal(frame,start,impact,0),transform:`translate(${interpolate(frame,[start,impact],[dx,0],{...clamp,easing:easeOut})}px, ${interpolate(frame,[start,impact],[dy,0],{...clamp,easing:easeOut})}px)`});

  return (
    <AbsoluteFill style={{background:transparent?'transparent':'radial-gradient(circle at 50% 53%,#C70B0B 0%,#9D0000 38%,#620000 100%)',overflow:'hidden'}}>
      <div style={{position:'absolute',inset:0,transform:`translateY(${lift}px)`}}>
        <div data-layer="hero-pill" style={{position:'absolute',left:pillX,top:pillTopBase,width:pillWidth,height:pillHeight,borderRadius:60,background:'#252525',opacity:0.98*pillProgress,boxShadow:'0 8px 18px rgba(0,0,0,.18)'}}>
          <div style={{position:'absolute',left:12,top:'50%',transform:`translateY(-50%) scale(${interpolate(frame,[0,8],[0.45,1],{...clamp,easing:easeOut})})`}}><HookMark size={64}/></div>
          <div style={{position:'absolute',left:94,top:'35%',width:Math.max(1,(pillWidth-122)*lineProgress),height:4,borderRadius:4,background:'#AF1012'}}/>
          <div style={{position:'absolute',left:94,top:'57%',width:Math.max(1,(pillWidth-140)*lineProgress),height:6,borderRadius:5,background:'#EAEAE5'}}/>
        </div>

        <svg width="512" height="1108" viewBox="0 0 512 1108" style={{position:'absolute',inset:0,pointerEvents:'none'}}>
          <path d="M326 592 C317 626 257 628 250 586 C246 558 270 548 293 559" fill="none" stroke="#B8B8B6" strokeWidth="6" strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1-arrowProgress}/>
          <path d="M291 559 L278 553 M291 559 L284 571" fill="none" stroke="#B8B8B6" strokeWidth="6" strokeLinecap="round" opacity={arrowProgress}/>
        </svg>

        <div data-word="debe" style={{position:'absolute',left:61,top:452,color:'#E9E7E2',fontFamily:'Arial,Helvetica,sans-serif',fontWeight:700,fontSize:17,...word(36,39)}}>debe</div>
        <div data-word="dejar" style={{position:'absolute',left:144,top:473,color:'#E9E7E2',fontFamily:'Arial,Helvetica,sans-serif',fontWeight:700,fontSize:17,...word(43,46)}}>dejar</div>
        <div data-word="absolutamente" style={{position:'absolute',left:211,top:493,padding:'2px 7px 3px',background:'#EDECE6',color:'#A9070B',fontFamily:'Arial,Helvetica,sans-serif',fontWeight:900,fontSize:18,lineHeight:1,...word(50,54,-10,6)}}>absolutamente</div>
        <div data-word="claro" style={{position:'absolute',right:42,top:521,color:'#E9E7E2',fontFamily:'Arial,Helvetica,sans-serif',fontWeight:700,fontSize:17,...word(68,73,10,5)}}>claro</div>

        <div data-row="x" style={{position:'absolute',left:61,top:610,display:'flex',alignItems:'center',gap:28,opacity:rowX.opacity,transform:`translateY(${rowX.y}px)`}}><RowIcon kind="x"/><FakeCopyLines variant={0}/></div>
        <div data-row="diamond" style={{position:'absolute',left:61,top:716,display:'flex',alignItems:'center',gap:28,opacity:rowD.opacity,transform:`translateY(${rowD.y}px)`}}><RowIcon kind="diamond"/><FakeCopyLines variant={1}/></div>
        <div data-row="megaphone" style={{position:'absolute',left:61,top:826,display:'flex',alignItems:'center',gap:28,opacity:rowM.opacity,transform:`translateY(${rowM.y}px)`}}><RowIcon kind="megaphone"/><FakeCopyLines variant={2}/></div>
      </div>
    </AbsoluteFill>
  );
};

const SourceChromeProxy: React.FC = () => (
  <>
    <div style={{position:'absolute',left:0,right:0,top:0,height:52,background:'#050505'}}/>
    <div style={{position:'absolute',top:9,left:26,color:'#F4F4F4',fontFamily:'Arial',fontSize:16,fontWeight:700}}>17:33</div>
    <div style={{position:'absolute',top:7,left:151,width:211,height:38,borderRadius:28,background:'#030303',border:'1px solid #1E0505'}}><div style={{position:'absolute',left:18,top:13,width:12,height:12,borderRadius:99,background:'#E02019'}}/></div>
    <div style={{position:'absolute',top:12,right:25,width:78,height:12,opacity:.88,background:'linear-gradient(90deg,#fff 0 10%,transparent 10% 24%,#fff 24% 34%,transparent 34% 48%,#fff 48% 60%,transparent 60% 72%,#fff 72% 100%)'}}/>
    <div style={{position:'absolute',left:0,right:0,bottom:0,height:63,background:'#050505'}}/>
  </>
);

export const S11Overlay: React.FC = () => <EditorialSystem transparent/>;

export const S11UiList: React.FC = () => {
  const hit54=useMemo(()=>makeUiHitDataUri(0x1154,460),[]);
  const hit85=useMemo(()=>makeUiHitDataUri(0x1185,620),[]);
  const hit93=useMemo(()=>makeUiHitDataUri(0x1193,680),[]);
  const hit102=useMemo(()=>makeUiHitDataUri(0x1102,740),[]);
  return (
    <AbsoluteFill style={{background:'#750000'}}>
      <EditorialSystem/>
      <SourceChromeProxy/>
      <Sequence from={54} layout="none"><Audio src={hit54} volume={0.52}/></Sequence>
      <Sequence from={85} layout="none"><Audio src={hit85} volume={0.46}/></Sequence>
      <Sequence from={93} layout="none"><Audio src={hit93} volume={0.46}/></Sequence>
      <Sequence from={102} layout="none"><Audio src={hit102} volume={0.5}/></Sequence>
    </AbsoluteFill>
  );
};
