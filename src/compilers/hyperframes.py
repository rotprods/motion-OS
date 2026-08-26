from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import hashlib, json

@dataclass(frozen=True)
class HyperFramesSpec:
    width: int
    height: int
    fps: int
    duration_ms: int
    scenes: tuple[dict[str, Any], ...]
    timeline: tuple[dict[str, Any], ...]
    provenance: tuple[str, ...]

    def to_dict(self):
        d=asdict(self); d["scenes"]=list(self.scenes); d["timeline"]=list(self.timeline); d["provenance"]=list(self.provenance); return d
    def content_hash(self):
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True, separators=(",",":")).encode()).hexdigest()

def _data(node):
    a=getattr(node,"attrs",{}) or {}; return a.get("data",a)

def compile_editing_graph_to_hyperframes(graph, *, width=1080, height=1920, fps=30) -> HyperFramesSpec:
    scenes=[]; timeline=[]; provenance=set(); max_end=0
    for n in graph.nodes:
        if n.kind=="Asset":
            provenance.update((_data(n).get("provenance") or []))
    for scene in sorted([n for n in graph.nodes if n.kind=="Scene"], key=lambda n:(_data(n).get("start_ms",0),n.id)):
        sd=_data(scene); start=int(sd.get("start_ms",0)); end=int(sd.get("end_ms",start)); max_end=max(max_end,end)
        layers=[]
        for e in graph.edges:
            if e.source!=scene.id or e.kind!="CONTAINS": continue
            child=graph.node(e.target); cd=_data(child)
            if child.kind=="Layer":
                layers.append({"id":child.id,"class":cd.get("layer_class","MIDGROUND"),"z":int(cd.get("z",4)),"attentionRole":cd.get("attention_role","secondary"),"data":cd})
                for phase in ("entry","settle","exit"):
                    event=cd.get(phase)
                    if isinstance(event,dict):
                        timeline.append({
                            "id":f"{child.id}:{phase}", "sceneId":scene.id, "target":child.id,
                            "atMs":start+int(event.get("at_ms",0)), "durationMs":int(event.get("duration_ms",0)),
                            "action":event.get("action",phase), "ease":event.get("ease","power3.out"),
                            "channels":event.get("channels",{}),
                        })
        scenes.append({"id":scene.id,"startMs":start,"endMs":end,"layers":sorted(layers,key=lambda x:(x["z"],x["id"]))})
    timeline.sort(key=lambda x:(x["atMs"],x["id"]))
    return HyperFramesSpec(width,height,fps,max_end,tuple(scenes),tuple(timeline),tuple(sorted(provenance)))

def emit_hyperframes_project(spec: HyperFramesSpec) -> dict[str,str]:
    data=json.dumps(spec.to_dict(),indent=2,ensure_ascii=False)
    html="""<!doctype html><html><head><meta charset=\"utf-8\"><style>
html,body,#stage{margin:0;width:100%;height:100%;overflow:hidden;background:#000}
#stage{position:relative}.layer{position:absolute;inset:0}
</style></head><body><div id=\"stage\"></div>
<script type=\"module\" src=\"./motion.js\"></script></body></html>
"""
    js="""import gsap from 'gsap';
import spec from './motion-spec.json' with {type:'json'};
const stage=document.querySelector('#stage');
for(const scene of spec.scenes){for(const l of scene.layers){const el=document.createElement('div');el.id=l.id;el.className='layer';el.dataset.sceneId=scene.id;el.style.zIndex=String(l.z);stage.appendChild(el);}}
const tl=gsap.timeline({paused:true});
for(const e of spec.timeline){const target='#'+CSS.escape(e.target); const vars={duration:e.durationMs/1000,ease:e.ease,...e.channels}; tl.to(target,vars,e.atMs/1000);}
window.__MOTION_OS__={spec,timeline:tl,seekMs:(ms)=>tl.time(ms/1000,false)};
"""
    return {"index.html":html,"motion.js":js,"motion-spec.json":data+"\n"}

def build_hyperframes_render_contract(spec: HyperFramesSpec, *, output="out/master.mp4"):
    return {"renderer":"hyperframes","authority":"compiler_ready","output":output,"duration_ms":spec.duration_ms,"fps":spec.fps,"width":spec.width,"height":spec.height,"spec_hash":spec.content_hash(),"deterministic_timeline":True}
