from PIL import Image
from src.assets.intelligence import inspect_asset

def test_resolution_scored_against_intended_use(tmp_path):
    asset=tmp_path/'hero.png'
    Image.new('RGBA',(570,615),(140,140,140,255)).save(asset)
    a=inspect_asset(asset,intended_display_px=520)
    assert a['fitness']['resolution']>=10.0
