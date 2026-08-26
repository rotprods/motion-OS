#!/usr/bin/env python3
from pathlib import Path
import sys,json,datetime,uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.agents.pipeline import normalize_brief,choose_style
from src.renderers.prototype import render
from src.qa.scoring import heuristic_visual_scores,weighted_score,technical_gate
from src.qa.visual_metrics import inspect_frames,metric_gate
from src.graph.patch_planner import plan_patches
STYLES=['editorial_finance','swiss_brutalist','dark_technical','experimental_kinetic']
def main():
 raw=json.loads((ROOT/'examples/benchmark_brief.json').read_text());raw['fps']=15;bid=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6];bench=ROOT/'data/benchmarks'/bid;bench.mkdir(parents=True);results=[]
 for sid in STYLES:
  local=dict(raw);local['style']=sid;brief=normalize_brief(local);style=choose_style(brief);run=bench/sid;run.mkdir();meta=render(run,brief,style,1);metrics=inspect_frames(run/'iter_01'/'frames',brief['fps'],brief['duration']);technical=technical_gate(meta,{'width':1080,'height':1920,'fps':brief['fps'],'duration':brief['duration']});mdef=metric_gate(metrics);scores=heuristic_visual_scores(1,sid);advisory=weighted_score(scores);results.append({'style':sid,'render':meta,'technical_defects':technical,'visual_metrics':metrics,'metric_defects':mdef,'advisory_visual_score':advisory,'advisory_only':True,'release_authority':False,'patch_plan':plan_patches(scores,technical+mdef,target=9.0)})
 summary={'benchmark_id':bid,'styles':STYLES,'results':results,'release_gate':'BLOCKED_UNTIL_SEMANTIC_VISION_QA','notes':'Mechanical metrics are real. Advisory aesthetic scores are synthetic and cannot approve release.'};(bench/'benchmark_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({'benchmark_dir':str(bench),'release_gate':summary['release_gate']},indent=2))
if __name__=='__main__':main()
