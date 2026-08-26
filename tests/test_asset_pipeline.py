from PIL import Image
from src.assets.pipeline import crop_asset,remove_border_background
def test_asset_crop_and_alpha(tmp_path):
 src=tmp_path/'s.png';Image.new('RGB',(20,20),'white').save(src);crop=tmp_path/'c.png';out=tmp_path/'a.png';crop_asset(src,(0,0,20,20),crop);remove_border_background(crop,out,tolerance=5);assert Image.open(out).mode=='RGBA'
