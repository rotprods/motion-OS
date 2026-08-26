from dataclasses import dataclass
@dataclass
class CandidateResult:id:str;metrics:dict;normalized:dict;fitness:float;pareto:bool;promoted:bool=False
DIRECTIONS={'outside_invariance':False,'boundary_continuity':False,'motion_energy':True,'contrast':True,'edge_density':True,'entropy':True,'risk':False};WEIGHTS={'outside_invariance':.22,'boundary_continuity':.18,'motion_energy':.16,'contrast':.12,'edge_density':.10,'entropy':.10,'risk':.12}
def norm(vals,higher=True):
    lo=min(vals);hi=max(vals)
    if hi-lo<1e-9:return [1.0]*len(vals)
    x=[(v-lo)/(hi-lo) for v in vals];return x if higher else [1-v for v in x]
def pareto_front(rows):
    front=[]
    for i,a in enumerate(rows):
        dominated=False
        for j,b in enumerate(rows):
            if i==j:continue
            allbe=True;strict=False
            for k,higher in DIRECTIONS.items():
                av,bv=a['metrics'][k],b['metrics'][k]
                if higher:
                    if bv<av:allbe=False;break
                    if bv>av:strict=True
                else:
                    if bv>av:allbe=False;break
                    if bv<av:strict=True
            if allbe and strict:dominated=True;break
        if not dominated:front.append(a['id'])
    return set(front)
def rank(rows):
    normalized={r['id']:{} for r in rows}
    for k,higher in DIRECTIONS.items():
        for r,v in zip(rows,norm([r['metrics'][k] for r in rows],higher)):normalized[r['id']][k]=v
    front=pareto_front(rows);res=[]
    for r in rows:
        fit=sum(normalized[r['id']][k]*WEIGHTS[k] for k in WEIGHTS);res.append(CandidateResult(r['id'],r['metrics'],normalized[r['id']],round(fit,4),r['id'] in front))
    res.sort(key=lambda x:(not x.pareto,-x.fitness))
    if res:res[0].promoted=True
    return res
