#!/usr/bin/env python3
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.graph.model import MotionGraph,Node,Edge
from src.graph.runtime_mutation import materialize_defects_and_patches
from src.graph.patch_planner import plan_patches
from src.qa.evidence_semantic import load_evidence_review
from src.qa.semantic_contract import release_gate
ap=argparse.ArgumentParser(); ap.add_argument('--review',required=True); ap.add_argument('--media',required=True); ap.add_argument('--out',required=True); args=ap.parse_args(); r=load_evidence_review(args.review,args.media,trusted_provider_classes={'external_multimodal_evidence'}); g=MotionGraph(); g.add_node(Node('brief','Brief',{'source':'v08_asset_slice'})); g.add_node(Node('style','Style',{'style_id':'editorial_finance'})); g.add_edge(Edge('brief','style','DERIVED_FROM',{}))
for i,(a,b) in enumerate([(0,1.2),(1.2,3.65),(3.65,5.0),(5.0,7.1),(7.1,10.0)],1):
 bid=f'B{i:03d}'; g.add_node(Node(bid,'Beat',{'start':a,'end':b})); g.add_edge(Edge('style',bid,'REQUIRES',{}))
g.add_node(Node('asset_coin','Asset',{'type':'generated_original','provenance':'verified'})); g.add_node(Node('renderer','Renderer',{'actual':'deterministic_asset_slice','production':False})); g.add_edge(Edge('asset_coin','renderer','USES',{})); patches=plan_patches(r.report['scores'],r.report['defects'],target=9.0,limit=8); mutation=materialize_defects_and_patches(g,1,r.report['defects'],patches); gate=release_gate([],[],r.report,target=9.0); out={'media_verified':r.verified_media,'provider':r.provider,'authoritative_for_gate':r.authoritative_for_gate,'release_gate':gate,'patches':patches,'graph_mutation':mutation,'graph_validation':g.validate()}; Path(args.out).write_text(json.dumps(out,indent=2,ensure_ascii=False)); graph=Path(args.out).with_suffix('.graph.json'); g.dump(graph); print(json.dumps(out,indent=2,ensure_ascii=False))
