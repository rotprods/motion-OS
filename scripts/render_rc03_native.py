from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import math, subprocess, shutil, json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/rc03'; FR=OUT/'frames_native'; FR.mkdir(parents=True,exist_ok=True)
W,H,FPS,DUR=1080,1920,30,10
PAPER=(232,226,216); PAPER2=(247,243,235); INK=(22,20,17); MUTED=(116,109,100); LINE=(86,79,72)
coin_src=Image.open(OUT/'assets/coin_clean.png').convert('RGBA')

def F(size,serif=False,italic=False,bold=False):
    if serif:
        if bold and italic: paths=['/usr/share/fonts/opentype/didot/GFSDidotBoldItalic.otf']
        elif bold: paths=['/usr/share/fonts/opentype/didot/GFSDidotBold.otf']
        elif italic: paths=['/usr/share/fonts/opentype/didot/GFSDidotItalic.otf']
        else: paths=['/usr/share/fonts/opentype/didot/GFSDidot.otf']
    else:
        paths=['/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for p in paths:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def clamp(x,a=0,b=1):return max(a,min(b,x))
def smooth(x):x=clamp(x);return x*x*(3-2*x)
def expo(x):x=clamp(x);return 1-(1-x)**4
def bell(x):return math.sin(math.pi*clamp(x))
def lerp(a,b,t):return a+(b-a)*t

def draw_grid(d,t,opacity=.25):
    ox=int(math.sin(t*.63)*14); oy=int(math.cos(t*.48)*9)
    col=tuple(int(PAPER[i]*(1-opacity)+MUTED[i]*opacity) for i in range(3))
    for y in range(-120+oy,H+120,120): d.line((40,y,W-40,y),fill=col,width=1)
    for x in range(-120+ox,W+120,120): d.line((x,55,x,H-55),fill=col,width=1)
    d.rectangle((40,55,W-40,H-55),outline=col,width=1)

def dots(d,x0,y0,w,h,spacing=27,alpha=.5):
    col=tuple(int(PAPER[i]*(1-alpha)+MUTED[i]*alpha) for i in range(3))
    for y in range(y0,y0+h,spacing):
        for x in range(x0,x0+w,spacing): d.ellipse((x-2,y-2,x+2,y+2),fill=col)

def base_field(t):
    im=Image.new('RGBA',(W,H),PAPER+(255,)); d=ImageDraw.Draw(im)
    draw_grid(d,t,.24); dots(d,355,320,430,380,27,.5);dots(d,300,1335,430,350,27,.34)
    dx=math.sin(t*.39)*18;dy=math.cos(t*.31)*11
    d.arc((-650+dx,710+dy,790+dx,1600+dy),198,352,fill=(139,132,123),width=2)
    d.arc((210-dx,540-dy,1510-dx,1240-dy),130,316,fill=(139,132,123),width=2)
    d.arc((220+dx,120,1320+dx,1850),100,270,fill=(157,150,141),width=2)
    d.text((52,24),'70–80px',font=F(19),fill=MUTED); d.text((500,24),'12 px',font=F(19),fill=MUTED); d.text((935,24),'70–80px',font=F(19),fill=MUTED)
    return im

def coin_layer(scale=1.0,flip=1.0,angle=0,brightness=1.0,contrast=1.06,blur=0):
    im=ImageEnhance.Contrast(coin_src).enhance(contrast)
    im=ImageEnhance.Brightness(im).enhance(brightness)
    target=max(28,int(600*scale)); ww=max(20,int(target*max(.12,abs(flip)))); hh=target
    im=im.resize((ww,hh),Image.Resampling.LANCZOS)
    if angle: im=im.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    if blur>0: im=im.filter(ImageFilter.GaussianBlur(blur))
    return im

def composite_shadow(base,layer,xy,blur=25,alpha=78,offset=(18,28)):
    x,y=map(int,xy); mask=layer.getchannel('A')
    sh=Image.new('RGBA',layer.size,(22,18,14,alpha)); sh.putalpha(mask.point(lambda p:int(p*alpha/255)))
    if blur: sh=sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh,(x+offset[0],y+offset[1])); base.alpha_composite(layer,(x,y))

def reveal_text(base,text,font,center_y,progress,fill=INK,max_w=930,track=0):
    p=expo(progress)
    if p<=0:return
    layer=Image.new('RGBA',(max_w,220),(0,0,0,0));d=ImageDraw.Draw(layer);d.text((max_w//2,10),text,font=font,fill=fill,anchor='ma');top=int((1-p)*220);crop=layer.crop((0,top,max_w,220))
    if track:
        nw=max(20,int(max_w*(.90+.10*p))); crop=crop.resize((nw,crop.height),Image.Resampling.LANCZOS); x=(W-nw)//2
    else:x=(W-max_w)//2
    base.alpha_composite(crop,(x,int(center_y+top)))

def render_frame(n,tunnel_variant='corridor',final_variant='asymmetric'):
    t=n/FPS;base=base_field(t);d=ImageDraw.Draw(base)
    if t<5.18:
        a=expo(t/1.0); c=coin_layer(.96,.30+.70*a,angle=-11+11*a); composite_shadow(base,c,(-215+215*a,-75+130*a),22,70); d.text((92,705),'VALUE / CULTURE / POWER',font=F(22),fill=INK); reveal_text(base,'REBELLION',F(144,True,bold=True),875,(t-1.15)/.72,track=1)
    if 4.03<t<5.30:
        u=clamp((t-4.03)/1.22); z=bell(u);e=expo(u);c=coin_layer(.70+2.7*z,max(.16,abs(math.cos(u*math.pi*.72))),angle=-12-36*u,brightness=.77,blur=max(0,11*z-3));composite_shadow(base,c,(-780+1700*e,950+95*math.sin(math.pi*u)),30,94)
    if 4.88<t<7.02:
        layer=base_field(t);ld=ImageDraw.Draw(layer);ld.rectangle((70,200,1010,1700),outline=(65,59,53),width=2);ld.text((92,240),'01 / SYSTEMS OF VALUE',font=F(21),fill=INK);reveal_text(layer,'MOVEMENT',F(132,True,bold=True),690,(t-5.25)/.62,track=1);layer.putalpha(int(255*expo((t-4.88)/.28)));base=Image.alpha_composite(base,layer)
    if 6.98<t<8.60:
        layer=base_field(t);ld=ImageDraw.Draw(layer);ld.text((74,190),'02 / STRUCTURE BECOMES MOTION',font=F(21),fill=INK);ld.text((540,835),'SYSTEM',font=F(170,True,bold=True),fill=INK,anchor='ma');layer.putalpha(int(255*expo((t-6.98)/.22)));base=Image.alpha_composite(base,layer)
    if t>8.64:
        layer=base_field(t);ld=ImageDraw.Draw(layer);ld.text((120,690),'MOTION.OS / AUTONOMOUS CREATIVE SYSTEM',font=F(22),fill=MUTED);ld.text((120,760),'MOTION',font=F(158,True,bold=True),fill=INK);ld.text((120,955),'SYSTEM',font=F(158,True,bold=True),fill=INK);layer.putalpha(int(255*expo((t-8.64)/.18)));base=Image.alpha_composite(base,layer)
    return base.convert('RGB')

def main():
    if FR.exists():shutil.rmtree(FR)
    FR.mkdir(parents=True)
    for n in range(FPS*DUR):render_frame(n).save(FR/f'{n:04d}.jpg',quality=91)
    silent=OUT/'rc03_native_silent.mp4';final=OUT/'MOTION_OS_RC03.mp4';subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',str(FR/'%04d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','17','-preset','medium','-movflags','+faststart',str(silent)],check=True);score=ROOT/'data/rc_candidate/score.wav';subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(silent),'-i',str(score),'-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(final)],check=True);print(final)
if __name__=='__main__':main()
