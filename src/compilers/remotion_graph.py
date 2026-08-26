from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import hashlib, json

LAYER_ORDER = {
    "ENVIRONMENT": 0, "BACKGROUND_GRAPHICS": 1, "FOOTAGE_PLATES": 2,
    "SUBJECT": 3, "MIDGROUND": 4, "PRIMARY_UI": 5, "TYPOGRAPHY": 6,
    "FOREGROUND": 7, "FX": 8, "CAPTIONS_BRAND": 9,
}

@dataclass(frozen=True)
class RemotionGraphSpec:
    composition_id: str
    fps: int
    width: int
    height: int
    duration_in_frames: int
    scenes: tuple[dict[str, Any], ...]
    assets: tuple[dict[str, Any], ...]
    provenance: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["scenes"] = list(self.scenes)
        d["assets"] = list(self.assets)
        d["provenance"] = list(self.provenance)
        return d

    def content_hash(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _data(node: Any) -> dict[str, Any]:
    attrs = getattr(node, "attrs", {}) or {}
    return attrs.get("data", attrs)

def compile_editing_graph_to_remotion(graph, *, composition_id="MotionOSStudio", fps=30, width=1080, height=1920) -> RemotionGraphSpec:
    scenes = []
    assets = []
    provenance = set()
    for n in graph.nodes:
        d = _data(n)
        if n.kind == "Asset":
            assets.append({"id": n.id, **d})
            provenance.update(d.get("provenance", []) or [])
    scene_nodes = sorted(
        [n for n in graph.nodes if n.kind == "Scene"],
        key=lambda n: (_data(n).get("start_ms", 0), n.id),
    )
    max_end_ms = 0
    for scene in scene_nodes:
        sd = _data(scene)
        start_ms = int(sd.get("start_ms", 0))
        end_ms = int(sd.get("end_ms", start_ms))
        max_end_ms = max(max_end_ms, end_ms)
        contained_ids = [e.target for e in graph.edges if e.source == scene.id and e.kind == "CONTAINS"]
        layers = []
        camera = None
        transition_in = None
        transition_out = None
        audio_links = []
        for node_id in contained_ids:
            child = graph.node(node_id)
            cd = _data(child)
            if child.kind == "Layer":
                layer_class = cd.get("layer_class", "MIDGROUND")
                layers.append({
                    "id": child.id,
                    "layerClass": layer_class,
                    "z": int(cd.get("z", LAYER_ORDER.get(layer_class, 4))),
                    "semanticRole": cd.get("semantic_role"),
                    "attentionRole": cd.get("attention_role", "secondary"),
                    "assetRef": cd.get("asset_ref"),
                    "entry": cd.get("entry"),
                    "settle": cd.get("settle"),
                    "exit": cd.get("exit"),
                    "rendererSupport": cd.get("renderer_support", []),
                    "data": cd,
                })
            elif child.kind == "CameraRig":
                camera = {"id": child.id, **cd}
            elif child.kind == "Transition":
                if cd.get("direction") == "out":
                    transition_out = {"id": child.id, **cd}
                else:
                    transition_in = {"id": child.id, **cd}
        for e in graph.edges:
            if e.source == scene.id and e.kind == "SYNC_WITH":
                target = graph.node(e.target)
                audio_links.append({"id": target.id, "kind": target.kind, **_data(target)})
        layers.sort(key=lambda x: (x["z"], x["id"]))
        from_frame = round(start_ms * fps / 1000)
        to_frame = round(end_ms * fps / 1000)
        scenes.append({
            "id": scene.id,
            "fromFrame": from_frame,
            "durationInFrames": max(1, to_frame - from_frame),
            "camera": camera,
            "layers": layers,
            "transitionIn": transition_in,
            "transitionOut": transition_out,
            "audio": sorted(audio_links, key=lambda x: (x.get("at_ms", 0), x["id"])),
        })
    return RemotionGraphSpec(
        composition_id=composition_id,
        fps=fps, width=width, height=height,
        duration_in_frames=max(1, round(max_end_ms * fps / 1000)),
        scenes=tuple(scenes), assets=tuple(sorted(assets, key=lambda x: x["id"])),
        provenance=tuple(sorted(provenance)),
    )

def emit_remotion_project_files(spec: RemotionGraphSpec) -> dict[str, str]:
    payload = json.dumps(spec.to_dict(), indent=2, ensure_ascii=False)
    root = """import React from 'react';
import {Composition} from 'remotion';
import {MotionOSComposition} from './MotionOSComposition';
import spec from './motion-spec.json';

export const RemotionRoot: React.FC = () => (
  <Composition
    id={spec.composition_id}
    component={MotionOSComposition}
    durationInFrames={spec.duration_in_frames}
    fps={spec.fps}
    width={spec.width}
    height={spec.height}
    defaultProps={{spec}}
  />
);
"""
    comp = """import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';

export const MotionOSComposition: React.FC<{spec:any}> = ({spec}) => (
  <AbsoluteFill>
    {spec.scenes.map((scene:any) => (
      <Sequence key={scene.id} from={scene.fromFrame} durationInFrames={scene.durationInFrames}>
        <AbsoluteFill data-scene-id={scene.id}>
          {scene.layers.map((layer:any) => (
            <div key={layer.id} data-layer-id={layer.id} style={{position:'absolute', inset:0, zIndex:layer.z}} />
          ))}
        </AbsoluteFill>
      </Sequence>
    ))}
  </AbsoluteFill>
);
"""
    return {
        "motion-spec.json": payload + "\n",
        "Root.tsx": root,
        "MotionOSComposition.tsx": comp,
    }

def build_ssr_render_contract(spec: RemotionGraphSpec, *, entry_point="src/index.ts", output="out/master.mp4") -> dict[str, Any]:
    return {
        "renderer": "remotion",
        "authority": "compiler_ready",
        "pipeline": ["bundle", "selectComposition", "renderMedia"],
        "entry_point": entry_point,
        "composition_id": spec.composition_id,
        "output": output,
        "codec": "h264",
        "input_props": {"spec_hash": spec.content_hash()},
        "expected": {
            "fps": spec.fps, "width": spec.width, "height": spec.height,
            "duration_in_frames": spec.duration_in_frames,
        },
    }
