from __future__ import annotations

from html import escape
from typing import Any, Mapping
import json


def _svg_element(el: Mapping[str, Any]) -> str:
    eid=escape(str(el["id"]), quote=True)
    kind=el.get("type","rect")
    if kind=="text":
        text=escape(str((el.get("text_state") or {}).get("content",el.get("text_content",""))))
        return f'<text id="{eid}" x="0" y="0">{text}</text>'
    if kind=="circle":
        return f'<circle id="{eid}" cx="0" cy="0" r="1" />'
    if kind=="path":
        return f'<path id="{eid}" d="{escape(str(el.get("d","")),quote=True)}" />'
    return f'<rect id="{eid}" x="0" y="0" width="1" height="1" />'


def emit_svg_js_player(recon: Mapping[str, Any]) -> str:
    """Emit deterministic SVG+JS frame player from reconstruction timeline data."""
    plan=recon["SVG_FRAME_RECON_PLAN"]
    assets=recon["SVG_ASSET_MAP"]
    timeline=recon["SVG_TIMELINE_FRAME_DATA"]
    width=assets["canvas"]["width"]; height=assets["canvas"]["height"]
    view_box=assets["canvas"].get("viewBox",f"0 0 {width} {height}")
    elements="\n".join(_svg_element(e) for e in assets.get("elements",[]) if e.get("vectorizable",True))
    payload=json.dumps(timeline,separators=(",",":"),ensure_ascii=False).replace("</","<\\/")
    fps=float(timeline["fps"])
    return f'''<!doctype html>
<meta charset="utf-8">
<svg id="stage" width="{width}" height="{height}" viewBox="{view_box}" xmlns="http://www.w3.org/2000/svg">{elements}</svg>
<script id="timeline" type="application/json">{payload}</script>
<script>
const data=JSON.parse(document.getElementById('timeline').textContent);
const fps={fps}; let frame=0;
function applyElement(s){{const el=document.getElementById(s.id);if(!el)return;el.style.display=s.visible===false?'none':'';if(s.opacity!=null)el.setAttribute('opacity',s.opacity);if(s.x!=null)el.setAttribute('x',s.x);if(s.y!=null)el.setAttribute('y',s.y);if(s.w!=null)el.setAttribute('width',s.w);if(s.h!=null)el.setAttribute('height',s.h);const t=s.transform||{{}};const tr=t.translate||[0,0], sc=t.scale||[1,1], rot=t.rotate||0;el.setAttribute('transform',`translate(${{tr[0]}} ${{tr[1]}}) rotate(${{rot}}) scale(${{sc[0]}} ${{sc[1]}})`);if(s.text_state&&s.text_state.content!=null&&el.tagName==='text')el.textContent=s.text_state.content;}}
function render(f){{const state=data.frame_data.find(x=>x.f===f);if(!state)return;(state.elements||[]).forEach(applyElement);}}
function seek(f){{frame=Math.max(0,Math.min(data.total_frames-1,f));render(frame);}}
window.MOTION_OS={{seek,render,fps,totalFrames:data.total_frames}};seek(0);
</script>'''
