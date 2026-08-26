from pathlib import Path
import importlib.util,subprocess,shutil,json,statistics
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'scripts/render_rc03_native.py';OUT=ROOT/'data/rc03/branches';OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('rc',SRC);rc=importlib.util.module_from_spec(spec);spec.loader.exec_module(rc)
variants={'A':('corridor','asymmetric'),'B':('single','asymmetric'),'C':('radial','centered'),'D':('corridor','oversized')};base_frames=ROOT/'data/rc03/frames_native';font=ImageFont.truetype('/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf',18)
def mse(a,b):
 a=a.convert('L').resize((216,384));b=b.convert('L').resize((216,384));pa=list(a.getdata());pb=list(b.getdata());return sum((x-y)**2 for x,y in zip(pa,pb))/len(pa)
rows=[]
for vid,(tun,fin) in variants.items():
 d=OUT/vid;fr=d/'frames';fr.mkdir(parents=True,exist_ok=True)
 for n in range(300):
  dst=fr/f'{n:04d}.jpg'; shutil.copy2(base_frames/f'{n:04d}.jpg',dst) if n<204 else rc.render_frame(n,tun,fin).save(dst,quality=90)
 silent=d/'silent.mp4';final=d/f'MOTION_OS_RC03_{vid}.mp4';subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(fr/'%04d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','fast',str(silent)],check=True);subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(silent),'-i',str(ROOT/'data/rc_candidate/score.wav'),'-c:v','copy','-c:a','aac','-b:a','192k','-shortest',str(final)],check=True)
 times=[7.05,7.35,7.75,8.15,8.42,8.58,8.8,9.2,9.75];ims=[Image.open(fr/f'{round(t*30):04d}.jpg').convert('RGB') for t in times];sh=Image.new('RGB',(216*9,420),(248,246,242));dr=ImageDraw.Draw(sh)
 for i,(t,im) in enumerate(zip(times,ims)): sh.paste(im.resize((216,384)),(i*216,0));dr.text((i*216+6,388),f'{t:.2f}',font=font,fill=(20,18,16))
 sh.save(d/'target_sheet.jpg',quality=92); diffs=[mse(a,b) for a,b in zip(ims,ims[1:])]; final_stab=mse(Image.open(fr/'0280.jpg'),Image.open(fr/'0299.jpg')); rows.append({'id':vid,'tunnel':tun,'final':fin,'target_motion_mse':round(statistics.mean(diffs),2),'final_stability_mse':round(final_stab,2),'video':str(final),'sheet':str(d/'target_sheet.jpg')})
(OUT/'branch_metrics.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
