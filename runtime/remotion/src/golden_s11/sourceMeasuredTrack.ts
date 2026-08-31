export type S11MeasuredBox = {
  x: number;
  y: number;
  width: number;
  height: number;
};

type KF = S11MeasuredBox & {frame:number};

const lerp=(a:number,b:number,t:number)=>a+(b-a)*t;
const sample=(frame:number,track:KF[]):S11MeasuredBox|null=>{
  if(frame<track[0].frame||frame>track[track.length-1].frame)return null;
  const exact=track.find(k=>k.frame===frame);
  if(exact)return exact;
  const ri=track.findIndex(k=>k.frame>frame);
  const l=track[ri-1],r=track[ri];
  const t=(frame-l.frame)/(r.frame-l.frame);
  return {x:lerp(l.x,r.x,t),y:lerp(l.y,r.y,t),width:lerp(l.width,r.width,t),height:lerp(l.height,r.height,t)};
};

const PILL:KF[]=[
  {frame:0,x:98,y:530,width:336,height:32},{frame:8,x:94,y:498,width:344,height:97},{frame:16,x:84,y:496,width:362,height:104},{frame:31,x:76,y:494,width:380,height:109},{frame:41,x:70,y:492,width:392,height:113},{frame:54,x:64,y:490,width:402,height:118},{frame:62,x:62,y:490,width:408,height:118},{frame:70,x:58,y:476,width:414,height:120},{frame:73,x:58,y:458,width:414,height:120},{frame:75,x:58,y:450,width:416,height:121},{frame:78,x:56,y:422,width:418,height:121},{frame:80,x:56,y:414,width:418,height:121},{frame:82,x:56,y:400,width:420,height:122},{frame:85,x:54,y:388,width:422,height:122},{frame:90,x:52,y:372,width:426,height:123},{frame:93,x:52,y:363,width:426,height:125},{frame:99,x:50,y:354,width:430,height:124},{frame:102,x:50,y:349,width:432,height:126},{frame:110,x:46,y:342,width:438,height:127},{frame:120,x:44,y:324,width:444,height:140},{frame:129,x:42,y:322,width:448,height:141},
];

const HOOK:KF[]=[
  {frame:8,x:112,y:510,width:77,height:76},{frame:16,x:106,y:511,width:76,height:76},{frame:31,x:98,y:510,width:81,height:80},{frame:41,x:93,y:509,width:83,height:83},{frame:54,x:88,y:508,width:86,height:86},{frame:62,x:85,y:507,width:87,height:87},{frame:70,x:83,y:495,width:88,height:87},{frame:73,x:82,y:476,width:89,height:89},{frame:75,x:82,y:468,width:89,height:88},{frame:78,x:81,y:440,width:89,height:88},{frame:80,x:81,y:432,width:89,height:88},{frame:82,x:80,y:419,width:90,height:89},{frame:85,x:80,y:406,width:89,height:89},{frame:90,x:78,y:391,width:91,height:90},{frame:93,x:77,y:383,width:91,height:90},{frame:99,x:76,y:374,width:91,height:90},{frame:102,x:75,y:369,width:92,height:91},{frame:110,x:73,y:362,width:93,height:92},{frame:120,x:70,y:355,width:94,height:94},{frame:129,x:68,y:352,width:95,height:95},
];

const ABS:KF[]=[
  {frame:54,x:190,y:424,width:212,height:30},{frame:62,x:189,y:422,width:215,height:30},{frame:70,x:188,y:410,width:218,height:31},{frame:73,x:188,y:394,width:218,height:32},{frame:75,x:188,y:386,width:218,height:32},{frame:78,x:187,y:362,width:220,height:31},{frame:80,x:187,y:355,width:220,height:31},{frame:82,x:187,y:343,width:221,height:32},{frame:85,x:186,y:332,width:222,height:32},{frame:90,x:186,y:319,width:223,height:32},{frame:93,x:186,y:311,width:224,height:33},{frame:99,x:186,y:302,width:225,height:33},{frame:102,x:184,y:298,width:228,height:32},{frame:110,x:184,y:291,width:229,height:33},{frame:120,x:182,y:284,width:233,height:33},{frame:129,x:182,y:280,width:235,height:34},
];

const XROW:KF[]=[
  {frame:77,x:108,y:585,width:38,height:38},{frame:78,x:96,y:565,width:62,height:61},{frame:80,x:90,y:551,width:74,height:74},{frame:82,x:82,y:532,width:88,height:87},{frame:85,x:80,y:518,width:91,height:90},{frame:90,x:82,y:507,width:86,height:85},{frame:93,x:81,y:500,width:86,height:84},{frame:99,x:78,y:490,width:89,height:88},{frame:102,x:78,y:486,width:88,height:88},{frame:110,x:76,y:480,width:89,height:88},{frame:120,x:74,y:475,width:90,height:90},{frame:129,x:71,y:474,width:92,height:90},
];
const DROW:KF[]=[
  {frame:82,x:106,y:686,width:39,height:38},{frame:85,x:86,y:655,width:79,height:77},{frame:90,x:79,y:636,width:91,height:90},{frame:93,x:80,y:631,width:88,height:86},{frame:99,x:80,y:624,width:86,height:86},{frame:102,x:78,y:620,width:88,height:87},{frame:110,x:76,y:615,width:89,height:88},{frame:120,x:74,y:612,width:90,height:90},{frame:129,x:71,y:612,width:92,height:91},
];
const MROW:KF[]=[
  {frame:88,x:98,y:788,width:61,height:46},{frame:90,x:94,y:780,width:70,height:52},{frame:93,x:86,y:768,width:83,height:64},{frame:99,x:84,y:764,width:82,height:64},{frame:102,x:84,y:762,width:81,height:68},{frame:110,x:80,y:757,width:85,height:71},{frame:120,x:78,y:756,width:85,height:72},{frame:129,x:77,y:758,width:85,height:71},
];

export const measuredS11=(frame:number)=>({
  pill:sample(frame,PILL), hook:sample(frame,HOOK), absolute:sample(frame,ABS),
  xRow:sample(frame,XROW), diamondRow:sample(frame,DROW), megaphoneRow:sample(frame,MROW),
});

export const S11_SOURCE_MEASURED_TRACK_SUMMARY={
  authority:'MEASURED_SOURCE_VISIBLE_HEURISTIC',
  method:'decoded_source_color_components_and_neutral_dark_component_tracking',
  sourceFrames:[405,534],
  rowFirstVisible:{x:77,diamond:82,megaphone:88},
  caveat:'visible output geometry only; does not prove original AE parenting, fonts, curves or layer topology',
} as const;
