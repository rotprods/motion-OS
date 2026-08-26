from dataclasses import dataclass,asdict
from pathlib import Path
from typing import Any
import hashlib,json
@dataclass
class AssetRecord:
    id:str;path:str;role:str;source_type:str;source_uri:str|None;license:str;license_verified:bool;generated_by:str|None=None;sha256:str|None=None;attrs:dict[str,Any]|None=None
    def fingerprint(self):
        p=Path(self.path)
        if p.exists() and p.is_file():self.sha256=hashlib.sha256(p.read_bytes()).hexdigest()
        return self
def coverage(records):return 1.0 if not records else sum(1 for r in records if r.license_verified and bool(r.license))/len(records)
def dump_registry(records,path):
    data={'assets':[asdict(r.fingerprint()) for r in records],'provenance_coverage':coverage(records)};Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8');return data
