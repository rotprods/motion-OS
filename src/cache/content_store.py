from pathlib import Path
import hashlib,json,shutil
class ContentStore:
    def __init__(self,root):self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
    def key(self,payload):return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def path(self,key):return self.root/key[:2]/key[2:]
    def manifest(self,key,payload):d=self.path(key);d.mkdir(parents=True,exist_ok=True);(d/'manifest.json').write_text(json.dumps(payload,indent=2))
    def put_file(self,key,source,name='artifact.mp4'):d=self.path(key);d.mkdir(parents=True,exist_ok=True);out=d/name;shutil.copy(source,out);return out
