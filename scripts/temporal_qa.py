from pathlib import Path
from PIL import Image,ImageStat,ImageFilter
import subprocess,json,statistics,math,sys,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1]
def ff(v,t,out):subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',f'{t:.3f}','-i',str(v),'-frames:v','1',str(out)],check=True)
def mse(a,b):
 a=a.convert('L').resize((270,480));b=b.convert('L').resize((270,480));pa=list(a.getdata());pb=list(b.getdata());return sum((x-y)**2 for x,y in zip(pa,pb))/len(pa)
def run(video,slug):
 out=ROOT/'reports'/slug;out.mkdir(parents=True,exist_ok=True);tmp=Path(tempfile.mkdtemp());times=[i*.25 for i in range(40)];ims=[]
 for i,t in enumerate(times):p=tmp/f'{i}.jpg';ff(video,t,p);ims.append(Image.open(p).convert('RGB').copy())
 diffs=[mse(a,b) for a,b in zip(ims,ims[1:])];summary={'video':str(video),'motion_mse_mean':round(statistics.mean(diffs),2),'motion_mse_stdev':round(statistics.pstdev(diffs),2),'samples':len(ims)};(out/'temporal_metrics.json').write_text(json.dumps(summary,indent=2));shutil.rmtree(tmp,ignore_errors=True);print(json.dumps(summary,indent=2))
if __name__=='__main__':run(Path(sys.argv[1]),sys.argv[2])
