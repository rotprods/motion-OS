#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,statistics
from pathlib import Path
from PIL import Image

COLORS={'column':(0,243,109),'question_mark':(0,168,255),'factor_x':(255,242,0)}

def frame_path(directory:Path,frame:int)->Path:
 for n in (f'element-{frame}.png',f'element-{frame:02d}.png',f'element-{frame:03d}.png',f'frame_{frame:03d}.png',f'{frame:04d}.png',f'{frame+1:04d}.png'):
  p=directory/n
  if p.exists():return p
 raise FileNotFoundError(frame)

def bbox_from_color(image:Image.Image,target:tuple[int,int,int],tol:int=18):
 rgba=image.convert('RGBA');pix=rgba.load();coords=[];tr,tg,tb=target
 for y in range(rgba.height):
  for x in range(rgba.width):
   r,g,b,a=pix[x,y]
   if a>8 and max(abs(r-tr),abs(g-tg),abs(b-tb))<=tol:coords.append((x,y))
 if not coords:return None
 xs=[p[0] for p in coords];ys=[p[1] for p in coords];return (min(xs),min(ys),max(xs)-min(xs)+1,max(ys)-min(ys)+1)

def iou(a,b):
 ax,ay,aw,ah=a;bx,by,bw,bh=b;ix=max(0,min(ax+aw,bx+bw)-max(ax,bx));iy=max(0,min(ay+ah,by+bh)-max(ay,by));inter=ix*iy;union=aw*ah+bw*bh-inter;return inter/union if union else 0.0

def centroid(a,b):return math.hypot((a[0]+a[2]/2)-(b[0]+b[2]/2),(a[1]+a[3]/2)-(b[1]+b[3]/2))
def areaerr(a,b):aa=a[2]*a[3];bb=b[2]*b[3];return abs(bb-aa)/aa*100 if aa else 0.0

def qualify(overlay_dir:Path,measured:dict)->dict:
 if measured.get('schema_version')!='motion-os.s16-measured-track/v1':raise ValueError('unsupported S16 track')
 metrics={};per_frame={}
 for key in ('column','question_mark','factor_x'):
  expected=[];records=[];obs_frames=[]
  for row in measured['frames']:
   raw=row.get(key)
   if raw is None:continue
   f=int(row['local_frame']);exp=(float(raw['x']),float(raw['y']),float(raw['width']),float(raw['height']));expected.append(f)
   obs=bbox_from_color(Image.open(frame_path(overlay_dir,f)),COLORS[key])
   if obs is None:continue
   obs_frames.append(f);records.append({'frame':f,'expected':exp,'observed':obs,'iou':iou(exp,obs),'centroid_error_px':centroid(exp,obs),'area_error_pct':areaerr(exp,obs)})
  metrics[key]={'expected_first':min(expected) if expected else None,'expected_last':max(expected) if expected else None,'observed_first':min(obs_frames) if obs_frames else None,'observed_last':max(obs_frames) if obs_frames else None,'first_error_frames':(min(obs_frames)-min(expected)) if expected and obs_frames else None,'last_error_frames':(max(obs_frames)-max(expected)) if expected and obs_frames else None,'mean_bbox_iou':statistics.fmean(r['iou'] for r in records) if records else None,'min_bbox_iou':min((r['iou'] for r in records),default=None),'mean_centroid_error_px':statistics.fmean(r['centroid_error_px'] for r in records) if records else None,'mean_area_error_pct':statistics.fmean(r['area_error_pct'] for r in records) if records else None};per_frame[key]=records
 gates={
  'column_geometry':metrics['column']['mean_bbox_iou'] is not None and metrics['column']['mean_bbox_iou']>=.98 and metrics['column']['mean_centroid_error_px']<=1,
  'question_geometry':metrics['question_mark']['mean_bbox_iou'] is not None and metrics['question_mark']['mean_bbox_iou']>=.98 and metrics['question_mark']['mean_centroid_error_px']<=1,
  'factor_geometry':metrics['factor_x']['mean_bbox_iou'] is not None and metrics['factor_x']['mean_bbox_iou']>=.90 and metrics['factor_x']['mean_centroid_error_px']<=4,
  'timing':all(metrics[k]['first_error_frames']==0 and metrics[k]['last_error_frames']==0 for k in metrics),
 }
 return {'schema_version':'motion-os.s16-source-bound-qualification/v1','scene_id':'S16_FACTOR_X','authority':'MEASURED_VISIBLE_OUTPUT_PARTIAL_QUALIFICATION','measurement_mode':'TARGET_ISOLATED_UNIQUE_COLOR_RENDER','metrics':metrics,'gates':gates,'p0_p1_visible_geometry_gates_pass':all(gates.values()),'full_9d_fidelity_validated':False,'blocked_dimensions':['exact Factor X font/source glyph outline','column/question-mark morphology/material/lighting','original AE graph/Graph Editor curves','exact opacity curves','source speaker pixels in structural mode','isolated original SFX stems','causal origin of local87+ global reflow'],'per_frame':per_frame}

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--overlay-dir',type=Path,required=True);ap.add_argument('--measured',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=qualify(a.overlay_dir,json.loads(a.measured.read_text()));a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'gates':out['gates'],'pass':out['p0_p1_visible_geometry_gates_pass']},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
