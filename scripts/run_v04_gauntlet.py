#!/usr/bin/env python3
from pathlib import Path
import sys,json,datetime,uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.agents.pipeline import normalize_brief,choose_style,storyboard,asset_plan
from src.graph.model import MotionGraph,Node,Edge
from src.graph.patch_planner import plan_patches
from src.graph.runtime_mutation import materialize_defects_and_patches
from src.renderers.prototype import render
from src.renderers.router import detect_capabilities,choose_renderer
from src.qa.scoring import heuristic_visual_scores,weighted_score,technical_gate
from src.qa.visual_metrics import inspect_frames,metric_gate
from src.qa.semantic_contract import release_gate

def main():
 raw=json.loads((ROOT/'examples/benchmark_brief.json').read_text());raw['fps']=15;rid=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_v04_'+uuid.uuid4().hex[:6];run=ROOT/'data/runs'/rid;run.mkdir(parents=True);brief=normalize_brief(raw);style=choose_style(brief);beats=storyboard(brief,style);caps=detect_capabilities();route=choose_renderer({'kinetic_type':True,'exact_text':True},caps);meta=render(run,brief,style,1);technical=technical_gate(meta,{'width':1080,'height':1920,'fps':brief['fps'],'duration':brief['duration']});metrics=inspect_frames(run/'iter_01'/'frames',brief['fps'],brief['duration']);measured=metric_gate(metrics);scores=heuristic_visual_scores(1,style['style_id']);patches=plan_patches(scores,technical+measured,target=9.0);g=MotionGraph();g.add_node(Node('brief','Brief',brief));g.add_node(Node('style','Style',style));g.add_edge(Edge('brief','style','DERIVED_FROM',{}));g.add_node(Node('renderer','Renderer',{'route':route,'actual_fixture':'native_prototype'}));mutation=materialize_defects_and_patches(g,1,technical+measured,patches);gate=release_gate(technical,measured,None,target=9.0);g.dump(run/'motion_graph.v04.json');result={'run_id':rid,'renderer_capabilities':[c.__dict__ for c in caps],'renderer_route':route,'technical':technical,'visual_metrics':metrics,'metric_defects':measured,'advisory_score':weighted_score(scores),'patches':patches,'graph_mutation':mutation,'graph_validation':g.validate(),'release_gate':gate,'semantic_report':None};(run/'v04_result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
