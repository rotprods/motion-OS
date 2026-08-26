from __future__ import annotations
from pathlib import Path
from PIL import Image,ImageStat,ImageFilter
import math
def _gray(path:Path)->Image.Image:return Image.open(path).convert('L')
def frame_entropy(img):
    hist=img.histogram();total=sum(hist) or 1;return -sum((c/total)*math.log2(c/total) for c in hist if c)
def rms_difference(a,b):
    import PIL.ImageChops as IC;a=a.resize((270,480));b=b.resize((270,480));return float(ImageStat.Stat(IC.difference(a,b)).rms[0])
def edge_density(img):return float(ImageStat.Stat(img.filter(ImageFilter.FIND_EDGES)).mean[0]/255.0)
def contrast(img):return float(ImageStat.Stat(img).stddev[0]/128.0)
def inspect_frames(frame_dir,fps,duration):
    frame_dir=Path(frame_dir);files=sorted(frame_dir.glob('*.jpg')) or sorted(frame_dir.glob('*.png'))
    if not files:raise ValueError(f'No frames in {frame_dir}')
    sample_count=min(20,len(files));indices=[round(i*(len(files)-1)/max(sample_count-1,1)) for i in range(sample_count)];samples=[_gray(files[i]) for i in indices];ent=[frame_entropy(x) for x in samples];edges=[edge_density(x) for x in samples];contrasts=[contrast(x) for x in samples];deltas=[rms_difference(samples[i],samples[i+1]) for i in range(len(samples)-1)];hold_n=max(2,min(len(files),round(fps*.5)));last=_gray(files[-1]);hold=[rms_difference(_gray(p),last) for p in files[-hold_n:]]
    return {'sample_count':sample_count,'entropy_mean':round(sum(ent)/len(ent),4),'edge_density_mean':round(sum(edges)/len(edges),4),'contrast_mean':round(sum(contrasts)/len(contrasts),4),'motion_delta_mean':round(sum(deltas)/max(len(deltas),1),4),'motion_delta_peak':round(max(deltas) if deltas else 0,4),'final_hold_rms_mean':round(sum(hold)/len(hold),4),'final_hold_rms_peak':round(max(hold),4)}
def metric_gate(metrics):
    defects=[]
    if metrics['contrast_mean']<.12:defects.append({'severity':'P1','code':'LOW_GLOBAL_CONTRAST','value':metrics['contrast_mean']})
    if metrics['motion_delta_peak']<3:defects.append({'severity':'P1','code':'INSUFFICIENT_VISUAL_CHANGE','value':metrics['motion_delta_peak']})
    if metrics['final_hold_rms_mean']>18:defects.append({'severity':'P2','code':'UNSTABLE_FINAL_HOLD','value':metrics['final_hold_rms_mean']})
    return defects
