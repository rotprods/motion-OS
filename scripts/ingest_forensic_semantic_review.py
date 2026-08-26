#!/usr/bin/env python3
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.graph.model import MotionGraph
from src.graph.runtime_mutation import materialize_defects_and_patches
from src.graph.patch_planner import plan_patches
from src.qa.evidence_semantic import load_evidence_review
from src.qa.semantic_contract import release_gate
review=ROOT/'forensics/semantic_review_v07.json'; media=Path('/mnt/data/MOTION_OS_V07/data/runs/20260823_090440_v07_60dd42/working_master.mp4'); graph_src=Path('/mnt/data/MOTION_OS_V07/data/runs/20260823_090440_v07_60dd42/graph_v07.json')
result=load_evidence_review(review,media,trusted_provider_classes={'external_multimodal_evidence'}); g=MotionGraph.load(graph_src); patches=plan_patches(result.report['scores'],result.report['defects'],target=9.0,limit=8); mutation=materialize_defects_and_patches(g,8,result.report['defects'],patches); graph_out=ROOT/'evidence/motion_graph.semantic_v08.json'; g.dump(graph_out); gate=release_gate([],[],result.report,target=9.0)
out={'media_verified':result.verified_media,'provider':result.provider,'authoritative_for_this_gate':result.authoritative_for_gate,'release_gate':gate,'patches':patches,'graph_mutation':mutation,'graph_validation':g.validate(),'graph_output':str(graph_out)}; (ROOT/'forensics/semantic_graph_mutation_v08.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)); print(json.dumps(out,indent=2,ensure_ascii=False))
