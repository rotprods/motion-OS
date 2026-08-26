from pathlib import Path
from PIL import Image
from collections import deque
import hashlib,math
def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''):h.update(c)
    return h.hexdigest()
def crop_asset(source,box,out_path):im=Image.open(source).convert('RGBA').crop(tuple(box));Path(out_path).parent.mkdir(parents=True,exist_ok=True);im.save(out_path);return out_path
def remove_border_background(source,out_path,tolerance=42,feather=2):
    im=Image.open(source).convert('RGBA');w,h=im.size;pix=im.load();corners=[pix[0,0][:3],pix[w-1,0][:3],pix[0,h-1][:3],pix[w-1,h-1][:3]];bg=tuple(sum(c[i] for c in corners)//4 for i in range(3));close=lambda rgb:math.sqrt(sum((rgb[i]-bg[i])**2 for i in range(3)))<=tolerance;q=deque();seen=set()
    for x in range(w):q.append((x,0));q.append((x,h-1))
    for y in range(h):q.append((0,y));q.append((w-1,y))
    while q:
        x,y=q.popleft()
        if (x,y) in seen:continue
        seen.add((x,y))
        if not close(pix[x,y][:3]):continue
        r,g,b,a=pix[x,y];pix[x,y]=(r,g,b,0)
        if x>0:q.append((x-1,y))
        if x<w-1:q.append((x+1,y))
        if y>0:q.append((x,y-1))
        if y<h-1:q.append((x,y+1))
    Path(out_path).parent.mkdir(parents=True,exist_ok=True);im.save(out_path);return out_path
def asset_record(asset_id,source,output,rights='generated_original',role='hero_object'):return {'asset_id':asset_id,'role':role,'source':str(source),'source_sha256':sha256_file(source),'output':str(output),'output_sha256':sha256_file(output),'rights':rights,'provenance_verified':True}
