from dataclasses import dataclass
@dataclass
class FitnessDecision:accepted:bool;global_delta:float;local_delta:float;regressions:list;reason:str
def compare(before,after,local_dimensions,regression_tolerance=.12,min_global_gain=.02):
    b,a=before['scores'],after['scores'];gd=round(after['score']-before['score'],3);ld=round(sum(a[k]-b[k] for k in local_dimensions),3);regs=[k for k in b if k in a and b[k]-a[k]>regression_tolerance];ok=not regs and ld>0 and gd>=min_global_gain;return FitnessDecision(ok,gd,ld,regs,'FITNESS_IMPROVED' if ok else ('REGRESSION_DETECTED' if regs else 'INSUFFICIENT_GAIN'))
