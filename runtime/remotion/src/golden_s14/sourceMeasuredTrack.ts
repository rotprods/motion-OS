export type Box={x:number;y:number;width:number;height:number;opacity?:number};
type K=Box&{frame:number};
const lerp=(a:number,b:number,t:number)=>a+(b-a)*t;
const sample=(frame:number,track:K[]):Box|null=>{
  if(frame<track[0].frame||frame>track[track.length-1].frame)return null;
  const exact=track.find(k=>k.frame===frame);if(exact)return exact;
  const r=track.findIndex(k=>k.frame>frame);const a=track[r-1],b=track[r];const t=(frame-a.frame)/(b.frame-a.frame);
  return {x:lerp(a.x,b.x,t),y:lerp(a.y,b.y,t),width:lerp(a.width,b.width,t),height:lerp(a.height,b.height,t),opacity:lerp(a.opacity??1,b.opacity??1,t)};
};

const AUDIO_CARD:K[]=[
{frame:0,x:135,y:261,width:260,height:502},{frame:2,x:127,y:287,width:278,height:490},{frame:6,x:121,y:275,width:296,height:514},{frame:10,x:83,y:265,width:303,height:532},{frame:11,x:0,y:263,width:329,height:536},{frame:12,x:0,y:261,width:247,height:542},{frame:14,x:0,y:261,width:189,height:544},{frame:15,x:0,y:261,width:146,height:544},{frame:16,x:0,y:261,width:115,height:546},{frame:17,x:0,y:261,width:81,height:546},{frame:18,x:0,y:261,width:81,height:546}];
const VISUAL_CARD:K[]=[
{frame:11,x:422,y:273,width:90,height:532},{frame:12,x:340,y:269,width:172,height:538},{frame:14,x:278,y:265,width:234,height:542},{frame:15,x:236,y:261,width:276,height:548},{frame:16,x:205,y:261,width:307,height:548},{frame:17,x:172,y:261,width:315,height:550},{frame:19,x:155,y:261,width:318,height:552},{frame:20,x:143,y:261,width:318,height:556},{frame:25,x:111,y:261,width:326,height:558},{frame:35,x:99,y:261,width:334,height:566},{frame:44,x:95,y:261,width:340,height:570},{frame:46,x:67,y:261,width:340,height:572},{frame:47,x:0,y:261,width:323,height:572},{frame:49,x:0,y:261,width:239,height:572},{frame:50,x:0,y:261,width:185,height:572},{frame:52,x:0,y:261,width:108,height:572},{frame:54,x:0,y:261,width:75,height:572}];
const TEXTO_CARD:K[]=[
{frame:47,x:431,y:261,width:81,height:566},{frame:49,x:346,y:261,width:166,height:568},{frame:50,x:283,y:261,width:229,height:566},{frame:52,x:207,y:261,width:305,height:568},{frame:54,x:182,y:261,width:330,height:570},{frame:55,x:162,y:261,width:350,height:570},{frame:60,x:115,y:261,width:354,height:570},{frame:65,x:95,y:261,width:354,height:570},{frame:75,x:93,y:261,width:356,height:572},{frame:90,x:91,y:261,width:358,height:576},{frame:93,x:91,y:261,width:358,height:576}];

const AUDIO_HEAD:K[]=[
{frame:0,x:155,y:226,width:213,height:49},{frame:2,x:150,y:210,width:225,height:50},{frame:6,x:144,y:194,width:238,height:52},{frame:10,x:108,y:182,width:245,height:54},{frame:11,x:50,y:179,width:249,height:54},{frame:12,x:19,y:176,width:196,height:53},{frame:14,x:15,y:175,width:138,height:52},{frame:15,x:15,y:185,width:94,height:40},{frame:16,x:16,y:185,width:62,height:36},{frame:17,x:15,y:189,width:27,height:30},{frame:18,x:15,y:189,width:27,height:30}];
const VISUAL_HEAD:K[]=[
{frame:11,x:432,y:181,width:80,height:50},{frame:12,x:350,y:174,width:162,height:56},{frame:14,x:290,y:170,width:222,height:58},{frame:15,x:248,y:169,width:264,height:56},{frame:16,x:217,y:168,width:275,height:56},{frame:17,x:186,y:164,width:276,height:58},{frame:19,x:168,y:160,width:280,height:59},{frame:20,x:156,y:160,width:281,height:57},{frame:25,x:123,y:150,width:288,height:64},{frame:35,x:108,y:150,width:301,height:53},{frame:44,x:106,y:160,width:303,height:38},{frame:46,x:77,y:160,width:301,height:38},{frame:47,x:57,y:160,width:236,height:36},{frame:49,x:50,y:160,width:159,height:35},{frame:50,x:44,y:160,width:66,height:35},{frame:51,x:19,y:160,width:81,height:33}];
const TEXTO_HEAD:K[]=[
{frame:49,x:387,y:160,width:125,height:37},{frame:50,x:320,y:160,width:158,height:36},{frame:51,x:277,y:160,width:228,height:37},{frame:52,x:248,y:160,width:245,height:36},{frame:54,x:225,y:160,width:256,height:37},{frame:55,x:206,y:160,width:255,height:35},{frame:56,x:188,y:160,width:258,height:35},{frame:57,x:174,y:160,width:260,height:35},{frame:60,x:156,y:160,width:259,height:35},{frame:65,x:138,y:160,width:259,height:34},{frame:75,x:137,y:160,width:260,height:34},{frame:90,x:136,y:160,width:261,height:32},{frame:93,x:134,y:160,width:264,height:32}];

export const measuredS14=(frame:number)=>({
 cards:{audio:sample(frame,AUDIO_CARD),visual:sample(frame,VISUAL_CARD),texto:sample(frame,TEXTO_CARD)},
 headings:{audio:sample(frame,AUDIO_HEAD),visual:sample(frame,VISUAL_HEAD),texto:sample(frame,TEXTO_HEAD)},
 semanticState:frame<17?'audio':frame<54?'visual':'texto',
 phase:frame<11?'hold_audio':frame<17?'audio_to_visual':frame<47?'hold_visual':frame<54?'visual_to_texto':'hold_texto'
});
export const S14_MEASURED_AUTHORITY={
 sourceFrames:[561,655],frameCount:94,fps:30,
 authority:'MEASURED_VISIBLE_KEYFRAME_PROJECTION',
 fullTrackDriveId:'19r2Xhl0IYZ6ErgcCFZUrsHbw-08g4FWj',
 caveat:'Keyframes are a renderer projection of the full per-frame Drive evidence. Original AE parenting/camera/font/effect graph remains unknown.'
} as const;
