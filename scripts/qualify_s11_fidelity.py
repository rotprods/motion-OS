#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,statistics
from pathlib import Path
from collections import deque
from PIL import Image


def sample(track,frame):
    if frame<track[0][0] or frame>track[-1][0]: return None
    for row in track:
        if row[0]==frame:return tuple(map(float,row[1:5]))
    ri=next(i for i,row in enumerate(track) if row[0]>frame); a,b=track[ri-1],track[ri]
    t=(frame-a[0])/(b[0]-a[0])
    return tuple(a[i]+(b[i]-a[i])*t for i in range(1,5))

def iou(a,b):
    ax,ay,aw,ah=a; bx,by,bw,bh=b
    ix=max(0,min(ax+aw,bx+bw)-max(ax,bx)); iy=max(0,min(ay+ah,by+bh)-max(ay,by)); inter=ix*iy
    union=aw*ah+bw*bh-inter
    return inter/union if union else 0.0

def centroid(a,b):return math.hypot((a[0]+a[2]/2)-(b[0]+b[2]/2),(a[1]+a[3]/2)-(b[1]+b[3]/2))
def areaerr(a,b):
    aa=a[2]*a[3]; bb=b[2]*b[3]
    return abs(bb-aa)/aa*100 if aa else 0.0

def frame_path(directory,frame):
    for name in (f'element-{frame:03d}.png',f'frame_{frame:03d}.png',f'{frame:04d}.png',f'{frame+1:04d}.png'):
        p=directory/name
        if p.exists():return p
    raise FileNotFoundError(frame)

def components(img,box,kind,pad=18):
    x,y,w,h=box; W,H=img.size; x0=max(0,int(x-pad)); y0=max(0,int(y-pad)); x1=min(W,int(x+w+pad+1)); y1=min(H,int(y+h+pad+1))
    px=img.convert('RGBA').load(); ww=x1-x0; hh=y1-y0; mask=[[False]*ww for _ in range(hh)]
    for yy in range(hh):
        for xx in range(ww):
            r,g,b,a=px[x0+xx,y0+yy]
            if a<=20:continue
            mask[yy][xx]=(max(r,g,b)-min(r,g,b)<50 and max(r,g,b)<90) if kind=='dark' else (r>150 and g>150 and b>150 and max(r,g,b)-min(r,g,b)<65)
    seen=set(); out=[]
    for yy in range(hh):
        for xx in range(ww):
            if not mask[yy][xx] or (xx,yy) in seen:continue
            q=deque([(xx,yy)]); seen.add((xx,yy)); xs=[]; ys=[]
            while q:
                cx,cy=q.popleft(); xs.append(cx); ys.append(cy)
                for nx in (cx-1,cx,cx+1):
                    for ny in (cy-1,cy,cy+1):
                        if 0<=nx<ww and 0<=ny<hh and mask[ny][nx] and (nx,ny) not in seen:
                            seen.add((nx,ny)); q.append((nx,ny))
            if len(xs)>=8:out.append((len(xs),x0+min(xs),y0+min(ys),max(xs)-min(xs)+1,max(ys)-min(ys)+1))
    return sorted(out,reverse=True)

def observe(img,expected,kind,wide=False):
    cs=components(img,expected,kind)
    if wide:cs=[c for c in cs if c[3]>max(20,expected[2]*.45)] or cs
    if not cs:return None
    c=max(cs,key=lambda z:z[0]); return tuple(map(float,c[1:5]))

def qualify(overlay_dir,measured):
    tracks=measured['tracks']; results={}
    for name,kind,wide in [('pill','dark',True),('boxed_absolutamente','white',True),('row_x','white',False),('row_diamond','white',False),('row_megaphone','white',False)]:
        rec=[]; first=None
        for frame in range(130):
            exp=sample(tracks[name],frame)
            if exp is None:continue
            obs=observe(Image.open(frame_path(overlay_dir,frame)),exp,kind,wide)
            if obs:
                if first is None:first=frame
                rec.append((iou(exp,obs),centroid(exp,obs),areaerr(exp,obs)))
        results[name]={
            'expected_first_visible':tracks[name][0][0],'observed_first_visible':first,
            'first_visible_error_frames':None if first is None else first-tracks[name][0][0],
            'mean_bbox_iou':statistics.fmean(x[0] for x in rec) if rec else None,
            'mean_centroid_error_px':statistics.fmean(x[1] for x in rec) if rec else None,
            'mean_area_error_pct':statistics.fmean(x[2] for x in rec) if rec else None,
            'min_bbox_iou':min((x[0] for x in rec),default=None),
        }
    gates={
        'pill':results['pill']['mean_bbox_iou']>=.92 and results['pill']['mean_centroid_error_px']<=3,
        'boxed_absolutamente':results['boxed_absolutamente']['mean_bbox_iou']>=.90,
        'row_timing':all(v is not None and abs(v)<=1 for v in [results['row_x']['first_visible_error_frames'],results['row_diamond']['first_visible_error_frames'],results['row_megaphone']['first_visible_error_frames']]),
        'row_geometry':all(results[n]['mean_centroid_error_px']<=3 and results[n]['mean_area_error_pct']<=8 for n in ['row_x','row_diamond','row_megaphone']),
    }
    return {'schema_version':'motion-os.s11-source-bound-qualification/v1','scene_id':'S11_UI_LIST','authority':'VISIBLE_OUTPUT_PARTIAL_QUALIFICATION','metrics':results,'gates':gates,'p0_p1_output_gates_pass':all(gates.values()),'full_9d_fidelity_validated':False,'blocked_dimensions':['exact fonts','original AE graph','original isolated SFX stems','full FX/color/depth/camera decomposition']}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--overlay-dir',type=Path,required=True); ap.add_argument('--measured',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); args=ap.parse_args()
    measured=json.loads(args.measured.read_text()); out=qualify(args.overlay_dir,measured); args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__':main()
