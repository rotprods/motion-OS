from pathlib import Path
from PIL import Image
import subprocess,tempfile,statistics,shutil
def extract_frame(video,t,out):subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',str(t),'-i',str(video),'-frames:v','1',str(out)],check=True)
def mse(a,b):
 a=a.convert('RGB').resize((320,568));b=b.convert('RGB').resize((320,568));pa=list(a.getdata());pb=list(b.getdata());return sum((x-y)**2 for p,q in zip(pa,pb) for x,y in zip(p,q))/(len(pa)*3)
def compare_videos(before,after,times):
 tmp=Path(tempfile.mkdtemp());vals=[]
 try:
  for i,t in enumerate(times):
   p1=tmp/f'a{i}.jpg';p2=tmp/f'b{i}.jpg';extract_frame(before,t,p1);extract_frame(after,t,p2);vals.append({'t':t,'mse':round(mse(Image.open(p1),Image.open(p2)),2)})
 finally:shutil.rmtree(tmp,ignore_errors=True)
 return {'samples':vals,'mean_mse':round(statistics.mean(v['mse'] for v in vals),2) if vals else 0}
