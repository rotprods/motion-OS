from __future__ import annotations
from pathlib import Path
import subprocess,json
def splice(master_path,patch_path,start,end,out_path):
    fc=f'[0:v]trim=start=0:end={start},setpts=PTS-STARTPTS[v0];[1:v]setpts=PTS-STARTPTS[v1];[0:v]trim=start={end},setpts=PTS-STARTPTS[v2];[v0][v1][v2]concat=n=3:v=1:a=0[outv]';subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(master_path),'-i',str(patch_path),'-filter_complex',fc,'-map','[outv]','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-vsync','cfr','-movflags','+faststart',str(out_path)],check=True);return str(out_path)
def probe(path):
    r=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,r_frame_rate:format=duration','-of','json',str(path)],capture_output=True,text=True,check=True);d=json.loads(r.stdout);s=d['streams'][0];return {'width':s['width'],'height':s['height'],'frames':int(s.get('nb_frames') or 0),'duration':round(float(d['format']['duration']),3),'r_frame_rate':s.get('r_frame_rate')}
