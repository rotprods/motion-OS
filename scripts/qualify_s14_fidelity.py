#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import statistics
from PIL import Image

@dataclass(frozen=True)
class Box:
    x: float; y: float; width: float; height: float
    @property
    def area(self)->float:return max(0.0,self.width)*max(0.0,self.height)
    @property
    def cx(self)->float:return self.x+self.width/2
    @property
    def cy(self)->float:return self.y+self.height/2

MEASUREMENT_COLORS={
 'card_audio':(0,243,109),'card_visual':(0,168,255),'card_texto':(234,0,255),
 'heading_audio':(255,242,0),'heading_visual':(0,255,240),'heading_texto':(255,122,0),
}

def frame_path(directory:Path,frame:int)->Path:
    candidates=[directory/f'element-{frame}.png',directory/f'element-{frame:02d}.png',directory/f'element-{frame:03d}.png',directory/f'frame_{frame:03d}.png',directory/f'{frame:04d}.png',directory/f'{frame+1:04d}.png']
    for p in candidates:
        if p.exists():return p
    raise FileNotFoundError(f'no overlay frame {frame}: {candidates}')

def iou(a:Box,b:Box)->float:
    ix=max(0.0,min(a.x+a.width,b.x+b.width)-max(a.x,b.x));iy=max(0.0,min(a.y+a.height,b.y+b.height)-max(a.y,b.y));inter=ix*iy;union=a.area+b.area-inter
    return inter/union if union else 0.0

def centroid(a:Box,b:Box)->float:return math.hypot(a.cx-b.cx,a.cy-b.cy)
def area_error(a:Box,b:Box)->float:return abs(a.area-b.area)/a.area*100 if a.area else 0.0

def crop_bounds(box:Box,size:tuple[int,int],pad:int)->tuple[int,int,int,int]:
    w,h=size;return max(0,math.floor(box.x-pad)),max(0,math.floor(box.y-pad)),min(w,math.ceil(box.x+box.width+pad)),min(h,math.ceil(box.y+box.height+pad))

def observe_measurement_color(image:Image.Image,expected:Box,target:tuple[int,int,int],pad:int=12,tolerance:int=18)->Box|None:
    """Measure one target-isolated renderer entity.

    S14's measurement render gives every card/heading a unique flat RGB identity
    while consuming the same geometry track as the production render. This avoids
    the S11 failure family where adjacency/connectivity polluted a bbox oracle.
    """
    rgba=image.convert('RGBA');x0,y0,x1,y1=crop_bounds(expected,rgba.size,pad);pix=rgba.load();coords=[]
    tr,tg,tb=target
    for y in range(y0,y1):
        for x in range(x0,x1):
            r,g,b,a=pix[x,y]
            if a<=8:continue
            if max(abs(r-tr),abs(g-tg),abs(b-tb))<=tolerance:coords.append((x,y))
    if not coords:return None
    xs=[p[0] for p in coords];ys=[p[1] for p in coords]
    return Box(min(xs),min(ys),max(xs)-min(xs)+1,max(ys)-min(ys)+1)

def observe_card(image:Image.Image,expected:Box,state:str='audio')->Box|None:
    return observe_measurement_color(image,expected,MEASUREMENT_COLORS[f'card_{state}'])

def observe_heading(image:Image.Image,expected:Box,state:str='audio')->Box|None:
    return observe_measurement_color(image,expected,MEASUREMENT_COLORS[f'heading_{state}'])

def load_expected(data:dict)->dict[str,dict[int,Box]]:
    out={f'card_{s}':{} for s in ('audio','visual','texto')};out.update({f'heading_{s}':{} for s in ('audio','visual','texto')})
    for row in data['frames']:
        f=int(row['local_frame'])
        for state in ('audio','visual','texto'):
            for kind,key in [('card','cards'),('heading','headings')]:
                raw=row[key].get(state)
                if raw is not None:out[f'{kind}_{state}'][f]=Box(float(raw['x']),float(raw['y']),float(raw['width']),float(raw['height']))
    return out

def summarize(records:list[dict],expected_frames:list[int],observed_frames:list[int])->dict:
    return {
      'expected_first_visible':min(expected_frames) if expected_frames else None,
      'expected_last_visible':max(expected_frames) if expected_frames else None,
      'observed_first_visible':min(observed_frames) if observed_frames else None,
      'observed_last_visible':max(observed_frames) if observed_frames else None,
      'first_visible_error_frames':(min(observed_frames)-min(expected_frames)) if expected_frames and observed_frames else None,
      'last_visible_error_frames':(max(observed_frames)-max(expected_frames)) if expected_frames and observed_frames else None,
      'mean_bbox_iou':statistics.fmean(r['iou'] for r in records) if records else None,
      'min_bbox_iou':min((r['iou'] for r in records),default=None),
      'mean_centroid_error_px':statistics.fmean(r['centroid_error_px'] for r in records) if records else None,
      'mean_area_error_pct':statistics.fmean(r['area_error_pct'] for r in records) if records else None,
    }

def qualify(overlay_dir:Path,measured:dict)->dict:
    if measured.get('schema_version')!='motion-os.s14-measured-track/v1':raise ValueError('unsupported S14 measured-track schema')
    source=measured['source'];expected=load_expected(measured);metrics={};per_frame={}
    for name,track in expected.items():
        records=[];observed_frames=[];kind,state=name.split('_',1)
        for f,exp in sorted(track.items()):
            image=Image.open(frame_path(overlay_dir,f))
            if image.size!=(int(source['width']),int(source['height'])):raise ValueError(f'overlay size mismatch at {f}: {image.size}')
            obs=observe_card(image,exp,state) if kind=='card' else observe_heading(image,exp,state)
            if obs is None:continue
            observed_frames.append(f);records.append({'frame':f,'expected':exp.__dict__,'observed':obs.__dict__,'iou':iou(exp,obs),'centroid_error_px':centroid(exp,obs),'area_error_pct':area_error(exp,obs)})
        metrics[name]=summarize(records,sorted(track),observed_frames);per_frame[name]=records
    card_names=['card_audio','card_visual','card_texto'];head_names=['heading_audio','heading_visual','heading_texto']
    gates={
      'card_geometry':all(metrics[n]['mean_bbox_iou'] is not None and metrics[n]['mean_bbox_iou']>=0.94 and metrics[n]['mean_centroid_error_px']<=3 and metrics[n]['mean_area_error_pct']<=6 for n in card_names),
      'card_timing':all(metrics[n]['first_visible_error_frames'] is not None and abs(metrics[n]['first_visible_error_frames'])<=1 and abs(metrics[n]['last_visible_error_frames'])<=1 for n in card_names),
      'heading_geometry':all(metrics[n]['mean_bbox_iou'] is not None and metrics[n]['mean_bbox_iou']>=0.82 and metrics[n]['mean_centroid_error_px']<=5 for n in head_names),
      'heading_timing':all(metrics[n]['first_visible_error_frames'] is not None and abs(metrics[n]['first_visible_error_frames'])<=1 and abs(metrics[n]['last_visible_error_frames'])<=1 for n in head_names),
    }
    return {'schema_version':'motion-os.s14-source-bound-qualification/v1','scene_id':'S14_AUDIO_VISUAL_TEXTO','source':source,'measurement_mode':'TARGET_ISOLATED_UNIQUE_COLOR_RENDER','authority':'MEASURED_VISIBLE_OUTPUT_PARTIAL_QUALIFICATION','metrics':metrics,'gates':gates,'p0_p1_visible_state_gates_pass':all(gates.values()),'full_9d_fidelity_validated':False,'blocked_dimensions':['annotation vector-path fidelity','exact heading font morphology','nested source-media pixel fidelity in structural mode','original AE graph/Graph Editor curves','isolated original SFX stems','full FX/color/depth/camera decomposition'],'per_frame':per_frame}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--overlay-dir',type=Path,required=True);ap.add_argument('--measured',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();m=json.loads(a.measured.read_text());out=qualify(a.overlay_dir,m);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('authority','measurement_mode','gates','p0_p1_visible_state_gates_pass')},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
