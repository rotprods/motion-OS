from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops, ImageStat

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.renderers.assembly import RenderArtifact, build_composite_plan, ffmpeg_assembly_argv
from src.renderers.color_policy import ArtifactColorBinding, BT709_SDR_LIMITED, SRGB_FULL, ffmpeg_color_filter, ffmpeg_output_color_args

OUT=ROOT/'.artifacts'/'heterogeneous-master'; OUT.mkdir(parents=True,exist_ok=True)
HF=ROOT/'runtime'/'hyperframes'/'out'/'runtime-local.mp4'; LOT=ROOT/'runtime'/'lottie'/'overlay-argb.mov'; AUDIO=OUT/'master-880hz.wav'
BASE=OUT/'base-bt709.mkv'; OVER=OUT/'overlay-bt709-alpha.mkv'; MASTER=OUT/'heterogeneous-master.mp4'; EVIDENCE=OUT/'heterogeneous_master_evidence.json'

def run(args:list[str])->None: subprocess.run(args,check=True,timeout=120)
def sha(path:Path)->str:
    h=hashlib.sha256();
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def probe(path:Path)->dict:
    p=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],check=True,capture_output=True,text=True,timeout=30); return json.loads(p.stdout)
def norm(source:Path,dest:Path,*,alpha:bool)->str:
    binding=ArtifactColorBinding(source.stem,SRGB_FULL,preserve_alpha=alpha); graph=ffmpeg_color_filter(binding,BT709_SDR_LIMITED,input_label='0:v',output_label='norm')
    run(['ffmpeg','-v','error','-y','-i',str(source),'-filter_complex',graph,'-map','[norm]','-c:v','ffv1','-level','3',*ffmpeg_output_color_args(),str(dest)])
    return graph

def frame(path:Path,t:float,out:Path)->None: run(['ffmpeg','-v','error','-y','-ss',f'{t:.3f}','-i',str(path),'-frames:v','1',str(out)])

def main()->int:
    for p in (HF,LOT):
        if not p.exists(): raise SystemExit(f'missing physical source: {p}')
    run(['ffmpeg','-v','error','-y','-f','lavfi','-i','sine=frequency=880:sample_rate=48000:duration=3','-c:a','pcm_s16le',str(AUDIO)])
    base_filter=norm(HF,BASE,alpha=False); overlay_filter=norm(LOT,OVER,alpha=True)
    base=RenderArtifact('hyperframes-base','hyperframes',str(BASE),0,3000,640,360,30,False,(f'PR#62@17da8a190a4492f1193716fa864bcd838bfcfd7b',f'sha256:{sha(BASE)}'),0)
    overlay=RenderArtifact('lottie-overlay','lottie',str(OVER),0,3000,640,360,30,True,(f'PR#66@3513566b37fa6b8d15c357e78bb523c611669d0b',f'sha256:{sha(OVER)}'),1)
    plan=build_composite_plan([base,overlay],width=640,height=360,fps=30,duration_ms=3000,audio_path=str(AUDIO))
    argv=ffmpeg_assembly_argv(plan,str(MASTER),overwrite=True)
    argv[-1:-1]=['-pix_fmt','yuv420p',*ffmpeg_output_color_args()]
    run(argv)
    meta=probe(MASTER); streams=meta.get('streams',[]); video=[s for s in streams if s.get('codec_type')=='video']; audio=[s for s in streams if s.get('codec_type')=='audio']; errors=[]
    if len(video)!=1: errors.append(f'video_stream_count:{len(video)}')
    if len(audio)!=1: errors.append(f'audio_stream_count:{len(audio)}')
    if video:
        v=video[0]
        if (v.get('width'),v.get('height'))!=(640,360): errors.append('dimensions')
        if v.get('avg_frame_rate') not in {'30/1','30'}: errors.append(f"fps:{v.get('avg_frame_rate')}")
        frames=v.get('nb_frames')
        if frames is not None and int(frames)!=90: errors.append(f'frames:{frames}')
        expected={'color_primaries':'bt709','color_transfer':'bt709','color_space':'bt709','color_range':'tv'}
        for k,e in expected.items():
            if v.get(k)!=e: errors.append(f'{k}:{v.get(k)}')
    duration=float(meta.get('format',{}).get('duration') or 0)
    if abs(duration-3.0)>0.08: errors.append(f'duration:{duration}')
    base_png=OUT/'base-final-frame.png'; master_png=OUT/'master-final-frame.png'; frame(BASE,2.90,base_png); frame(MASTER,2.90,master_png)
    diff=ImageChops.difference(Image.open(base_png).convert('RGB'),Image.open(master_png).convert('RGB')); mean=sum(ImageStat.Stat(diff).mean)/3
    if mean<0.15: errors.append(f'overlay_not_visibly_contributing:{mean}')
    lineage=json.loads((ROOT/'integration'/'heterogeneous_master'/'SOURCE_LINEAGE.json').read_text())
    payload={'schema':'motion-os.heterogeneous-master-physical/v1','authority':'PHYSICAL_HETEROGENEOUS_MASTER_VERIFIED' if not errors else 'EXECUTED_FAILED','creative_authority':'none','source_revision':subprocess.run(['git','rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip(),'github_run_id':__import__('os').environ.get('GITHUB_RUN_ID'),'lineage':lineage,'plan_hash':plan['plan_hash'],'filters':{'base':base_filter,'overlay':overlay_filter},'artifacts':{str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in (HF,LOT,AUDIO,BASE,OVER,MASTER)},'probe':meta,'overlay_visual_difference_mae':mean,'errors':errors,'ok':not errors}
    EVIDENCE.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n'); print(json.dumps(payload,indent=2,sort_keys=True)); return 0 if not errors else 1

if __name__=='__main__': raise SystemExit(main())
