from __future__ import annotations
from dataclasses import dataclass, asdict
from numbers import Real
from typing import Any
import hashlib, json, math, re

_ALLOWED_GSAP_CHANNELS = frozenset({
    "x", "y", "z", "scale", "scaleX", "scaleY",
    "rotation", "rotationX", "rotationY", "opacity", "color", "backgroundColor",
})
_EASE_RE = re.compile(r"^[A-Za-z0-9_.(),+\-]{1,64}$")


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
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True, separators=(",",":"), allow_nan=False).encode()).hexdigest()


def _data(node):
    a=getattr(node,"attrs",{}) or {}; return a.get("data",a)


def _bounded_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def _safe_channels(value: object, event_id: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"HyperFrames channels must be an object: {event_id}")
    unknown=set(value)-_ALLOWED_GSAP_CHANNELS
    if unknown:
        raise ValueError(f"unsupported HyperFrames animation channels for {event_id}: {sorted(unknown)}")
    out:dict[str,Any]={}
    for key, raw in value.items():
        if isinstance(raw, bool):
            raise ValueError(f"HyperFrames animation channel cannot be boolean: {event_id}:{key}")
        if isinstance(raw, Real):
            number=float(raw)
            if not math.isfinite(number):
                raise ValueError(f"HyperFrames animation channel must be finite: {event_id}:{key}")
            out[key]=raw
        elif isinstance(raw, str):
            if not raw or len(raw)>256 or any(ord(char)<32 for char in raw):
                raise ValueError(f"HyperFrames animation channel string malformed: {event_id}:{key}")
            out[key]=raw
        else:
            raise ValueError(f"HyperFrames animation channel must be scalar: {event_id}:{key}")
    return out


def _safe_ease(value: object, event_id: str) -> str:
    if not isinstance(value,str) or _EASE_RE.fullmatch(value) is None:
        raise ValueError(f"HyperFrames ease malformed: {event_id}")
    return value


def compile_editing_graph_to_hyperframes(graph, *, width=1080, height=1920, fps=30) -> HyperFramesSpec:
    scenes=[]; timeline=[]; provenance=set(); max_end=0
    for n in graph.nodes:
        if n.kind=="Asset": provenance.update((_data(n).get("provenance") or []))
    for scene in sorted([n for n in graph.nodes if n.kind=="Scene"], key=lambda n:(_data(n).get("start_ms",0),n.id)):
        sd=_data(scene); start=_bounded_int(sd.get("start_ms",0),f"{scene.id}.start_ms"); end=_bounded_int(sd.get("end_ms",start),f"{scene.id}.end_ms")
        if start < 0 or end <= start: raise ValueError(f"invalid HyperFrames scene interval: {scene.id}")
        max_end=max(max_end,end)
        layers=[]
        for e in graph.edges:
            if e.source!=scene.id or e.kind!="CONTAINS": continue
            child=graph.node(e.target); cd=_data(child)
            if child.kind=="Layer":
                z=_bounded_int(cd.get("z",4),f"{child.id}.z")
                layers.append({"id":child.id,"class":cd.get("layer_class","MIDGROUND"),"z":z,"attentionRole":cd.get("attention_role","secondary"),"data":cd})
                for phase in ("entry","settle","exit"):
                    event=cd.get(phase)
                    if isinstance(event,dict):
                        event_id=f"{child.id}:{phase}"
                        at_ms=_bounded_int(event.get("at_ms",0),f"{event_id}.at_ms")
                        duration_ms=_bounded_int(event.get("duration_ms",0),f"{event_id}.duration_ms")
                        if at_ms < 0 or duration_ms < 0: raise ValueError(f"negative HyperFrames event timing: {event_id}")
                        timeline.append({"id":event_id,"sceneId":scene.id,"target":child.id,"atMs":start+at_ms,"durationMs":duration_ms,"action":event.get("action",phase),"ease":_safe_ease(event.get("ease","power3.out"),event_id),"channels":_safe_channels(event.get("channels",{}),event_id)})
        scenes.append({"id":scene.id,"startMs":start,"endMs":end,"layers":sorted(layers,key=lambda x:(x["z"],x["id"]))})
    timeline.sort(key=lambda x:(x["atMs"],x["id"]))
    return HyperFramesSpec(width,height,fps,max_end,tuple(scenes),tuple(timeline),tuple(sorted(provenance)))


def emit_hyperframes_project(spec: HyperFramesSpec) -> dict[str,str]:
    if spec.width <= 0 or spec.height <= 0 or spec.fps <= 0 or spec.duration_ms <= 0: raise ValueError("HyperFrames spec requires positive width/height/fps/duration")
    data=json.dumps(spec.to_dict(),indent=2,ensure_ascii=False,allow_nan=False); duration_s=spec.duration_ms/1000
    html=f"""<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><style>html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#090909}}[data-composition-id=\"motion-os-master\"]{{position:relative;width:{spec.width}px;height:{spec.height}px;overflow:hidden;background:#090909;color:#f5f5f0;font-family:Arial,sans-serif}}.layer{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;box-sizing:border-box}}.layer-label{{font-size:max(20px,5vw);font-weight:700;letter-spacing:.04em;text-transform:uppercase}}</style></head><body><div id=\"motion-os-root\" data-composition-id=\"motion-os-master\" data-start=\"0\" data-duration=\"{duration_s:.6f}\" data-track-index=\"0\" data-width=\"{spec.width}\" data-height=\"{spec.height}\"></div><script type=\"module\" src=\"./motion.js\"></script></body></html>"""
    js="""import gsap from 'gsap';
import spec from './motion-spec.json' with {type:'json'};
const root=document.querySelector('#motion-os-root');
if(!root) throw new Error('motion-os root composition missing');
for(const scene of spec.scenes){for(const layer of scene.layers){const el=document.createElement('div');el.id=layer.id;el.className='layer';el.dataset.sceneId=scene.id;el.style.zIndex=String(layer.z);const label=document.createElement('div');label.className='layer-label';label.textContent=String((layer.data&&layer.data.text)||layer.id);el.appendChild(label);root.appendChild(el);}}
window.__timelines=window.__timelines||{}; const tl=gsap.timeline({paused:true});
for(const event of spec.timeline){const target='#'+CSS.escape(event.target);const vars={duration:event.durationMs/1000,ease:event.ease,...event.channels};tl.to(target,vars,event.atMs/1000);}
window.__timelines['motion-os-master']=tl;window.__MOTION_OS__={spec,timeline:tl,seekMs:(ms)=>tl.time(ms/1000,false)};
"""
    return {"index.html":html,"motion.js":js,"motion-spec.json":data+"\n"}


def build_hyperframes_render_contract(spec: HyperFramesSpec, *, output="out/master.mp4"):
    expected_frames=round(spec.duration_ms*spec.fps/1000)
    return {"renderer":"hyperframes","authority":"compiler_ready","output":output,"duration_ms":spec.duration_ms,"fps":spec.fps,"width":spec.width,"height":spec.height,"expected_frames":expected_frames,"visual_duration_authority":"frame_count/fps","spec_hash":spec.content_hash(),"deterministic_timeline":True}
