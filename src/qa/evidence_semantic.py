from pathlib import Path
from dataclasses import dataclass
import hashlib,json
from .semantic_contract import validate_semantic_report
@dataclass
class EvidenceSemanticResult:provider:str;media_sha256:str;verified_media:bool;report:dict;authoritative_for_gate:bool
def sha256_file(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def load_evidence_review(review_path,media_path,*,trusted_provider_classes=None):
 r=json.loads(Path(review_path).read_text());expected=r.get('media',{}).get('sha256');actual=sha256_file(media_path);verified=bool(expected) and expected==actual;semantic={'scores':r['scores'],'defects':r.get('defects',[])};validate_semantic_report(semantic);pc=r.get('provider_class','unknown');auth=verified and pc in (trusted_provider_classes or set());return EvidenceSemanticResult(r.get('provider','unknown'),actual,verified,semantic,auth)
