from dataclasses import dataclass
@dataclass
class GauntletPolicy:target_score:float=9.0;max_iterations:int=6
def next_action(score,p0,p1,iteration,improving,policy=GauntletPolicy()):
    if p0 or p1:return 'ITERATE' if iteration<policy.max_iterations else 'ESCALATE'
    if score>=policy.target_score:return 'ACCEPT'
    if iteration>=policy.max_iterations:return 'ESCALATE'
    return 'ITERATE' if improving else 'REBUILD'
