export type Box={x:number;y:number;width:number;height:number;opacity?:number};
type K=Box&{frame:number};
const lerp=(a:number,b:number,t:number)=>a+(b-a)*t;
const sample=(frame:number,track:K[]):Box|null=>{
  if(frame<track[0].frame||frame>track[track.length-1].frame)return null;
  const exact=track.find(k=>k.frame===frame);if(exact)return exact;
  const r=track.findIndex(k=>k.frame>frame);const a=track[r-1],b=track[r];const t=(frame-a.frame)/(b.frame-a.frame);
  return {x:lerp(a.x,b.x,t),y:lerp(a.y,b.y,t),width:lerp(a.width,b.width,t),height:lerp(a.height,b.height,t),opacity:lerp(a.opacity??1,b.opacity??1,t)};
};

// Screen-space cards. Extra keys around nonlinear transition windows are
// intentionally retained; compression into only semantic impact frames lost
// measurable trajectory and caused the first S14 fidelity defects.
const AUDIO_CARD:K[]=[
{frame:0,x:135,y:261,width:260,height:502},{frame:1,x:131,y:261,width:269,height:508},{frame:2,x:127,y:287,width:278,height:490},{frame:3,x:127,y:287,width:278,height:490},{frame:4,x:125,y:283,width:287,height:498},{frame:5,x:123,y:279,width:292,height:506},{frame:6,x:121,y:275,width:296,height:514},{frame:7,x:117,y:271,width:302,height:520},{frame:8,x:117,y:271,width:302,height:520},{frame:9,x:108,y:269,width:299,height:526},{frame:10,x:83,y:265,width:303,height:532},{frame:11,x:0,y:263,width:329,height:536},{frame:12,x:0,y:261,width:247,height:542},{frame:13,x:0,y:261,width:247,height:542},{frame:14,x:0,y:261,width:189,height:544},{frame:15,x:0,y:261,width:146,height:544},{frame:16,x:0,y:261,width:115,height:546},{frame:17,x:0,y:261,width:81,height:546},{frame:18,x:0,y:261,width:81,height:546}];
const VISUAL_CARD:K[]=[
{frame:11,x:422,y:273,width:90,height:532},{frame:12,x:340,y:269,width:172,height:538},{frame:13,x:340,y:269,width:172,height:538},{frame:14,x:278,y:265,width:234,height:542},{frame:15,x:236,y:261,width:276,height:548},{frame:16,x:205,y:261,width:307,height:548},{frame:17,x:172,y:261,width:315,height:550},{frame:18,x:172,y:261,width:315,height:550},{frame:19,x:155,y:261,width:318,height:552},{frame:20,x:143,y:261,width:318,height:556},{frame:22,x:123,y:261,width:322,height:556},{frame:25,x:111,y:261,width:326,height:558},{frame:27,x:103,y:261,width:328,height:560},{frame:28,x:103,y:261,width:328,height:560},{frame:29,x:101,y:261,width:330,height:560},{frame:30,x:101,y:261,width:330,height:562},{frame:31,x:99,y:261,width:332,height:562},{frame:32,x:99,y:261,width:332,height:564},{frame:35,x:99,y:261,width:334,height:566},{frame:44,x:95,y:261,width:340,height:570},{frame:45,x:87,y:261,width:340,height:570},{frame:46,x:67,y:261,width:340,height:572},{frame:47,x:0,y:261,width:323,height:572},{frame:48,x:0,y:261,width:323,height:572},{frame:49,x:0,y:261,width:239,height:572},{frame:50,x:0,y:261,width:185,height:572},{frame:51,x:0,y:261,width:132,height:572},{frame:52,x:0,y:261,width:108,height:572},{frame:53,x:0,y:261,width:108,height:572},{frame:54,x:0,y:261,width:75,height:572}];
const TEXTO_CARD:K[]=[
{frame:47,x:431,y:261,width:81,height:566},{frame:48,x:431,y:261,width:81,height:564},{frame:49,x:346,y:261,width:166,height:568},{frame:50,x:283,y:261,width:229,height:566},{frame:51,x:239,y:261,width:273,height:568},{frame:52,x:207,y:261,width:305,height:568},{frame:53,x:207,y:261,width:305,height:568},{frame:54,x:182,y:261,width:330,height:570},{frame:55,x:162,y:261,width:350,height:570},{frame:56,x:147,y:261,width:365,height:570},{frame:57,x:134,y:261,width:378,height:570},{frame:60,x:115,y:261,width:354,height:570},{frame:61,x:109,y:261,width:354,height:570},{frame:62,x:101,y:261,width:354,height:570},{frame:65,x:95,y:261,width:354,height:570},{frame:75,x:93,y:261,width:356,height:572},{frame:90,x:91,y:261,width:358,height:576},{frame:93,x:91,y:261,width:358,height:576}];

// Heading boxes are visible-output bounds, not font metrics. v2 corrects a
// tracker identity swap during the visual->texto crossing at local 52..56.
const AUDIO_HEAD:K[]=[
{frame:0,x:155,y:226,width:213,height:49},{frame:2,x:150,y:210,width:225,height:50},{frame:6,x:144,y:194,width:238,height:52},{frame:10,x:108,y:182,width:245,height:54},{frame:11,x:50,y:179,width:249,height:54},{frame:12,x:19,y:176,width:196,height:53},{frame:14,x:15,y:175,width:138,height:52},{frame:15,x:15,y:185,width:94,height:40},{frame:16,x:16,y:185,width:62,height:36},{frame:17,x:15,y:189,width:27,height:30},{frame:18,x:15,y:189,width:27,height:30}];
const VISUAL_HEAD:K[]=[
{frame:11,x:432,y:181,width:80,height:50},{frame:12,x:350,y:174,width:162,height:56},{frame:13,x:350,y:174,width:162,height:56},{frame:14,x:290,y:170,width:222,height:58},{frame:15,x:248,y:169,width:264,height:56},{frame:16,x:217,y:168,width:275,height:56},{frame:17,x:186,y:164,width:276,height:58},{frame:18,x:186,y:164,width:276,height:58},{frame:19,x:168,y:160,width:280,height:59},{frame:20,x:156,y:158,width:281,height:59},{frame:22,x:136,y:154,width:285,height:62},{frame:25,x:123,y:150,width:288,height:64},{frame:27,x:115,y:150,width:292,height:61},{frame:28,x:115,y:150,width:292,height:61},{frame:29,x:112,y:150,width:294,height:60},{frame:30,x:112,y:150,width:295,height:59},{frame:31,x:110,y:150,width:297,height:58},{frame:32,x:109,y:150,width:299,height:56},{frame:35,x:108,y:150,width:301,height:53},{frame:44,x:104,y:150,width:305,height:48},{frame:45,x:97,y:150,width:304,height:47},{frame:46,x:77,y:150,width:301,height:48},{frame:47,x:57,y:150,width:236,height:46},{frame:48,x:57,y:150,width:236,height:46},{frame:49,x:50,y:150,width:159,height:45},{frame:50,x:44,y:151,width:66,height:44},{frame:51,x:19,y:151,width:81,height:42}];
const TEXTO_HEAD:K[]=[
{frame:49,x:384,y:150,width:128,height:47},{frame:50,x:320,y:150,width:170,height:46},{frame:51,x:276,y:150,width:229,height:47},{frame:52,x:245,y:150,width:248,height:46},{frame:53,x:245,y:150,width:248,height:46},{frame:54,x:220,y:150,width:261,height:47},{frame:55,x:200,y:150,width:261,height:45},{frame:56,x:185,y:150,width:261,height:45},{frame:57,x:172,y:150,width:262,height:45},{frame:60,x:154,y:150,width:261,height:45},{frame:61,x:148,y:150,width:260,height:45},{frame:62,x:142,y:150,width:260,height:44},{frame:65,x:138,y:150,width:259,height:44},{frame:75,x:137,y:150,width:260,height:44},{frame:90,x:136,y:150,width:261,height:42},{frame:93,x:134,y:150,width:264,height:42}];

export const measuredS14=(frame:number)=>({
 cards:{audio:sample(frame,AUDIO_CARD),visual:sample(frame,VISUAL_CARD),texto:sample(frame,TEXTO_CARD)},
 headings:{audio:sample(frame,AUDIO_HEAD),visual:sample(frame,VISUAL_HEAD),texto:sample(frame,TEXTO_HEAD)},
 semanticState:frame<17?'audio':frame<54?'visual':'texto',
 phase:frame<11?'hold_audio':frame<17?'audio_to_visual':frame<47?'hold_visual':frame<54?'visual_to_texto':'hold_texto'
});
export const S14_MEASURED_AUTHORITY={
 sourceFrames:[561,655],frameCount:94,fps:30,
 authority:'MEASURED_VISIBLE_KEYFRAME_PROJECTION_V2',
 fullTrackV1DriveId:'19r2Xhl0IYZ6ErgcCFZUrsHbw-08g4FWj',
 fullTrackV2DriveId:'1VFgmwZaJdnDaRRJ8Lz-GiwUUPiKDcPum',
 correction:'S14-MEAS-CORR-001: visual/texto heading identity swap adjudicated at local 52..56',
 caveat:'Keyframes are a renderer projection of versioned per-frame Drive evidence. Original AE parenting/camera/font/effect graph remains unknown.'
} as const;
