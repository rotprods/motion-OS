export type S16Box={x:number;y:number;width:number;height:number};
type K=S16Box&{frame:number};
type KF=K&{relativeLuma:number};
const lerp=(a:number,b:number,t:number)=>a+(b-a)*t;
const sample=(frame:number,track:K[]):S16Box|null=>{
 if(frame<track[0].frame||frame>track[track.length-1].frame)return null;
 const exact=track.find(k=>k.frame===frame);if(exact)return exact;
 const r=track.findIndex(k=>k.frame>frame),a=track[r-1],b=track[r],t=(frame-a.frame)/(b.frame-a.frame);
 return{x:lerp(a.x,b.x,t),y:lerp(a.y,b.y,t),width:lerp(a.width,b.width,t),height:lerp(a.height,b.height,t)};
};
const sampleFactor=(frame:number,track:KF[]):(S16Box&{relativeLuma:number})|null=>{
 if(frame<track[0].frame||frame>track[track.length-1].frame)return null;
 const exact=track.find(k=>k.frame===frame);if(exact)return exact;
 const r=track.findIndex(k=>k.frame>frame),a=track[r-1],b=track[r],t=(frame-a.frame)/(b.frame-a.frame);
 return{x:lerp(a.x,b.x,t),y:lerp(a.y,b.y,t),width:lerp(a.width,b.width,t),height:lerp(a.height,b.height,t),relativeLuma:lerp(a.relativeLuma,b.relativeLuma,t)};
};

// Visible screen-space column bbox. Full structural asset is 230×224 and is
// bottom-clipped by the source viewport during entrance; opacity remains inferred.
const COLUMN:K[]=[
 {frame:2,x:30,y:858,width:230,height:156},{frame:3,x:30,y:846,width:230,height:168},{frame:4,x:30,y:836,width:230,height:178},{frame:5,x:30,y:828,width:230,height:186},{frame:7,x:30,y:821,width:230,height:193},{frame:8,x:30,y:816,width:230,height:198},{frame:9,x:30,y:811,width:230,height:203},{frame:10,x:30,y:807,width:230,height:207},{frame:12,x:30,y:804,width:230,height:210},{frame:13,x:30,y:802,width:230,height:212},{frame:14,x:30,y:800,width:230,height:214},{frame:15,x:30,y:798,width:230,height:216},{frame:17,x:30,y:796,width:230,height:218},{frame:18,x:30,y:795,width:230,height:219},{frame:19,x:30,y:794,width:230,height:220},{frame:20,x:30,y:793,width:230,height:221},{frame:23,x:30,y:792,width:230,height:222},{frame:25,x:30,y:791,width:230,height:223},{frame:33,x:30,y:790,width:230,height:224},{frame:86,x:30,y:789,width:230,height:225},{frame:87,x:30,y:786,width:230,height:228},{frame:88,x:30,y:782,width:230,height:232},{frame:89,x:30,y:778,width:230,height:236},{frame:90,x:30,y:775,width:230,height:239},{frame:91,x:30,y:773,width:230,height:241}
];

const QUESTION:K[]=[
 {frame:9,x:132,y:652,width:46,height:70},{frame:10,x:106,y:643,width:74,height:145},{frame:11,x:106,y:635,width:74,height:157},{frame:12,x:106,y:630,width:74,height:159},{frame:13,x:106,y:625,width:74,height:163},{frame:14,x:106,y:621,width:74,height:163},{frame:16,x:106,y:616,width:74,height:169},{frame:17,x:106,y:613,width:74,height:172},{frame:18,x:106,y:611,width:74,height:174},{frame:19,x:106,y:609,width:74,height:176},{frame:20,x:106,y:607,width:74,height:178},{frame:21,x:106,y:607,width:74,height:180},{frame:22,x:106,y:606,width:74,height:181},{frame:25,x:106,y:605,width:74,height:183},{frame:30,x:106,y:604,width:74,height:184},{frame:35,x:106,y:604,width:74,height:185},{frame:44,x:106,y:604,width:74,height:186},{frame:86,x:106,y:602,width:74,height:186},{frame:87,x:106,y:598,width:74,height:187},{frame:88,x:106,y:594,width:74,height:186},{frame:89,x:106,y:588,width:74,height:186},{frame:90,x:106,y:584,width:74,height:185},{frame:91,x:106,y:582,width:74,height:186}
];

const FACTOR:KF[]=[
 {frame:19,x:136,y:969,width:315,height:45,relativeLuma:.488},{frame:20,x:136,y:925,width:315,height:62,relativeLuma:.551},{frame:22,x:136,y:889,width:315,height:62,relativeLuma:.622},{frame:23,x:136,y:859,width:315,height:62,relativeLuma:.676},{frame:24,x:136,y:835,width:315,height:62,relativeLuma:.735},{frame:25,x:136,y:815,width:315,height:62,relativeLuma:.774},{frame:27,x:136,y:798,width:315,height:62,relativeLuma:.858},{frame:28,x:136,y:784,width:315,height:62,relativeLuma:.884},{frame:29,x:136,y:774,width:315,height:62,relativeLuma:.903},{frame:30,x:136,y:764,width:315,height:62,relativeLuma:.915},{frame:31,x:136,y:758,width:315,height:62,relativeLuma:.949},{frame:32,x:136,y:753,width:315,height:62,relativeLuma:.951},{frame:35,x:136,y:742,width:315,height:62,relativeLuma:.976},{frame:36,x:136,y:739,width:315,height:62,relativeLuma:.993},{frame:38,x:136,y:735,width:315,height:62,relativeLuma:1.005},{frame:40,x:136,y:731,width:315,height:62,relativeLuma:1.010},{frame:41,x:136,y:729,width:315,height:62,relativeLuma:1.022},{frame:42,x:136,y:728,width:315,height:62,relativeLuma:1.005},{frame:43,x:136,y:727,width:315,height:62,relativeLuma:1.000},{frame:45,x:136,y:725,width:315,height:62,relativeLuma:1.000},{frame:47,x:136,y:724,width:315,height:62,relativeLuma:1.010},{frame:48,x:136,y:723,width:315,height:62,relativeLuma:1.002},{frame:51,x:136,y:722,width:315,height:62,relativeLuma:1.007},{frame:54,x:136,y:721,width:315,height:62,relativeLuma:1.007},{frame:86,x:136,y:720,width:315,height:62,relativeLuma:1.005},{frame:87,x:136,y:716,width:315,height:62,relativeLuma:1.010},{frame:88,x:136,y:712,width:315,height:62,relativeLuma:1.002},{frame:89,x:136,y:708,width:315,height:62,relativeLuma:1.010},{frame:90,x:136,y:704,width:315,height:62,relativeLuma:1.005},{frame:91,x:136,y:702,width:315,height:62,relativeLuma:1.002}
];

export const measuredS16=(frame:number)=>({
 column:sample(frame,COLUMN),
 questionMark:sample(frame,QUESTION),
 factorX:sampleFactor(frame,FACTOR),
 sourceUiReveal:frame>=87,
 phase:frame<2?'subject_only':frame<9?'column_entry':frame<19?'question_entry':frame<54?'factor_payoff_motion':frame<87?'calm_hold':'source_ui_reflow',
});

export const S16_MEASURED_AUTHORITY={
 authority:'MEASURED_SOURCE_BOUND_PROJECTION_V1',
 fullTrackDriveId:'178eElG7KSsUILKpmIijqaiHiBLculKeO',
 cameraReportV2DriveId:'1UttMAqDNpGsMPvAe5l7iuinBtpG1PjUu',
 caveats:{columnOpacity:'EVIDENCE_BOUND_INFERENCE',factorOpacity:'VISIBLE_LUMA_PROXY_NOT_ALPHA',factorFont:'UNKNOWN',questionAsset:'UNKNOWN',local87PlusReflowCause:'UNKNOWN_SOURCE_LOCK_BY_DEFAULT'},
} as const;
