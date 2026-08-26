import json
from pathlib import Path
ALLOWED_CP={'NOT_STARTED','SPECIFIED','PARTIAL','FUNCTIONAL','ROBUST','PRODUCTION','BLOCKED'}
def validate_weights(path):
 d=json.loads(Path(path).read_text());families=['global_domains','creative','engineering','autonomy','trust'];s={k:round(sum(float(v) for v in d[k].values()),6) for k in families};bad={k:v for k,v in s.items() if abs(v-1)>1e-6};return {'ok':not bad,'sums':s,'bad':bad}
def validate_checkpoints(path):
 rows=json.loads(Path(path).read_text());bad=[r for r in rows if r.get('status') not in ALLOWED_CP];ids=[r['id'] for r in rows];return {'ok':not bad and len(ids)==len(set(ids)),'count':len(rows),'invalid':bad}
def release_readiness(project_state_path,semantic_review_path):
 s=json.loads(Path(project_state_path).read_text());r=json.loads(Path(semantic_review_path).read_text());hard=[d for d in r.get('defects',[]) if d.get('severity') in {'P0','P1'}];return {'ready':s.get('release_status')=='READY' and not hard and r.get('mean_score',0)>=9,'state_release_status':s.get('release_status'),'semantic_mean':r.get('mean_score'),'hard_defects':hard}
