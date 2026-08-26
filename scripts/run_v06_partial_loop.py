import sys,json,datetime,uuid,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.graph.model import MotionGraph,Node,Edge
from src.graph.impact import affected_subgraph
from src.graph.scheduler import GraphScheduler,Job
from src.renderers.partial import render_master,render_segment
from src.renderers.compositor import splice,probe
from src.qa.frame_metrics import compare_videos
from src.qa.multimodal_critic import FixtureProvider
from src.qa.release import release_gate
rid=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_v06_'+uuid.uuid4().hex[:6];run=ROOT/'data/runs'/rid;run.mkdir(parents=True);g=MotionGraph();g.add_node(Node('brief','Brief',{'duration':10,'fps':30}));g.add_node(Node('B004','Beat',{'start':4.3,'end':5.4}));g.add_node(Node('P_OCC','Primitive',{'name':'object_occlusion'}));g.add_edge(Edge('B004','P_OCC','USES'));impact=affected_subgraph(g,['B004'],2,.25);base={'headline_scale':1.0,'foreground_crop':1.0,'motion_blur':1.0,'occlusion_speed':1.0};patchp={'headline_scale':1.0,'foreground_crop':.82,'motion_blur':1.18,'occlusion_speed':.86};master=render_master(run/'master',10,30,base,'master');patch=render_segment(run/'patch',impact.start,impact.end,30,patchp,'patch');candidate=run/'candidate.mp4';splice(master['path'],patch['path'],impact.start,impact.end,candidate);inside=compare_videos(master['path'],candidate,[impact.start+.15,(impact.start+impact.end)/2,impact.end-.15]);outside=compare_videos(master['path'],candidate,[1,2.5,9.5]);mb=probe(master['path']);ma=probe(candidate);promote=inside['mean_mse']>20 and outside['mean_mse']<8 and abs(mb['duration']-ma['duration'])<=.05;working=run/'working_master.mp4';shutil.copy(candidate if promote else master['path'],working);critic=FixtureProvider(score=8.7).evaluate(working,{});gate=release_gate({'score':critic.score,'defects':critic.defects},critic.provider,9);result={'run_id':rid,'impact':impact.__dict__,'inside_compare':inside,'outside_compare':outside,'patch_promoted_to_working_master':promote,'semantic_critic':{'provider':critic.provider,'authoritative':critic.authoritative,'score':critic.score},'production_release':gate};(run/'v06_result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
