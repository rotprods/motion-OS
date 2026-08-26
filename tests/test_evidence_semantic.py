import json,hashlib
from src.qa.evidence_semantic import load_evidence_review
def test_evidence_review_binds_to_media(tmp_path):
 media=tmp_path/'x.bin';media.write_bytes(b'abc');sha=hashlib.sha256(b'abc').hexdigest();scores={k:5.0 for k in ['focal_hierarchy','composition_balance','typography_integrity','style_coherence','asset_realism','motion_motivation','transition_motivation','narrative_clarity','brand_adherence','final_frame_memorability']};review=tmp_path/'r.json';review.write_text(json.dumps({'provider':'test','provider_class':'trusted','media':{'sha256':sha},'scores':scores,'defects':[]}));r=load_evidence_review(review,media,trusted_provider_classes={'trusted'});assert r.verified_media and r.authoritative_for_gate
