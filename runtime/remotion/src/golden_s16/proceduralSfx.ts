const writeAscii=(view:DataView,offset:number,value:string)=>{for(let i=0;i<value.length;i++)view.setUint8(offset+i,value.charCodeAt(i));};
const bytesToBase64=(bytes:Uint8Array):string=>{let binary='';const chunk=0x4000;for(let o=0;o<bytes.length;o+=chunk){const c=bytes.subarray(o,Math.min(bytes.length,o+chunk));for(let i=0;i<c.length;i++)binary+=String.fromCharCode(c[i]);}return globalThis.btoa(binary);};
/** Deterministic structural impact. Timing can be qualified; timbre is never source-SFX authority. */
export const makeS16Hit=(seedInput:number,pitchHz=420):string=>{
 const sampleRate=44100,duration=.15,count=Math.round(sampleRate*duration),dataSize=count*2,buffer=new ArrayBuffer(44+dataSize),view=new DataView(buffer);
 writeAscii(view,0,'RIFF');view.setUint32(4,36+dataSize,true);writeAscii(view,8,'WAVE');writeAscii(view,12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,sampleRate,true);view.setUint32(28,sampleRate*2,true);view.setUint16(32,2,true);view.setUint16(34,16,true);writeAscii(view,36,'data');view.setUint32(40,dataSize,true);
 let seed=seedInput>>>0;const noise=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return(seed/0xffffffff)*2-1;};
 for(let i=0;i<count;i++){const t=i/sampleRate;const click=noise()*Math.exp(-80*t)*.16;const tone=Math.sin(2*Math.PI*pitchHz*t)*Math.exp(-29*t)*.28;const low=Math.sin(2*Math.PI*72*t)*Math.exp(-19*t)*.22;const s=Math.max(-1,Math.min(1,click+tone+low));view.setInt16(44+i*2,Math.round(s*32767),true);}
 return`data:audio/wav;base64,${bytesToBase64(new Uint8Array(buffer))}`;
};
