from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


LAYER_ORDER = {
    "ENVIRONMENT": 0,
    "BACKGROUND_GRAPHICS": 1,
    "FOOTAGE_PLATES": 2,
    "SUBJECT": 3,
    "MIDGROUND": 4,
    "PRIMARY_UI": 5,
    "TYPOGRAPHY": 6,
    "FOREGROUND": 7,
    "FX": 8,
    "CAPTIONS_BRAND": 9,
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
        document = asdict(self)
        document["scenes"] = list(self.scenes)
        document["assets"] = list(self.assets)
        document["provenance"] = list(self.provenance)
        return document

    def content_hash(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _data(node: Any) -> dict[str, Any]:
    attrs = getattr(node, "attrs", {}) or {}
    return attrs.get("data", attrs)


def _related_nodes(
    graph: Any,
    scene_id: str,
    relation: str,
    *,
    expected_kind: str,
    strict_kind: bool,
) -> list[Any]:
    nodes: list[Any] = []
    for edge in graph.edges:
        if edge.source != scene_id or edge.kind != relation:
            continue
        target = graph.node(edge.target)
        if target.kind != expected_kind:
            if strict_kind:
                raise ValueError(
                    f"{scene_id} {relation} must target {expected_kind}, got {target.kind}:{target.id}"
                )
            continue
        nodes.append(target)
    if len(nodes) > 1:
        raise ValueError(
            f"{scene_id} has multiple {expected_kind} nodes via {relation}: {[node.id for node in nodes]}"
        )
    return nodes


def _merge_relation(
    *,
    scene_id: str,
    role: str,
    legacy: dict[str, Any] | None,
    explicit_node: Any | None,
) -> dict[str, Any] | None:
    if explicit_node is None:
        return legacy
    explicit = {"id": explicit_node.id, **_data(explicit_node)}
    if legacy is not None and legacy.get("id") != explicit_node.id:
        raise ValueError(
            f"{scene_id} has conflicting legacy/explicit {role}: {legacy.get('id')} vs {explicit_node.id}"
        )
    return explicit


def compile_editing_graph_to_remotion(
    graph: Any,
    *,
    composition_id: str = "MotionOSStudio",
    fps: int = 30,
    width: int = 1080,
    height: int = 1920,
) -> RemotionGraphSpec:
    scenes: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    provenance: set[str] = set()
    for node in graph.nodes:
        data = _data(node)
        if node.kind == "Asset":
            assets.append({"id": node.id, **data})
            provenance.update(data.get("provenance", []) or [])

    scene_nodes = sorted(
        [node for node in graph.nodes if node.kind == "Scene"],
        key=lambda node: (_data(node).get("start_ms", 0), node.id),
    )
    max_end_ms = 0
    for scene in scene_nodes:
        scene_data = _data(scene)
        start_ms = int(scene_data.get("start_ms", 0))
        end_ms = int(scene_data.get("end_ms", start_ms))
        max_end_ms = max(max_end_ms, end_ms)

        contained_ids = [
            edge.target
            for edge in graph.edges
            if edge.source == scene.id and edge.kind == "CONTAINS"
        ]
        layers: list[dict[str, Any]] = []
        legacy_camera: dict[str, Any] | None = None
        legacy_transition_in: dict[str, Any] | None = None
        legacy_transition_out: dict[str, Any] | None = None
        audio_links: list[dict[str, Any]] = []

        for node_id in contained_ids:
            child = graph.node(node_id)
            child_data = _data(child)
            if child.kind == "Layer":
                layer_class = child_data.get("layer_class", "MIDGROUND")
                layers.append(
                    {
                        "id": child.id,
                        "layerClass": layer_class,
                        "z": int(child_data.get("z", LAYER_ORDER.get(layer_class, 4))),
                        "semanticRole": child_data.get("semantic_role"),
                        "attentionRole": child_data.get("attention_role", "secondary"),
                        "assetRef": child_data.get("asset_ref"),
                        "entry": child_data.get("entry"),
                        "settle": child_data.get("settle"),
                        "exit": child_data.get("exit"),
                        "rendererSupport": child_data.get("renderer_support", []),
                        "data": child_data,
                    }
                )
            elif child.kind == "CameraRig":
                candidate = {"id": child.id, **child_data}
                if legacy_camera is not None and legacy_camera["id"] != child.id:
                    raise ValueError(f"{scene.id} contains multiple legacy CameraRig nodes")
                legacy_camera = candidate
            elif child.kind == "Transition":
                candidate = {"id": child.id, **child_data}
                if child_data.get("direction") == "out":
                    if (
                        legacy_transition_out is not None
                        and legacy_transition_out["id"] != child.id
                    ):
                        raise ValueError(f"{scene.id} contains multiple legacy outgoing transitions")
                    legacy_transition_out = candidate
                else:
                    if (
                        legacy_transition_in is not None
                        and legacy_transition_in["id"] != child.id
                    ):
                        raise ValueError(f"{scene.id} contains multiple legacy incoming transitions")
                    legacy_transition_in = candidate

        # EditingGraph's canonical semantic relationships are explicit edges:
        # Scene --USES--> CameraRig and Scene --ENTERS_VIA/EXITS_VIA--> Transition.
        # CONTAINS support above remains only for historical compatibility.
        camera_nodes = _related_nodes(
            graph,
            scene.id,
            "USES",
            expected_kind="CameraRig",
            strict_kind=False,
        )
        transition_in_nodes = _related_nodes(
            graph,
            scene.id,
            "ENTERS_VIA",
            expected_kind="Transition",
            strict_kind=True,
        )
        transition_out_nodes = _related_nodes(
            graph,
            scene.id,
            "EXITS_VIA",
            expected_kind="Transition",
            strict_kind=True,
        )

        camera = _merge_relation(
            scene_id=scene.id,
            role="camera",
            legacy=legacy_camera,
            explicit_node=camera_nodes[0] if camera_nodes else None,
        )
        transition_in = _merge_relation(
            scene_id=scene.id,
            role="incoming transition",
            legacy=legacy_transition_in,
            explicit_node=transition_in_nodes[0] if transition_in_nodes else None,
        )
        transition_out = _merge_relation(
            scene_id=scene.id,
            role="outgoing transition",
            legacy=legacy_transition_out,
            explicit_node=transition_out_nodes[0] if transition_out_nodes else None,
        )

        for edge in graph.edges:
            if edge.source == scene.id and edge.kind == "SYNC_WITH":
                target = graph.node(edge.target)
                audio_links.append({"id": target.id, "kind": target.kind, **_data(target)})

        layers.sort(key=lambda item: (item["z"], item["id"]))
        from_frame = round(start_ms * fps / 1000)
        to_frame = round(end_ms * fps / 1000)
        scenes.append(
            {
                "id": scene.id,
                "fromFrame": from_frame,
                "durationInFrames": max(1, to_frame - from_frame),
                "camera": camera,
                "layers": layers,
                "transitionIn": transition_in,
                "transitionOut": transition_out,
                "audio": sorted(audio_links, key=lambda item: (item.get("at_ms", 0), item["id"])),
            }
        )

    return RemotionGraphSpec(
        composition_id=composition_id,
        fps=fps,
        width=width,
        height=height,
        duration_in_frames=max(1, round(max_end_ms * fps / 1000)),
        scenes=tuple(scenes),
        assets=tuple(sorted(assets, key=lambda item: item["id"])),
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


def build_ssr_render_contract(
    spec: RemotionGraphSpec,
    *,
    entry_point: str = "src/index.ts",
    output: str = "out/master.mp4",
) -> dict[str, Any]:
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
            "fps": spec.fps,
            "width": spec.width,
            "height": spec.height,
            "duration_in_frames": spec.duration_in_frames,
        },
    }
