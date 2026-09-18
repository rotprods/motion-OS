from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.compilers.hyperframes import HyperFramesSpec, emit_hyperframes_project
from src.compilers.lottie import compile_vector_subgraph_to_lottie, player_roundtrip_contract

HF = ROOT / "runtime" / "hyperframes"
LOT = ROOT / "runtime" / "lottie"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_hyperframes() -> dict:
    HF.mkdir(parents=True, exist_ok=True)
    spec = HyperFramesSpec(
        width=640,
        height=360,
        fps=30,
        duration_ms=3000,
        scenes=(
            {
                "id": "heterogeneous_base",
                "startMs": 0,
                "endMs": 3000,
                "layers": [
                    {
                        "id": "hf_hero",
                        "class": "HERO",
                        "z": 1,
                        "attentionRole": "primary",
                        "data": {"text": "MOTION.OS", "provenance": ["p3.3-fixture"]},
                    }
                ],
            },
        ),
        timeline=(
            {"id":"hf_hero:entry","sceneId":"heterogeneous_base","target":"hf_hero","atMs":0,"durationMs":900,"action":"entry","ease":"power3.out","channels":{"opacity":1,"scale":1.08}},
            {"id":"hf_hero:settle","sceneId":"heterogeneous_base","target":"hf_hero","atMs":900,"durationMs":1200,"action":"settle","ease":"power2.inOut","channels":{"scale":1.0}},
            {"id":"hf_hero:exit","sceneId":"heterogeneous_base","target":"hf_hero","atMs":2400,"durationMs":600,"action":"exit","ease":"power2.in","channels":{"opacity":0.7,"scale":0.96}},
        ),
        provenance=("PR#62@17da8a190a4492f1193716fa864bcd838bfcfd7b", "P3.3"),
    )
    emitted = emit_hyperframes_project(spec)
    files = {}
    for name, text in emitted.items():
        path = HF / name
        path.write_text(text, encoding="utf-8")
        files[name] = sha256(path.read_bytes())
    evidence = {"schema":"motion-os.heterogeneous-hyperframes/v1","spec_sha256":spec.content_hash(),"files":files,"expected_frames":90,"fps":30,"width":640,"height":360}
    (HF / "compiler_evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return evidence


def ring_shapes() -> list[dict]:
    return [{"ty":"gr","nm":"Animated Ring","it":[
        {"d":1,"ty":"el","s":{"a":0,"k":[180,180]},"p":{"a":0,"k":[0,0]},"nm":"Ellipse Path 1"},
        {"ty":"st","c":{"a":0,"k":[1.0,0.26,0.08,1.0]},"o":{"a":0,"k":100},"w":{"a":0,"k":18},"lc":2,"lj":2,"ml":4,"bm":0,"nm":"Stroke 1"},
        {"ty":"tm","s":{"a":0,"k":0},"e":{"a":1,"k":[{"i":{"x":[0.667],"y":[1.0]},"o":{"x":[0.333],"y":[0.0]},"t":0,"s":[5],"e":[100]},{"t":89,"s":[100]}]},"o":{"a":0,"k":0},"m":1,"nm":"Trim Paths 1"},
        {"ty":"tr","p":{"a":0,"k":[0,0]},"a":{"a":0,"k":[0,0]},"s":{"a":0,"k":[100,100]},"r":{"a":0,"k":0},"o":{"a":0,"k":100},"sk":{"a":0,"k":0},"sa":{"a":0,"k":0},"nm":"Transform"}
    ]}]


def lottie_html() -> str:
    return """<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:transparent}#stage{width:640px;height:360px;background:transparent}</style></head><body><div id='stage'></div><script src='./lottie.min.js'></script><script>
(async()=>{const data=await fetch('./animation.json').then(r=>r.json());const animation=lottie.loadAnimation({container:document.getElementById('stage'),renderer:'svg',loop:false,autoplay:false,animationData:JSON.parse(JSON.stringify(data)),rendererSettings:{clearCanvas:true,preserveAspectRatio:'xMidYMid meet'}});animation.addEventListener('DOMLoaded',()=>{window.__animation=animation;window.__seek=(frame)=>{animation.goToAndStop(frame,true);return {frame:Math.round(animation.currentFrame),total:Math.round(animation.totalFrames),svg:document.querySelectorAll('#stage svg').length};};document.documentElement.dataset.ready='true';});})().catch(e=>{document.documentElement.dataset.ready='error';document.documentElement.dataset.error=String(e&&e.message||e)});
</script></body></html>"""


def build_lottie() -> dict:
    LOT.mkdir(parents=True, exist_ok=True)
    doc = compile_vector_subgraph_to_lottie([{"id":"runtime_ring","type":"shape","features":["transform","stroke","trim_path"],"data":{"transform":{"position":[320,180,0]},"shapes":ring_shapes()}}], width=640,height=360,fps=30,in_frame=0,out_frame=90,markers=[{"tm":0,"cm":"start","dr":0},{"tm":89,"cm":"end","dr":0}])
    contract = player_roundtrip_contract(doc, player="lottie-web")
    animation = json.dumps(doc, sort_keys=True, separators=(",",":"), ensure_ascii=False)+"\n"
    (LOT/"animation.json").write_text(animation, encoding="utf-8")
    (LOT/"player_contract.json").write_text(json.dumps(contract,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (LOT/"index.html").write_text(lottie_html(),encoding="utf-8")
    evidence={"schema":"motion-os.heterogeneous-lottie/v1","document_sha256":contract["document_sha256"],"animation_file_sha256":sha256((LOT/"animation.json").read_bytes()),"expected_frame_count":90,"fps":30,"width":640,"height":360}
    (LOT/"compiler_evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return evidence


def main() -> int:
    print(json.dumps({"hyperframes":build_hyperframes(),"lottie":build_lottie()},indent=2,sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())
