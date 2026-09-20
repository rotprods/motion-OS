#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,subprocess
from pathlib import Path
from PIL import Image
SAMPLES=(0,10,17,25,46,54,60,75,93)
def run_json(args:list[str])->dict:
 p=subprocess.run(args,check=True,capture_output=True,text=True);return json.loads(p.stdout)
def count_gray_card(im:Image.Image,box:tuple[int,int,int,int])->int:
 c=im.convert('RGB').crop(box);return sum(1 for r,g,b in c.getdata() if max(r,g,b)-min(r,g,b)<70 and 40<max(r,g,b)<220)
def count_heading(im:Image.Image)->int:
 c=im.convert('RGB').crop((0,140,512,250));return sum(1 for r,g,b in c.getdata() if r>150 and g>145 and b>140 and max(r,g,b)-min(r,g,b)<55)
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--video',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--samples-dir',type=Path,required=True);a=ap.parse_args()
 probe=run_json(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(a.video)]);v=next(s for s in probe['streams'] if s['codec_type']=='video');audio=[s for s in probe['streams'] if s['codec_type']=='audio'];frames=int(v.get('nb_read_frames') or v.get('nb_frames') or 0)
 if frames!=94:raise ValueError(f'expected 94 frames, got {frames}')
 if v['width']!=512 or v['height']!=1108:raise ValueError('S14 dimensions mismatch')
 if v['r_frame_rate']!='30/1':raise ValueError(f"expected 30/1 fps, got {v['r_frame_rate']}")
 if not audio:raise ValueError('S14 structural render must preserve modeled audio-accent domain')
 a.samples_dir.mkdir(parents=True,exist_ok=True);checks={}
 for f in SAMPLES:
  path=a.samples_dir/f'frame_{f:03d}.png';subprocess.run(['ffmpeg','-y','-v','error','-i',str(a.video),'-vf',f'select=eq(n\\,{f})','-vframes','1',str(path)],check=True);im=Image.open(path)
  item={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'heading_pixels':count_heading(im),'gray_card_pixels':count_gray_card(im,(20,250,500,850))}
  if item['heading_pixels']<500:raise ValueError(f'heading materially absent at local frame {f}')
  if item['gray_card_pixels']<12000:raise ValueError(f'carousel card materially absent at local frame {f}')
  checks[str(f)]=item
 ev={'schema_version':'motion-os.golden-s14-render-evidence/v1','video_sha256':hashlib.sha256(a.video.read_bytes()).hexdigest(),'frame_count':frames,'fps':30,'width':512,'height':1108,'audio_streams':len(audio),'samples':checks,'authority':'STRUCTURAL_RENDER_EXECUTED','source_fidelity_authority':'BLOCKED_UNTIL_SOURCE_BOUND_DIFF'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(ev,indent=2,sort_keys=True)+'\n');return 0
if __name__=='__main__':raise SystemExit(main())
