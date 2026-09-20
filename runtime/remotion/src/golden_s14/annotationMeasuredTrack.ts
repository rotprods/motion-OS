import type {Box} from './sourceMeasuredTrack';

type K=Box&{frame:number};
const lerp=(a:number,b:number,t:number)=>a+(b-a)*t;
const sample=(frame:number,track:K[]):Box|null=>{
  if(frame<track[0].frame||frame>track[track.length-1].frame)return null;
  const exact=track.find(k=>k.frame===frame);if(exact)return exact;
  const r=track.findIndex(k=>k.frame>frame);const a=track[r-1],b=track[r];const t=(frame-a.frame)/(b.frame-a.frame);
  return {x:lerp(a.x,b.x,t),y:lerp(a.y,b.y,t),width:lerp(a.width,b.width,t),height:lerp(a.height,b.height,t),opacity:1};
};

// Source-visible annotation bounding boxes. These tracks describe physical
// output geometry only; they are NOT the original AE vector paths/strokes.
const AUDIO:K[]=[
{frame:0,x:146,y:484,width:234,height:86},{frame:1,x:144,y:472,width:240,height:112},{frame:2,x:140,y:506,width:246,height:42},{frame:3,x:140,y:506,width:246,height:42},{frame:4,x:138,y:488,width:250,height:76},{frame:5,x:136,y:512,width:256,height:30},{frame:7,x:132,y:504,width:262,height:45},{frame:8,x:132,y:504,width:262,height:45},{frame:9,x:122,y:508,width:266,height:38},{frame:10,x:98,y:520,width:266,height:10},{frame:11,x:15,y:477,width:293,height:134},{frame:12,x:17,y:520,width:209,height:10},{frame:13,x:17,y:520,width:209,height:10},{frame:14,x:51,y:524,width:111,height:6},{frame:15,x:16,y:524,width:104,height:4},{frame:16,x:58,y:524,width:53,height:91},{frame:17,x:48,y:479,width:29,height:111},{frame:18,x:48,y:479,width:29,height:111}];
const VISUAL:K[]=[
{frame:11,x:423,y:362,width:88,height:164},{frame:12,x:341,y:356,width:170,height:180},{frame:13,x:341,y:356,width:170,height:180},{frame:14,x:279,y:354,width:232,height:184},{frame:15,x:237,y:353,width:274,height:185},{frame:16,x:206,y:352,width:305,height:186},{frame:17,x:173,y:350,width:311,height:188},{frame:18,x:173,y:350,width:311,height:188},{frame:19,x:156,y:349,width:314,height:189},{frame:21,x:132,y:347,width:317,height:191},{frame:22,x:124,y:346,width:318,height:192},{frame:23,x:124,y:346,width:318,height:192},{frame:25,x:112,y:344,width:321,height:194},{frame:27,x:104,y:343,width:324,height:197},{frame:31,x:100,y:342,width:328,height:198},{frame:35,x:100,y:340,width:330,height:200},{frame:40,x:98,y:338,width:334,height:202},{frame:44,x:96,y:336,width:336,height:204},{frame:45,x:88,y:336,width:336,height:204},{frame:46,x:68,y:336,width:336,height:204},{frame:47,x:16,y:336,width:306,height:204},{frame:48,x:16,y:336,width:306,height:204},{frame:49,x:16,y:336,width:222,height:204},{frame:50,x:16,y:336,width:158,height:202},{frame:51,x:16,y:336,width:114,height:198},{frame:52,x:16,y:344,width:80,height:180},{frame:53,x:16,y:344,width:80,height:180},{frame:54,x:16,y:354,width:56,height:160}];
const TEXTO:K[]=[
{frame:47,x:452,y:284,width:32,height:52},{frame:49,x:366,y:276,width:96,height:95},{frame:50,x:304,y:272,width:154,height:110},{frame:51,x:260,y:272,width:188,height:110},{frame:52,x:228,y:270,width:236,height:112},{frame:53,x:228,y:270,width:236,height:112},{frame:54,x:202,y:270,width:280,height:112},{frame:55,x:182,y:270,width:278,height:112},{frame:56,x:168,y:270,width:290,height:112},{frame:57,x:154,y:270,width:298,height:112},{frame:58,x:154,y:270,width:298,height:112},{frame:59,x:142,y:268,width:300,height:114},{frame:60,x:134,y:272,width:300,height:110},{frame:62,x:120,y:270,width:302,height:112},{frame:65,x:116,y:270,width:300,height:112},{frame:66,x:114,y:280,width:300,height:102},{frame:69,x:112,y:278,width:302,height:104},{frame:71,x:114,y:276,width:300,height:106},{frame:74,x:112,y:276,width:302,height:106},{frame:75,x:112,y:272,width:302,height:110},{frame:78,x:112,y:269,width:302,height:113},{frame:81,x:112,y:270,width:304,height:110},{frame:83,x:112,y:270,width:302,height:112},{frame:84,x:112,y:270,width:304,height:110},{frame:85,x:112,y:270,width:302,height:110},{frame:88,x:112,y:268,width:304,height:112},{frame:89,x:112,y:270,width:304,height:110},{frame:90,x:112,y:268,width:304,height:112},{frame:91,x:112,y:272,width:304,height:108},{frame:92,x:112,y:268,width:304,height:112},{frame:93,x:112,y:268,width:304,height:112}];

export const measuredS14Annotation=(frame:number)=>({audio:sample(frame,AUDIO),visual:sample(frame,VISUAL),texto:sample(frame,TEXTO)});
export const S14_ANNOTATION_TRACK_AUTHORITY={
  authority:'MEASURED_VISIBLE_BBOX_PROXY_NOT_EXACT_VECTOR_PATH',
  fullTrackDriveId:'1VYdmrkBHIa3SlytJg36ZDTJua3icx55D',
  sourceSha256:'9b3076cb542e358386942a0fb6b160f1345564d4326738f9a340e2b5b38e199d',
  caveat:'Screen-space bbox trajectory is measured. Original Bézier topology, stroke construction and hidden mattes remain UNKNOWN.'
} as const;
