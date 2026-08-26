from dataclasses import dataclass
@dataclass
class ImpactRegion:roots:list;nodes:list;beats:list;start:float|None;end:float|None
def affected_subgraph(g,roots,max_hops=2,padding=.25):
    kinds={'USES','REQUIRES','DERIVED_FROM','PRECEDES','FAILS','PATCHED_BY'};seen=set(roots);frontier=[(r,0) for r in roots]
    while frontier:
        u,h=frontier.pop(0)
        if h>=max_hops:continue
        for e in g.edges:
            if e.kind not in kinds:continue
            v=e.target if e.source==u else (e.source if e.target==u and e.kind in {'USES','REQUIRES','DERIVED_FROM'} else None)
            if v and v not in seen:seen.add(v);frontier.append((v,h+1))
    beats=[];starts=[];ends=[]
    for i in seen:
        n=g.node(i)
        if n.kind=='Beat':beats.append(i);starts.append(n.attrs['start']);ends.append(n.attrs['end'])
    return ImpactRegion(list(roots),sorted(seen),sorted(beats),max(0,min(starts)-padding) if starts else None,max(ends)+padding if ends else None)
