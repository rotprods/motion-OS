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
    """Emit a standalone HyperFrames composition executable by the CLI.

    HyperFrames lints the standalone HTML surface, so the synchronous timeline
    registration is emitted inline rather than hidden behind an external script.
    ``motion.js`` remains an exact runtime-source evidence copy and
    ``motion-spec.json`` remains the deterministic compiler projection.
    """
    if spec.width <= 0 or spec.height <= 0 or spec.fps <= 0 or spec.duration_ms <= 0:
        raise ValueError("HyperFrames spec requires positive width/height/fps/duration")

    data=json.dumps(spec.to_dict(),indent=2,ensure_ascii=False)
    compact=json.dumps(spec.to_dict(),sort_keys=True,separators=(",",":"),ensure_ascii=False)
    duration_s=spec.duration_ms/1000
    js=f"""'use strict';
const spec={compact};
const root=document.querySelector('#motion-os-root');
if(!root) throw new Error('motion-os root composition missing');
if(!window.gsap) throw new Error('GSAP runtime missing');
for(const scene of spec.scenes){{
  for(const layer of scene.layers){{
    const el=document.createElement('div');
    el.id=layer.id;
    el.className='layer';
    el.dataset.sceneId=scene.id;
    el.style.zIndex=String(layer.z);
    const label=document.createElement('div');
    label.className='layer-label';
    label.textContent=String((layer.data&&layer.data.text)||layer.id);
    el.appendChild(label);
    root.appendChild(el);
  }}
}}
window.__timelines=window.__timelines||{{}};
const tl=window.gsap.timeline({{paused:true}});
for(const event of spec.timeline){{
  const target='#'+CSS.escape(event.target);
  const vars={{duration:event.durationMs/1000,ease:event.ease,...event.channels}};
  tl.to(target,vars,event.atMs/1000);
}}
window.__timelines['motion-os-master']=tl;
window.__MOTION_OS__={{spec,timeline:tl,seekMs:(ms)=>tl.time(ms/1000,false)}};
"""
    html=f"""<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#090909}}
[data-composition-id=\"motion-os-master\"]{{position:relative;width:{spec.width}px;height:{spec.height}px;overflow:hidden;background:#090909;color:#f5f5f0;font-family:Arial,sans-serif}}
.layer{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;box-sizing:border-box}}
.layer-label{{font-size:max(20px,5vw);font-weight:700;letter-spacing:.04em;text-transform:uppercase}}
</style>
<script src=\"https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js\"></script>
</head>
<body>
<div id=\"motion-os-root\" data-composition-id=\"motion-os-master\" data-start=\"0\" data-duration=\"{duration_s:.6f}\" data-track-index=\"0\" data-width=\"{spec.width}\" data-height=\"{spec.height}\"></div>
<script>{js}</script>
</body>
</html>
"""
    return {"index.html":html,"motion.js":js,"motion-spec.json":data+"\n"}

def build_hyperframes_render_contract(spec: HyperFramesSpec, *, output="out/master.mp4"):
    expected_frames=round(spec.duration_ms*spec.fps/1000)
    return {
        "renderer":"hyperframes",
        "authority":"compiler_ready",
        "output":output,
        "duration_ms":spec.duration_ms,
        "fps":spec.fps,
        "width":spec.width,
        "height":spec.height,
        "expected_frames":expected_frames,
        "visual_duration_authority":"frame_count/fps",
        "spec_hash":spec.content_hash(),
        "deterministic_timeline":True,
    }
