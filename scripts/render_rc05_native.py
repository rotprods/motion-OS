from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import math, subprocess, shutil, json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/rc05'; FR=OUT/'frames'; FR.mkdir(parents=True,exist_ok=True)
W,H,FPS,DUR=1080,1920,30,10
PAPER=(232,226,216); PAPER2=(247,243,235); INK=(22,20,17); MUTED=(116,109,100); LINE=(86,79,72)
coin_src=Image.open(ROOT/'data/rc04/coin_final_clean.png').convert('RGBA')
def F(size,serif=False,italic=False,bold=False):
    if serif:
        if bold and italic: paths=['/usr/share/fonts/opentype/didot/GFSDidotBoldItalic.otf']
        elif bold: paths=['/usr/share/fonts/opentype/didot/GFSDidotBold.otf']
        elif italic: paths=['/usr/share/fonts/opentype/didot/GFSDidotItalic.otf']
        else: paths=['/usr/share/fonts/opentype/didot/GFSDidot.otf']
    else: paths=['/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for p in paths:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()
def clamp(x,a=0,b=1):return max(a,min(b,x))
def smooth(x):x=clamp(x);return x*x*(3-2*x)
def expo(x):x=clamp(x);return 1-(1-x)**4
def bell(x):return math.sin(math.pi*clamp(x))
def draw_grid(d,t,opacity=.25):
    ox=int(math.sin(t*.63)*14); oy=int(math.cos(t*.48)*9); col=tuple(int(PAPER[i]*(1-opacity)+MUTED[i]*opacity) for i in range(3))
    for y in range(-120+oy,H+120,120): d.line((40,y,W-40,y),fill=col,width=1)
    for x in range(-120+ox,W+120,120): d.line((x,55,x,H-55),fill=col,width=1)
    d.rectangle((40,55,W-40,H-55),outline=col,width=1)
def base_field(t):
    im=Image.new('RGBA',(W,H),PAPER+(255,));d=ImageDraw.Draw(im);draw_grid(d,t,.24);return im
def coin_layer(scale=1.0,flip=1.0,angle=0,brightness=1.0,contrast=1.06,blur=0):
    im=ImageEnhance.Contrast(coin_src).enhance(contrast);im=ImageEnhance.Brightness(im).enhance(brightness);target=max(28,int(600*scale));ww=max(20,int(target*max(.12,abs(flip))));im=im.resize((ww,target),Image.Resampling.LANCZOS)
    if angle: im=im.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    if blur>0: im=im.filter(ImageFilter.GaussianBlur(blur))
    return im
def composite_shadow(base,layer,xy,blur=25,alpha=78,offset=(18,28)):
    x,y=map(int,xy);mask=layer.getchannel('A');sh=Image.new('RGBA',layer.size,(22,18,14,alpha));sh.putalpha(mask.point(lambda p:int(p*alpha/255)));sh=sh.filter(ImageFilter.GaussianBlur(blur)) if blur else sh;base.alpha_composite(sh,(x+offset[0],y+offset[1]));base.alpha_composite(layer,(x,y))
def render_frame(n,tunnel_variant='single_clean',final_variant='asymmetric'):
    t=n/FPS;base=base_field(t);d=ImageDraw.Draw(base)
    if t<5.18:
        a=expo(t);c=coin_layer(.96,.30+.70*a,angle=-11+11*a);composite_shadow(base,c,(-215+215*a,-75+130*a),22,70);d.text((92,705),'VALUE / CULTURE / POWER',font=F(22),fill=INK);d.text((540,875),'REBELLION',font=F(144,True,bold=True),fill=INK,anchor='ma')
    if 4.03<t<5.30:
        u=clamp((t-4.03)/1.22);z=bell(u);e=expo(u);c=coin_layer(.70+2.7*z,max(.16,abs(math.cos(u*math.pi*.72))),angle=-12-36*u,brightness=.77,blur=max(0,11*z-3));composite_shadow(base,c,(-780+1700*e,950+95*math.sin(math.pi*u)),30,94)
    if 4.88<t<6.90:
        layer=base_field(t);ld=ImageDraw.Draw(layer);ld.rectangle((70,200,1010,1700),outline=(65,59,53),width=2);ld.text((92,240),'01 / SYSTEMS OF VALUE',font=F(21),fill=INK);ld.text((540,690),'MOVEMENT',font=F(132,True,bold=True),fill=INK,anchor='ma');layer.putalpha(int(255*expo((t-4.88)/.28)));base=Image.alpha_composite(base,layer)
    if 6.68<t<7.08:
        u=expo((t-6.68)/.36);cover=Image.new('RGBA',(W,int(H*u)),PAPER2+(246,));base.alpha_composite(cover,(0,H-int(H*u)));c=coin_layer(.42+.58*bell(u),max(.18,abs(math.cos(u*math.pi))),angle=12-24*u,brightness=.98);composite_shadow(base,c,(690-560*u,1650-1180*u),14,46)
    if 7.02<t<8.60:
        alpha=expo((t-7.02)/.16);layer=base_field(t);ld=ImageDraw.Draw(layer);ld.text((74,190),'02 / STRUCTURE BECOMES MOTION',font=F(21),fill=INK);ld.text((540,835),'SYSTEM',font=F(180,True,bold=True),fill=INK,anchor='ma');layer.putalpha(int(255*alpha));base=Image.alpha_composite(base,layer)
    if t>8.63:
        alpha=expo((t-8.63)/.16);layer=base_field(t);ld=ImageDraw.Draw(layer);ld.text((120,690),'MOTION.OS / AUTONOMOUS CREATIVE SYSTEM',font=F(22),fill=MUTED);ld.text((120,760),'MOTION',font=F(158,True,bold=True),fill=INK);ld.text((120,955),'SYSTEM',font=F(158,True,bold=True),fill=INK);layer.putalpha(int(255*alpha));base=Image.alpha_composite(base,layer)
    return base.convert('RGB')
def main():
    if FR.exists():shutil.rmtree(FR)
    FR.mkdir(parents=True)
    for n in range(FPS*DUR):render_frame(n).save(FR/f'{n:04d}.jpg',quality=91)
    silent=OUT/'rc05_silent.mp4';final=OUT/'MOTION_OS_RC05.mp4';subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',str(FR/'%04d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','17','-preset','medium',str(silent)],check=True);score=ROOT/'data/rc_candidate/score.wav';subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(silent),'-i',str(score),'-c:v','copy','-c:a','aac','-b:a','192k','-shortest',str(final)],check=True);print(final)
if __name__=='__main__':main()
