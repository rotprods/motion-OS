#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,subprocess
from pathlib import Path
from PIL import Image
SAMPLES=(0,5,10,19,23,54,86,89,91)
def run_json(args:list[str])->dict:
 p=subprocess.run(args,check=True,capture_output=True,text=True);return json.loads(p.stdout)
def white_count(im:Image.Image,box:tuple[int,int,int,int])->int:
 c=im.convert('RGB').crop(box);return sum(1 for r,g,b in c.getdata() if r>145 and g>140 and b>135 and max(r,g,b)-min(r,g,b)<75)
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--video',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--samples-dir',type=Path,required=True);a=ap.parse_args()
 probe=run_json(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(a.video)]);v=next(s for s in probe['streams'] if s['codec_type']=='video');audio=[s for s in probe['streams'] if s['codec_type']=='audio'];frames=int(v.get('nb_read_frames') or v.get('nb_frames') or 0)
 if frames!=92:raise ValueError(f'expected 92 frames, got {frames}')
 if (v['width'],v['height'])!=(512,1108):raise ValueError('S16 dimensions mismatch')
 if v['r_frame_rate']!='30/1':raise ValueError(f"expected 30/1 fps, got {v['r_frame_rate']}")
 if not audio:raise ValueError('S16 structural render must preserve modeled audio domain')
 a.samples_dir.mkdir(parents=True,exist_ok=True);checks={}
 for f in SAMPLES:
  path=a.samples_dir/f'frame_{f:03d}.png';subprocess.run(['ffmpeg','-y','-v','error','-i',str(a.video),'-vf',f'select=eq(n\\,{f})','-vframes','1',str(path)],check=True);im=Image.open(path)
  checks[str(f)]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'payoff_white_pixels':white_count(im,(80,680,480,900)),'source_ui_white_pixels':white_count(im,(430,300,512,950))}
 if checks['54']['payoff_white_pixels']<1000:raise ValueError('Factor X payoff materially absent at calm hold start')
 if checks['89']['source_ui_white_pixels']<=checks['86']['source_ui_white_pixels']:raise ValueError('source-lock UI reveal not observable after local87')
 ev={'schema_version':'motion-os.golden-s16-render-evidence/v1','video_sha256':hashlib.sha256(a.video.read_bytes()).hexdigest(),'frame_count':frames,'fps':30,'width':512,'height':1108,'audio_streams':len(audio),'samples':checks,'authority':'STRUCTURAL_RENDER_EXECUTED','source_fidelity_authority':'BLOCKED_UNTIL_SOURCE_BOUND_DIFF'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(ev,indent=2,sort_keys=True)+'\n');return 0
if __name__=='__main__':raise SystemExit(main())
