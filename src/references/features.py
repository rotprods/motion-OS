from pathlib import Path
from PIL import Image,ImageStat,ImageFilter
import math
def extract_visual_dna(path):
    im=Image.open(path).convert('RGB').resize((320,568));g=im.convert('L');stat=ImageStat.Stat(im);gs=ImageStat.Stat(g);edge=ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).mean[0]/255;hist=g.histogram();total=sum(hist);entropy=-sum((c/total)*math.log2(c/total) for c in hist if c)
    return {'source':str(path),'composition':{'edge_density_proxy':round(edge,4),'negative_space_proxy':round(max(0,1-edge*4),4)},'palette':{'mean_rgb':[round(x,1) for x in stat.mean]},'material':{'contrast':round(gs.stddev[0]/64,4),'entropy':round(entropy,4)},'motion_grammar':'unknown_from_still','camera_grammar':'inferred_still','confidence':.72}
def diversity_select(items,k=4):
    if len(items)<=k:return items
    selected=[items[0]]
    def dist(a,b):
        ar=a['palette']['mean_rgb'];br=b['palette']['mean_rgb'];return sum((x-y)**2 for x,y in zip(ar,br))**.5+abs(a['composition']['edge_density_proxy']-b['composition']['edge_density_proxy'])*255
    while len(selected)<k:
        cand=max((x for x in items if x not in selected),key=lambda x:min(dist(x,s) for s in selected));selected.append(cand)
    return selected
