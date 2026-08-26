from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib
import json


def build_raster_sequence_timeline(records: Sequence[Mapping[str, Any]], *, fps: float, width: int, height: int) -> dict[str, Any]:
    """Exact/hybrid baseline for non-vectorizable source regions.

    This does not claim vector reconstruction. It preserves physical decoded frames as raster evidence and
    creates a deterministic frame timeline, which is an allowed representation under the reconstruction canon.
    """
    frames=[]
    for i,rec in enumerate(records):
        frame=int(rec.get("frame",i))
        sha=str(rec.get("sha256", ""))
        path=str(rec.get("path", ""))
        if not sha or not path:
            raise ValueError("each raster frame requires path + sha256")
        frames.append({"frame":frame,"at_ms":round(frame*1000/fps),"path":path,"sha256":sha})
    payload={
        "schema":"motion-os.raster-frame-reconstruction/v1",
        "mode":"exact_raster_sequence",
        "fps":float(fps),
        "width":int(width),
        "height":int(height),
        "total_frames":len(frames),
        "duration_ms":round(len(frames)*1000/fps),
        "frames":frames,
        "fidelity_claim":"decoded_frame_sequence_replay; not vectorized",
    }
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"))
    payload["timeline_sha256"]=hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def emit_raster_sequence_player(timeline: Mapping[str, Any], *, relative_prefix: str = "") -> str:
    """Emit deterministic HTML/JS frame player. Frames remain individual raster assets, never CSS-blurred."""
    data=json.dumps(dict(timeline),ensure_ascii=False,separators=(",",":"))
    prefix=json.dumps(relative_prefix)
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><style>
html,body{{margin:0;background:#000;width:100%;height:100%;display:grid;place-items:center;overflow:hidden}}
#frame{{width:{int(timeline['width'])}px;height:{int(timeline['height'])}px;object-fit:contain;image-rendering:auto}}
</style></head><body><img id='frame' alt='exact raster reconstruction frame'/>
<script>
const TL={data}; const prefix={prefix}; const img=document.getElementById('frame');
let f=0; let start=null; let raf=0;
const src=i=>prefix+TL.frames[i].path;
function setFrame(i){{f=Math.max(0,Math.min(TL.total_frames-1,i|0)); img.src=src(f); img.dataset.frame=String(f);}}
function tick(ts){{if(start===null)start=ts; const elapsed=ts-start; const next=Math.min(TL.total_frames-1,Math.floor(elapsed*TL.fps/1000)); if(next!==f)setFrame(next); if(next<TL.total_frames-1)raf=requestAnimationFrame(tick);}}
window.motionOS={{timeline:TL,setFrame,play:()=>{{cancelAnimationFrame(raf);start=null;raf=requestAnimationFrame(tick)}},stop:()=>cancelAnimationFrame(raf)}};
setFrame(0);
</script></body></html>"""


def verify_raster_records(records: Sequence[Mapping[str, Any]]) -> list[str]:
    errors=[]
    for rec in records:
        path=Path(str(rec.get("path", "")))
        expected=str(rec.get("sha256", ""))
        if not path.exists():
            errors.append(f"missing:{path}")
            continue
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=expected:
            errors.append(f"sha_mismatch:frame={rec.get('frame')}:expected={expected}:actual={actual}")
    return errors
