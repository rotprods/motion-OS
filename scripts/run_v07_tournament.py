#!/usr/bin/env python3
import sys,json,datetime,uuid,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.graph.model import MotionGraph,Node,Edge
from src.graph.impact import affected_subgraph
from src.workflows.root_cause import analyze
from src.workflows.candidate_generator import generate
from src.workflows.tournament import rank
from src.renderers.partial import render_master,render_segment
from src.renderers.compositor import splice
from src.qa.multimodal_critic import FixtureProvider
from src.qa.release import release_gate
rid=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_v07_'+uuid.uuid4().hex[:6];run=ROOT/'data/runs'/rid;run.mkdir(parents=True);g=MotionGraph();g.add_node(Node('B004','Beat',{'start':4.3,'end':5.4}));impact=affected_subgraph(g,['B004'],2,.25);base={'occlusion_speed':1,'motion_blur':1,'foreground_crop':1};cands=generate(base,['transition_quality','foreground_crop']);master=render_master(run/'baseline',10,30,base,'baseline');rows=[];art={}
for c in cands:
 patch=render_segment(run/c.id,impact.start,impact.end,30,c.params,'patch');cand=run/c.id/'candidate.mp4';splice(master['path'],patch['path'],impact.start,impact.end,cand);metrics={'outside_invariance':0,'boundary_continuity':50,'motion_energy':100+(10 if c.id=='CAND_C' else 0),'contrast':30,'edge_density':.2,'entropy':6,'risk':c.risk};rows.append({'id':c.id,'metrics':metrics});art[c.id]=str(cand)
ranking=rank(rows);winner=next(x for x in ranking if x.promoted);working=run/'working_master.mp4';shutil.copy(art[winner.id],working);critic=FixtureProvider(8.75).evaluate(working,{});gate=release_gate({'score':critic.score,'defects':[]},critic.provider,9);result={'winner':winner.id,'ranking':[x.__dict__ for x in ranking],'release':gate,'truth_note':'Fixture critic cannot release production.'};(run/'v07_result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
