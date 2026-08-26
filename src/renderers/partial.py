from __future__ import annotations
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess
W,H=1080,1920
def _font(size,serif=False):
    p='/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed.ttf' if serif else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';return ImageFont.truetype(p,size) if Path(p).exists() else ImageFont.load_default()
def _frame(t,params):
    bg=(231,225,214);ink=(23,21,18);gray=(115,108,99);im=Image.new('RGB',(W,H),bg);d=ImageDraw.Draw(im)
    for y in range(60,H-60,120):d.line((40,y,W-40,y),fill=gray,width=1)
    for x in range(40,W-40,120):d.line((x,60,x,H-60),fill=gray,width=1)
    d.rectangle((40,60,W-40,H-60),outline=gray,width=1);cx,cy=310,380
    for rr,col in [(265,(65,63,60)),(245,(210,205,195)),(218,(120,116,110)),(192,(226,221,212))]:d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),fill=col)
    d.text((cx,265),'SYSTEM / VALUE',font=_font(25,True),fill=ink,anchor='ma');d.text((cx,455),'2026',font=_font(50,True),fill=ink,anchor='ma')
    d.text((540,810),'systems are becoming',font=_font(48,True),fill=ink,anchor='ma');size=max(72,int(118*float(params.get('headline_scale',1.0))));d.text((540,930),'MOTION BECOMES SYSTEM',font=_font(size,True),fill=ink,anchor='ma')
    phase=max(0,min(1,(t-4.05)/1.35));occ=float(params.get('foreground_crop',1));speed=float(params.get('occlusion_speed',1));x=int(1180-1050*min(1,phase/max(.01,speed)));y=int(1180+float(params.get('trajectory_y',0))*phase);rr=int(310*occ);d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(48,46,43));d.text((x,y),'VALUE',font=_font(64,True),fill=(205,200,191),anchor='mm')
    if t>6.2:d.text((540,1460),'PRODUCTION GRAPH',font=_font(86,True),fill=ink,anchor='ma')
    return im
def render_segment(out_dir,start,end,fps,params,name='segment'):
    out_dir.mkdir(parents=True,exist_ok=True);frames=out_dir/f'{name}_frames';frames.mkdir(exist_ok=True);total=max(1,round((end-start)*fps))
    for i in range(total):_frame(start+i/fps,params).save(frames/f'{i:04d}.jpg',quality=90)
    mp4=out_dir/f'{name}.mp4';subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(fps),'-i',str(frames/'%04d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-movflags','+faststart',str(mp4)],check=True);return {'path':str(mp4),'start':start,'end':end,'fps':fps,'frames':total}
def render_master(out_dir,duration,fps,params,name='master'):return render_segment(out_dir,0,duration,fps,params,name)
