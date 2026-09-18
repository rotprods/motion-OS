#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image

SAMPLES=(0,8,16,54,73,85,93,102,129)


def run_json(args:list[str])->dict:
    proc=subprocess.run(args,check=True,capture_output=True,text=True)
    return json.loads(proc.stdout)


def white_count(image:Image.Image, box:tuple[int,int,int,int])->int:
    crop=image.convert('RGB').crop(box)
    return sum(1 for r,g,b in crop.getdata() if r>190 and g>190 and b>185)


def dark_count(image:Image.Image, box:tuple[int,int,int,int])->int:
    crop=image.convert('RGB').crop(box)
    return sum(1 for r,g,b in crop.getdata() if r<65 and g<65 and b<65)


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--video',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--samples-dir',type=Path,required=True)
    args=parser.parse_args()

    probe=run_json(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(args.video)])
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    audio=[s for s in probe['streams'] if s['codec_type']=='audio']
    frames=int(video.get('nb_read_frames') or video.get('nb_frames') or 0)
    if frames!=130: raise ValueError(f'expected 130 frames, got {frames}')
    if video['width']!=512 or video['height']!=1108: raise ValueError('S11 dimensions mismatch')
    if video['r_frame_rate']!='30/1': raise ValueError(f"expected 30/1 fps, got {video['r_frame_rate']}")
    if not audio: raise ValueError('S11 structural fixture must preserve the modeled UI SFX domain')

    args.samples_dir.mkdir(parents=True,exist_ok=True)
    checks={}
    for frame in SAMPLES:
        path=args.samples_dir/f'frame_{frame:03d}.png'
        subprocess.run(['ffmpeg','-y','-v','error','-i',str(args.video),'-vf',f'select=eq(n\\,{frame})','-vframes','1',str(path)],check=True)
        image=Image.open(path)
        item={'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        if frame==8:
            item['pill_dark_pixels']=dark_count(image,(70,450,460,630))
            if item['pill_dark_pixels']<=9000: raise ValueError('hero pill not materially present at local frame 8')
        if frame==54:
            item['boxed_emphasis_white_pixels']=white_count(image,(170,350,440,590))
            if item['boxed_emphasis_white_pixels']<=500: raise ValueError('boxed absolutamente emphasis not visible at local frame 54')
        if frame in (85,93,102):
            bands=((455,625),(565,755),(675,890))
            counts=[white_count(image,(35,y0,145,y1)) for y0,y1 in bands]
            item['row_band_white_pixels']=counts
            required=1 if frame==85 else 2 if frame==93 else 3
            if sum(1 for count in counts if count>350)<required:
                raise ValueError(f'expected at least {required} support rows at local frame {frame}: {counts}')
        checks[str(frame)]=item

    evidence={
        'schema_version':'motion-os.golden-s11-render-evidence/v1',
        'video_sha256':hashlib.sha256(args.video.read_bytes()).hexdigest(),
        'frame_count':frames,
        'fps':30,
        'width':512,
        'height':1108,
        'audio_streams':len(audio),
        'samples':checks,
        'authority':'STRUCTURAL_RENDER_EXECUTED',
        'source_fidelity_authority':'BLOCKED_UNTIL_SOURCE_BOUND_DIFF',
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
