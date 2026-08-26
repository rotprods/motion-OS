from __future__ import annotations
from dataclasses import dataclass, asdict
import subprocess, hashlib, json
@dataclass
class RendererCapabilities:
    name:str; available:bool; supports:dict; evidence:dict
class RendererContract:
    name='base'
    def capabilities(self):raise NotImplementedError
    def validate_environment(self):return self.capabilities()
    def render_master(self,*a,**k):raise NotImplementedError
    def render_region(self,*a,**k):raise NotImplementedError
    def render_frame(self,*a,**k):raise NotImplementedError
    def estimate_cost(self,seconds):return {'seconds':seconds,'estimated_cost':0.0}
    def cache_key(self,payload):return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    def healthcheck(self):c=self.capabilities();return {'renderer':self.name,'ok':c.available,'capabilities':asdict(c)}
def command_version(cmd):
    try:r=subprocess.run(cmd,capture_output=True,text=True,timeout=8);return {'ok':r.returncode==0,'stdout':(r.stdout or r.stderr).strip()[:500],'returncode':r.returncode}
    except Exception as e:return {'ok':False,'error':str(e)}
class EnvironmentRenderer(RendererContract):
    def __init__(self,name,commands,supports):self.name=name;self.commands=commands;self._supports=supports
    def capabilities(self):
        evidence={k:command_version(v) for k,v in self.commands.items()};return RendererCapabilities(self.name,all(v.get('ok') for v in evidence.values()),self._supports,evidence)
def detect_renderers():
    hyper=EnvironmentRenderer('hyperframes',{'cli':['bash','-lc','command -v hyperframes || npx --offline hyperframes --version']},{'svg':True,'html':True,'kinetic_typography':True,'partial_render':True,'audio':True,'3d':'limited'})
    rem=EnvironmentRenderer('remotion',{'cli':['bash','-lc','command -v remotion || npx --offline remotion --version']},{'exact_typography':True,'ui':True,'charts':True,'partial_render':True,'audio':True})
    web=EnvironmentRenderer('chromium_web',{'chromium':['chromium','--version'],'ffmpeg':['ffmpeg','-version']},{'html':True,'svg':True,'deterministic_frames':True,'audio':True,'partial_render':True,'3d':'css_2_5d'})
    return {r.name:r.capabilities() for r in (hyper,rem,web)}
