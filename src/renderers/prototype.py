from __future__ import annotations
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import math,subprocess,json
W,H=1080,1920
def _font(size,serif=False,italic=False):
    p='/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Italic.ttf' if serif and italic else ('/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed.ttf' if serif else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');return ImageFont.truetype(p,size) if Path(p).exists() else ImageFont.load_default()
def _fit_font(text,max_width,start_size,serif=False,min_size=42):
    size=start_size
    while size>min_size:
        f=_font(size,serif);box=f.getbbox(text)
        if box[2]-box[0]<=max_width:return f
        size-=2
    return _font(min_size,serif)
def _ease(x):x=max(0,min(1,x));return 1-(1-x)**4
def _coin(size,dark=False):
    im=Image.new('RGBA',(size,size),(0,0,0,0));d=ImageDraw.Draw(im);cx=cy=size//2;base=(160,156,148) if not dark else (92,90,86)
    for rr,col in [(.495,(52,50,47)),(.482,(218,214,204)),(.463,(108,104,98)),(.448,(232,228,216)),(.418,base)]:r=size*rr;d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=col+(255,))
    d.text((cx,size*.115),'SYSTEM / VALUE',font=_fit_font('SYSTEM / VALUE',size*.56,int(size*.052),True,18),fill=(65,62,58),anchor='ma');d.text((cx,size*.752),'2026',font=_font(int(size*.082),True),fill=(62,60,56),anchor='ma');return im.filter(ImageFilter.GaussianBlur(.18))
def _palette(style):return {'editorial_finance':((231,225,214),(23,21,18),(105,100,92)),'swiss_brutalist':((244,244,240),(15,15,15),(110,110,106)),'dark_technical':((13,15,18),(240,240,236),(110,116,124)),'experimental_kinetic':((239,236,228),(17,17,17),(115,109,100))}.get(style,((231,225,214),(23,21,18),(105,100,92)))
def render(run_dir,brief,style,iteration=1):
    fps=int(brief['fps']);sample_fps=min(fps,15);dur=float(brief['duration']);total=round(sample_fps*dur);frames=run_dir/f'iter_{iteration:02d}'/'frames';frames.mkdir(parents=True,exist_ok=True);bg,ink,gray=_palette(style['style_id']);c1=_coin(620,style['style_id']=='dark_technical');headline=brief['headline'].upper()
    for n in range(total):
        t=n/sample_fps;im=Image.new('RGB',(W,H),bg);d=ImageDraw.Draw(im)
        for y in range(55,H-55,120):d.line((40,y,W-40,y),fill=gray,width=1)
        for x in range(40,W-40,120):d.line((x,55,x,H-55),fill=gray,width=1)
        if t<dur*.46:
            p=_ease(t/(dur*.12));c=c1.resize((int(620*(.42+.58*p)),)*2);im.paste(c,(int(-310+255*p),int(-130+250*p)),c);d.text((540,930),headline,font=_fit_font(headline,920,104,True,64),fill=ink,anchor='ma')
        else:d.text((540,815),'AUTONOMOUS' if iteration<3 else 'PRODUCTION',font=_font(118,True),fill=ink,anchor='ma')
        im.save(frames/f'{n:04d}.jpg',quality=88)
    mp4=run_dir/f'iter_{iteration:02d}'/'render.mp4';subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(sample_fps),'-i',str(frames/'%04d.jpg'),'-r',str(fps),'-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(mp4)],check=True);probe=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames:format=duration','-of','json',str(mp4)],capture_output=True,text=True,check=True);data=json.loads(probe.stdout);st=data['streams'][0];fmt=data['format'];return {'width':st['width'],'height':st['height'],'frames':int(st.get('nb_frames') or total),'duration':round(float(fmt['duration']),3),'fps':fps,'path':str(mp4)}
