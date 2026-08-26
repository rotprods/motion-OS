from dataclasses import dataclass,asdict
from pathlib import Path
from PIL import Image,ImageStat,ImageFilter
import hashlib
@dataclass
class AssetFitness:
    resolution:float;realism:float;perspective_fit:float;lighting_fit:float;background_separation:float;material_quality:float;semantic_fit:float;style_fit:float;license_confidence:float;editability:float
    def score(self):return round(sum(asdict(self).values())/10,3)
def sha256(path):
    h=hashlib.sha256();
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()
def inspect_asset(path,license_confidence=1.0,semantic_fit=.9,style_fit=.9,intended_display_px=None):
    im=Image.open(path).convert('RGBA');w,h=im.size;gray=im.convert('RGB').convert('L');contrast=min(1,ImageStat.Stat(gray).stddev[0]/64);est=ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).mean[0]/255;alpha=list(im.getchannel('A').get_flattened_data());transparent=sum(a<250 for a in alpha)/max(1,len(alpha));resolution=min(1,min(w,h)/max(1,intended_display_px)) if intended_display_px else min(1,(w*h)/(1400*1400));realism=min(1,.45+contrast*.35+min(1,est*4)*.2);material=min(1,.5+contrast*.3+min(1,est*5)*.2);bgsep=min(1,.45+transparent*.9);edit=min(1,.55+transparent*.75);fit=AssetFitness(resolution*10,realism*10,8.5,8.5,bgsep*10,material*10,semantic_fit*10,style_fit*10,license_confidence*10,edit*10);return {'path':str(path),'width':w,'height':h,'sha256':sha256(path),'fitness':asdict(fit),'score':fit.score(),'alpha_fraction':round(transparent,4),'measured':{'contrast':round(contrast,4),'edge_signal':round(est,4),'intended_display_px':intended_display_px}}
def provenance_record(path,source_type,source,license_name,transformations=None):return {'asset_id':Path(path).stem,'source_type':source_type,'source':source,'license':license_name,'license_confidence':1.0,'sha256':sha256(path),'transformations':transformations or [],'production_path':str(path)}
