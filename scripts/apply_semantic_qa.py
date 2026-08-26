#!/usr/bin/env python3
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.graph.model import MotionGraph
from src.graph.runtime_mutation import materialize_defects_and_patches,link_iterations
from src.graph.patch_planner import plan_patches
from src.qa.semantic_contract import validate_semantic_report, release_gate
from src.qa.visual_metrics import inspect_frames,metric_gate
from src.qa.scoring import technical_gate

def main(run_path,iteration):
    run=Path(run_path); iteration=int(iteration)
    graph_path=run/'motion_graph.v04.json' if iteration==1 else run/f'motion_graph.iter_{iteration-1:02d}.json'
    g=MotionGraph.load(graph_path)
    report=json.loads((run/f'iter_{iteration:02d}'/'semantic_report.json').read_text()); validate_semantic_report(report)
    patches=plan_patches(report['scores'],report['defects'],target=9.0,limit=6)
    if iteration>1: link_iterations(g,iteration-1,iteration)
    materialize_defects_and_patches(g,iteration,report['defects'],patches)
    metrics=inspect_frames(run/f'iter_{iteration:02d}'/'frames',15,10)
    mdef=metric_gate(metrics); tdef=[]
    gate=release_gate(tdef,mdef,report,target=9.0)
    out=run/f'motion_graph.iter_{iteration:02d}.json'; g.dump(out)
    result={'iteration':iteration,'semantic_report':report,'patches':patches,'metric_defects':mdef,'release_gate':gate,'graph_validation':g.validate()}
    (run/f'iter_{iteration:02d}'/'semantic_gate.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main(sys.argv[1],sys.argv[2])
