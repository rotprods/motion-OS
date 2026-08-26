#!/usr/bin/env python3
from pathlib import Path
import sys,json,uuid,datetime,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.agents.pipeline import normalize_brief,choose_style,storyboard,asset_plan,render_plan
from src.renderers.prototype import render
from src.qa.scoring import heuristic_visual_scores,weighted_score,technical_gate
from src.workflows.gauntlet import next_action,GauntletPolicy
def main():
 raw=json.loads((ROOT/'examples/benchmark_brief.json').read_text());rid=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6];run=ROOT/'data/runs'/rid;run.mkdir(parents=True);brief=normalize_brief(raw);style=choose_style(brief);policy=GauntletPolicy();history=[];last=None
 for iteration in range(1,policy.max_iterations+1):
  meta=render(run,brief,style,iteration);defects=technical_gate(meta,{'width':1080,'height':1920,'fps':brief['fps'],'duration':brief['duration']});scores=heuristic_visual_scores(iteration,style['style_id']);score=weighted_score(scores);action=next_action(score,sum(d['severity']=='P0' for d in defects),sum(d['severity']=='P1' for d in defects),iteration,True if last is None else score>last,policy);history.append({'iteration':iteration,'score':score,'action':action,'qa_mode':'prototype_heuristic'});
  if action=='ACCEPT':shutil.copy(meta['path'],run/'final.mp4');break
  last=score
 print(json.dumps({'run_dir':str(run),'history':history},indent=2))
if __name__=='__main__':main()
