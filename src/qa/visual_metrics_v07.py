from __future__ import annotations
from pathlib import Path
import cv2,numpy as np,math,statistics
def _read(video,t):
    cap=cv2.VideoCapture(str(video));cap.set(cv2.CAP_PROP_POS_MSEC,float(t)*1000);ok,frame=cap.read();cap.release()
    if not ok:raise RuntimeError(f'Cannot read frame at {t} from {video}')
    return cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
def _small(im):return cv2.resize(im,(320,568),interpolation=cv2.INTER_AREA)
def mse_images(a,b):a=_small(a).astype(np.float32);b=_small(b).astype(np.float32);return float(np.mean((a-b)**2))
def contrast(im):return float(np.std(_small(im)))
def edge_density(im):return float(np.mean(cv2.Canny(_small(im),60,140)>0))
def entropy(im):hist=cv2.calcHist([_small(im)],[0],None,[256],[0,256]).ravel();p=hist/hist.sum();p=p[p>0];return float(-(p*np.log2(p)).sum())
def sample(video,times):return [{'t':t,'contrast':contrast(_read(video,t)),'edge_density':edge_density(_read(video,t)),'entropy':entropy(_read(video,t))} for t in times]
def temporal_motion_energy(video,start,end,samples=7):
    times=[start+(end-start)*i/(samples-1) for i in range(samples)];ims=[_read(video,t) for t in times];diffs=[mse_images(a,b) for a,b in zip(ims,ims[1:])];return {'mean':statistics.mean(diffs),'stdev':statistics.pstdev(diffs),'samples':diffs}
def boundary_continuity(video,start,end,epsilon=.04):
    vals=[mse_images(_read(video,max(0,start-epsilon)),_read(video,start+epsilon)),mse_images(_read(video,max(0,end-epsilon)),_read(video,end+epsilon))];return {'start_mse':vals[0],'end_mse':vals[1],'mean':statistics.mean(vals)}
def outside_invariance(before,after,times):
    vals=[mse_images(_read(before,t),_read(after,t)) for t in times];return {'mean':statistics.mean(vals),'samples':vals}
