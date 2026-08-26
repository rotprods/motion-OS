from dataclasses import dataclass,asdict
@dataclass
class Job:id:str;kind:str;status:str;priority:int;deps:list[str];payload:dict
class GraphScheduler:
    def __init__(self):self.jobs={}
    def add(self,j):
        if j.id in self.jobs:raise ValueError(f'Duplicate job {j.id}')
        self.jobs[j.id]=j
    def ready(self):
        done={i for i,j in self.jobs.items() if j.status=='DONE'};return sorted([j for j in self.jobs.values() if j.status=='PENDING' and set(j.deps)<=done],key=lambda j:(-j.priority,j.id))
    def mark(self,i,status):self.jobs[i].status=status
    def to_dict(self):return {'jobs':[asdict(j) for j in self.jobs.values()]}
