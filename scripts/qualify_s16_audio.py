#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,subprocess,tempfile,wave
from array import array
from pathlib import Path
FPS=30.0
REQUIRED=[0.37,4.64,9.73,14.44,20.95,23.20,36.37]

def pcm(path:Path):
 with wave.open(str(path),'rb') as w:
  if w.getsampwidth()!=2:raise ValueError('PCM16 required')
  sr=w.getframerate();ch=w.getnchannels();raw=w.readframes(w.getnframes())
 a=array('h');a.frombytes(raw);mono=[sum(a[i:i+ch])/ch for i in range(0,len(a),ch)] if ch>1 else list(a);return sr,mono

def scores(path:Path,block_ms=2.5):
 sr,s=pcm(path);block=max(8,int(sr*block_ms/1000));out=[]
 for st in range(0,len(s)-block+1,block):
  seg=s[st:st+block];ss=sum((((seg[i]-seg[i-1])/32768.0)**2) for i in range(1,len(seg)));out.append((st/sr,math.sqrt(ss/max(1,len(seg)-1))))
 return out

def peak_near(sc,frame,radius=1.4):
 c=frame/FPS;r=radius/FPS;cand=[x for x in sc if c-r<=x[0]<=c+r];return max(cand,key=lambda x:x[1]) if cand else None

def extract(video:Path,dst:Path):subprocess.run(['ffmpeg','-y','-v','error','-i',str(video),'-vn','-ac','1','-ar','44100','-c:a','pcm_s16le',str(dst)],check=True)

def qualify(render:Path,contract:dict,gate:float):
 events=[float(x['local_frame']) for x in contract['audio_transient_proxies']]
 if len(events)!=len(REQUIRED) or any(abs(a-b)>.02 for a,b in zip(events,REQUIRED)):raise ValueError('S16 canonical transient proxies changed unexpectedly')
 with tempfile.TemporaryDirectory() as td:
  wav=Path(td)/'render.wav';extract(render,wav);sc=scores(wav);rows=[]
  for src in REQUIRED:
   p=peak_near(sc,src);rf=None if p is None else p[0]*FPS;rows.append({'source_peak_frame':src,'render_peak_frame':rf,'error_frames':None if rf is None else rf-src,'render_transient_score':None if p is None else p[1]})
 errs=[abs(r['error_frames']) for r in rows if r['error_frames'] is not None];passed=len(errs)==len(REQUIRED) and max(errs)<=gate
 return {'schema_version':'motion-os.s16-audio-onset-qualification/v1','scene_id':'S16_FACTOR_X','authority':'MEASURED_RENDERED_TRANSIENT_PEAK_VS_MEASURED_SOURCE_MIX_PROXY','events':rows,'mean_absolute_error_frames':sum(errs)/len(errs) if errs else None,'max_absolute_error_frames':max(errs) if errs else None,'gate_frames':gate,'onset_peak_gate_pass':passed,'full_audio_fidelity_validated':False,'unknowns':['isolated source SFX stems','source SFX identity/timbre','exact source transient envelope','music/voice/SFX source decomposition']}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--render-video',type=Path,required=True);ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--gate-frames',type=float,default=1.5);a=ap.parse_args();out=qualify(a.render_video,json.loads(a.contract.read_text()),a.gate_frames);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'mean':out['mean_absolute_error_frames'],'max':out['max_absolute_error_frames'],'pass':out['onset_peak_gate_pass']},indent=2));return 0 if out['onset_peak_gate_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
