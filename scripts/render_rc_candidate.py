from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
import math,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/rc_candidate';FR=OUT/'frames';FR.mkdir(parents=True,exist_ok=True)
W,H,FPS,DUR=1080,1920,6,10;PAPER=(232,226,216);INK=(22,20,17);MUTED=(113,106,97)
asset=Image.open(ROOT/'data/v08_asset_slice/assets/coin_alpha.png').convert('RGBA')
def F(size,serif=False,italic=False,bold=False):
 p='/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf' if serif and bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';return ImageFont.truetype(p,size)
def clamp(x):return max(0,min(1,x))
def expo(x):x=clamp(x);return 1-(1-x)**4
def bell(x):x=clamp(x);return math.sin(math.pi*x)
def coin_layer(scale=1,flip=1,brightness=1.0,angle=0):
 im=ImageEnhance.Brightness(ImageEnhance.Contrast(asset.copy()).enhance(1.08)).enhance(brightness);target=int(520*scale);ww=max(22,int(target*max(.08,abs(flip))));im=im.resize((ww,target),Image.Resampling.LANCZOS);return im.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True) if angle else im
def paste_shadow(base,layer,xy,blur=24,alpha=80):
 mask=layer.getchannel('A');sh=Image.new('RGBA',layer.size,(10,8,6,alpha));sh.putalpha(mask.point(lambda p:int(p*alpha/255)));canvas=Image.new('RGBA',base.size,(0,0,0,0));canvas.paste(sh,(xy[0]+18,xy[1]+28),sh);canvas=canvas.filter(ImageFilter.GaussianBlur(blur));base.alpha_composite(canvas);base.alpha_composite(layer,xy)
def render(n):
 t=n/FPS;base=Image.new('RGBA',(W,H),PAPER+(255,));d=ImageDraw.Draw(base)
 for y in range(0,H,120):d.line((40,y,W-40,y),fill=(180,173,164),width=1)
 for x in range(0,W,120):d.line((x,55,x,H-55),fill=(180,173,164),width=1)
 p=expo(t/1.05);c=coin_layer(.92+.08*p,.24+.76*p,1.03,-8+8*p);paste_shadow(base,c,(int(-230+210*p),int(50+70*p)),22,72)
 if t<5.15:d.text((540,880),'REBELLION',font=F(132,True,bold=True),fill=INK,anchor='ma')
 if 5.15<t<8.72:d.text((540,670),'MOVEMENT',font=F(120,True,bold=True),fill=INK,anchor='ma')
 if 7.18<t<8.72:d.text((540,1160),'SYSTEM',font=F(104,True,bold=True),fill=INK,anchor='ma')
 if t>8.72:d.text((540,790),'MOTION BECOMES SYSTEM',font=F(82,True,bold=True),fill=INK,anchor='ma')
 return base.convert('RGB')
for n in range(FPS*DUR):render(n).save(FR/f'{n:04d}.jpg',quality=92)
video=OUT/'rc_silent.mp4';subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',str(FR/'%04d.jpg'),'-vf','fps=30','-c:v','libx264','-pix_fmt','yuv420p','-crf','17',str(video)],check=True);print(video)
