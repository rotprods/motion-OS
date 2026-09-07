from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Mapping

from src.compilers.remotion_graph import RemotionGraphSpec, compile_editing_graph_to_remotion
from src.content.studio_execution_gateway import StudioExecutionContext, execute_verified_studio_handoff
from src.editing.compiler import validate_timeline_coverage
from src.graph.editing_graph import TypedEditingGraph
from src.graph.model import Edge
from src.renderers.multirender import assign_renderers, render_manifest


def _canonical_hash(value: object) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _positive_decimal(value: object, *, field: str, default: Decimal | None = None) -> Decimal:
    if value is None and default is not None:
        return default
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a positive number")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be a positive number") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError(f"{field} must be a positive finite number")
    return parsed


def _semantic_beats(manifest: Mapping[str, Any], ctx: StudioExecutionContext) -> tuple[Mapping[str, Any], ...]:
    raw = manifest.get("semantic_beats")
    if not isinstance(raw, list) or not raw:
        raise ValueError("semantic_beats must be a non-empty list")
    beats: list[Mapping[str, Any]] = []
    ids: list[str] = []
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise ValueError(f"semantic_beats[{index}] must be an object")
        beat_id = item.get("id")
        if not isinstance(beat_id, str) or not beat_id.strip():
            raise ValueError(f"semantic_beats[{index}].id must be a non-empty string")
        ids.append(beat_id)
        beats.append(item)
    if tuple(ids) != ctx.semantic_beat_ids:
        raise ValueError("semantic beat identity/order differs from authorized Studio context")
    if len(set(ids)) != len(ids):
        raise ValueError("semantic beat IDs must be unique")
    return tuple(beats)


def _timeline_boundaries(beats: tuple[Mapping[str, Any], ...], *, duration_ms: int) -> tuple[int, ...]:
    if not isinstance(duration_ms, int) or isinstance(duration_ms, bool) or duration_ms <= 0:
        raise ValueError("duration_ms must be a positive integer")
    if duration_ms < len(beats):
        raise ValueError("duration_ms must permit at least one millisecond per semantic beat")
    weights: list[Decimal] = []
    for index, beat in enumerate(beats):
        weights.append(
            _positive_decimal(
                beat.get("target_duration_s"),
                field=f"semantic_beats[{index}].target_duration_s",
                default=Decimal(1),
            )
        )
    total = sum(weights, Decimal(0))
    boundaries = [0]
    cumulative = Decimal(0)
    for index, weight in enumerate(weights[:-1], start=1):
        cumulative += weight
        boundary = int(
            (Decimal(duration_ms) * cumulative / total).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
        minimum = boundaries[-1] + 1
        maximum = duration_ms - (len(beats) - index)
        boundaries.append(min(max(boundary, minimum), maximum))
    boundaries.append(duration_ms)
    return tuple(boundaries)


def _downstream_cue_map(manifest: Mapping[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    raw = manifest.get("downstream_edit_cues")
    if raw is None:
        return out
    if not isinstance(raw, list):
        raise ValueError("downstream_edit_cues must be a list when present")
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise ValueError(f"downstream_edit_cues[{index}] must be an object")
        beat_id = item.get("beat_id")
        if not isinstance(beat_id, str) or not beat_id:
            raise ValueError(f"downstream_edit_cues[{index}].beat_id must be a non-empty string")
        values = []
        for field in ("intent", "suggested_layer"):
            value = item.get(field)
            if value is not None:
                if not isinstance(value, str):
                    raise ValueError(f"downstream_edit_cues[{index}].{field} must be text")
                if value.strip():
                    values.append(value.strip())
        out.setdefault(beat_id, []).extend(values)
    return out


def _primary_layer_class(cues: list[str]) -> str:
    text = " ".join(cues).casefold()
    ui_markers = ("ui", "repo", "browser", "counter", "graph", "interface", "screen", "hud")
    return "PRIMARY_UI" if any(marker in text for marker in ui_markers) else "SUBJECT"


def _asset_manifest(manifest: Mapping[str, Any], ctx: StudioExecutionContext) -> dict[str, Any]:
    render = manifest.get("render")
    avatar = manifest.get("avatar")
    assets: list[dict[str, Any]] = []
    if isinstance(render, Mapping):
        asset_ref = render.get("asset_ref")
        if asset_ref is not None:
            if not isinstance(asset_ref, str) or not asset_ref.strip():
                raise ValueError("render.asset_ref must be a non-empty string when present")
            assets.append(
                {
                    "id": "asset:phase06-avatar-master",
                    "source_ref": asset_ref,
                    "provider_job_id": ctx.render_job_id,
                    "provider": render.get("provider"),
                }
            )
    profile_id = avatar.get("profile_id") if isinstance(avatar, Mapping) else None
    return {
        "content_id": ctx.content_id,
        "provenance_root": ctx.provenance_root,
        "avatar_profile_id": profile_id,
        "assets": assets,
    }


def compile_phase06_manifest_to_studio_graph(
    ctx: StudioExecutionContext,
    manifest: Mapping[str, Any],
) -> tuple[TypedEditingGraph, dict[str, Any]]:
    content_id = manifest.get("content_id")
    if content_id != ctx.content_id:
        raise ValueError("manifest content_id differs from authorized Studio context")
    beats = _semantic_beats(manifest, ctx)
    duration_s = _positive_decimal(manifest.get("duration_target_s"), field="duration_target_s")
    duration_ms = int((duration_s * Decimal(1000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    boundaries = _timeline_boundaries(beats, duration_ms=duration_ms)
    cue_map = _downstream_cue_map(manifest)
    unknown_cue_ids = sorted(set(cue_map) - set(ctx.semantic_beat_ids))
    if unknown_cue_ids:
        raise ValueError(f"downstream edit cues reference unknown semantic beats: {unknown_cue_ids}")
    asset_manifest = _asset_manifest(manifest, ctx)

    graph = TypedEditingGraph(
        graph_id=f"studio:{ctx.content_id}",
        project_id=ctx.content_id,
    )
    project_id = f"project:{ctx.content_id}"
    brief_id = f"brief:{ctx.content_id}"
    graph.add_node(
        graph.typed_node(
            project_id,
            "Project",
            data={
                "duration_ms": duration_ms,
                "source": "phase06_sealed_manifest",
                "provenance_root": ctx.provenance_root,
                "replay_fingerprint": ctx.replay_fingerprint,
            },
            authority="authoritative",
            provenance_refs=[ctx.provenance_root, ctx.replay_fingerprint],
        )
    )
    graph.add_node(
        graph.typed_node(
            brief_id,
            "Brief",
            data={
                "core_thesis": manifest.get("core_thesis"),
                "script_display_text": manifest.get("script_display_text"),
                "content_id": ctx.content_id,
            },
            authority="authoritative",
            provenance_refs=[ctx.replay_fingerprint],
        )
    )
    graph.add_edge(Edge(project_id, brief_id, "CONTAINS", {"id": "e_project_brief"}))

    asset_node_id: str | None = None
    if asset_manifest["assets"]:
        asset_doc = asset_manifest["assets"][0]
        asset_node_id = asset_doc["id"]
        graph.add_node(
            graph.typed_node(
                asset_node_id,
                "Asset",
                data={
                    **asset_doc,
                    "provenance": [ctx.provenance_root, ctx.replay_fingerprint],
                },
                authority="authoritative",
                provenance_refs=[ctx.provenance_root, str(asset_doc["source_ref"])],
            )
        )
        graph.add_edge(Edge(project_id, asset_node_id, "CONTAINS", {"id": "e_project_avatar_asset"}))

    scene_ids: list[str] = []
    for index, beat in enumerate(beats):
        beat_id = str(beat["id"])
        start_ms, end_ms = boundaries[index], boundaries[index + 1]
        beat_cues = beat.get("edit_cues")
        if beat_cues is None:
            beat_cues_list: list[str] = []
        elif isinstance(beat_cues, list) and all(isinstance(item, str) for item in beat_cues):
            beat_cues_list = [item.strip() for item in beat_cues if item.strip()]
        else:
            raise ValueError(f"semantic beat {beat_id} edit_cues must be a list of strings")
        combined_cues = beat_cues_list + cue_map.get(beat_id, [])
        intent_id = f"intent:{beat_id}"
        scene_id = f"scene:{beat_id}"
        scene_ids.append(scene_id)

        graph.add_node(
            graph.typed_node(
                intent_id,
                "Intent",
                data={
                    "function": beat.get("function"),
                    "text": beat.get("text"),
                    "edit_cues": combined_cues,
                },
                authority="authoritative",
                provenance_refs=[ctx.replay_fingerprint, beat_id],
                continuity_id=beat_id,
            )
        )
        graph.add_node(
            graph.typed_node(
                beat_id,
                "NarrativeBeat",
                data={
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "function": beat.get("function"),
                    "text": beat.get("text"),
                    "edit_cues": combined_cues,
                    "upstream_target_duration_s": beat.get("target_duration_s"),
                },
                authority="authoritative",
                provenance_refs=[ctx.provenance_root, ctx.replay_fingerprint],
                continuity_id=beat_id,
            )
        )
        graph.add_node(
            graph.typed_node(
                scene_id,
                "Scene",
                data={
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "semantic_beat_id": beat_id,
                    "narrative_function": beat.get("function"),
                    "edit_cues": combined_cues,
                },
                authority="inferred",
                provenance_refs=[beat_id, ctx.replay_fingerprint],
                continuity_id=beat_id,
            )
        )
        graph.add_edge(Edge(brief_id, intent_id, "DRIVES", {"id": f"e_brief_{intent_id}"}))
        graph.add_edge(Edge(intent_id, beat_id, "DRIVES", {"id": f"e_intent_{beat_id}"}))
        graph.add_edge(Edge(beat_id, scene_id, "MATERIALIZES_AS", {"id": f"e_beat_scene_{beat_id}"}))

        primary_class = _primary_layer_class(combined_cues)
        layer_specs = (
            ("environment", "ENVIRONMENT", "secondary", None),
            ("primary", primary_class, "primary", asset_node_id),
            ("typography", "TYPOGRAPHY", "secondary", None),
        )
        for suffix, layer_class, attention_role, asset_ref in layer_specs:
            layer_id = f"layer:{beat_id}:{suffix}"
            graph.add_node(
                graph.typed_node(
                    layer_id,
                    "Layer",
                    data={
                        "layer_class": layer_class,
                        "z": {"ENVIRONMENT": 0, "SUBJECT": 3, "PRIMARY_UI": 5, "TYPOGRAPHY": 6}[layer_class],
                        "semantic_role": suffix,
                        "attention_role": attention_role,
                        "asset_ref": asset_ref,
                        "text": beat.get("text") if suffix == "typography" else None,
                        "edit_cues": combined_cues,
                        "renderer_support": ["remotion", "hyperframes"],
                    },
                    authority="inferred",
                    provenance_refs=[beat_id, ctx.provenance_root],
                    continuity_id=f"{beat_id}:{suffix}",
                )
            )
            graph.add_edge(Edge(scene_id, layer_id, "CONTAINS", {"id": f"e_{scene_id}_{suffix}"}))
            if asset_ref:
                graph.add_edge(Edge(layer_id, asset_ref, "USES", {"id": f"e_{layer_id}_asset"}))

        if index < len(beats) - 1:
            next_beat_id = str(beats[index + 1]["id"])
            transition_id = f"transition:{beat_id}:{next_beat_id}"
            graph.add_node(
                graph.typed_node(
                    transition_id,
                    "Transition",
                    data={
                        "type": "match_geometry_or_existing_element",
                        "from_beat_id": beat_id,
                        "to_beat_id": next_beat_id,
                        "rule": "transition emerges from existing on-screen state",
                    },
                    authority="inferred",
                    provenance_refs=[beat_id, next_beat_id],
                    continuity_id=f"{beat_id}->{next_beat_id}",
                )
            )
            graph.add_edge(Edge(scene_id, transition_id, "EXITS_VIA", {"id": f"e_exit_{transition_id}"}))

    for index in range(1, len(scene_ids)):
        previous_beat_id = str(beats[index - 1]["id"])
        beat_id = str(beats[index]["id"])
        transition_id = f"transition:{previous_beat_id}:{beat_id}"
        graph.add_edge(Edge(scene_ids[index], transition_id, "ENTERS_VIA", {"id": f"e_enter_{transition_id}"}))

    typed = graph.validate_typed()
    if not typed["ok"]:
        raise ValueError(f"Studio graph validation failed: {typed}")
    validate_timeline_coverage(graph, duration_ms)
    return graph, asset_manifest


def remotion_graph_spec_to_runtime_spec(spec: RemotionGraphSpec) -> dict[str, Any]:
    scenes: list[dict[str, Any]] = []
    for scene in spec.scenes:
        from_frame = int(scene["fromFrame"])
        duration = int(scene["durationInFrames"])
        layers = list(scene.get("layers") or [])
        transition = scene.get("transitionIn") or {"type": "cut"}
        if not isinstance(transition, Mapping):
            transition = {"type": "cut"}
        camera = scene.get("camera") or {"motion": "static"}
        if not isinstance(camera, Mapping):
            camera = {"motion": "static"}
        camera_doc = dict(camera)
        camera_doc["motion"] = str(camera_doc.get("motion") or "static")
        scenes.append(
            {
                "id": scene["id"],
                "from": from_frame,
                "durationInFrames": duration,
                "camera": camera_doc,
                "depth": {
                    "layers_z": [
                        {
                            "id": layer["id"],
                            "z_index": int(layer.get("z", 0)),
                            "parallax_ratio": 0.0,
                        }
                        for layer in layers
                    ]
                },
                "transition": {
                    "type": str(transition.get("type") or "cut"),
                    "at_ms_global": round(from_frame * 1000 / spec.fps),
                },
                "events": [
                    {
                        "id": f"event:{scene['id']}",
                        "at_frame": from_frame,
                        "action": "semantic_scene_start",
                    }
                ],
                "layers": layers,
            }
        )
    runtime = {
        "project": {
            "fps": spec.fps,
            "width": spec.width,
            "height": spec.height,
            "duration_frames": spec.duration_in_frames,
        },
        "zOrder": [
            item["id"]
            for scene in scenes
            for item in sorted(scene["layers"], key=lambda layer: (int(layer.get("z", 0)), layer["id"]), reverse=True)
        ],
        "scenes": scenes,
    }
    return runtime


def _prepare_authorized_context(
    ctx: StudioExecutionContext,
    manifest: Mapping[str, Any],
    *,
    fps: int,
    width: int,
    height: int,
) -> dict[str, Any]:
    for name, value in (("fps", fps), ("width", width), ("height", height)):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    graph, asset_manifest = compile_phase06_manifest_to_studio_graph(ctx, manifest)
    assignments = assign_renderers(graph, available=("remotion",))
    project_nodes = graph.query_nodes(kind="Project")
    if len(project_nodes) != 1:
        raise ValueError("Studio graph must contain exactly one Project node")
    duration_ms = int(project_nodes[0].attrs["data"]["duration_ms"])
    render_doc = render_manifest(
        graph,
        assignments,
        fps=fps,
        width=width,
        height=height,
        duration_ms=duration_ms,
    )
    remotion_spec = compile_editing_graph_to_remotion(
        graph,
        composition_id="MotionOSRuntime",
        fps=fps,
        width=width,
        height=height,
    )
    runtime_spec = remotion_graph_spec_to_runtime_spec(remotion_spec)
    asset_manifest_hash = _canonical_hash(asset_manifest)
    bundle: dict[str, Any] = {
        "schema": "motion-os.studio-execution-bundle/v1",
        "stage": "STUDIO_COMPILED",
        "execution_started": True,
        "render_started": False,
        "content_id": ctx.content_id,
        "provenance_root": ctx.provenance_root,
        "replay_fingerprint": ctx.replay_fingerprint,
        "render_job_id": ctx.render_job_id,
        "semantic_beat_ids": list(ctx.semantic_beat_ids),
        "graph": graph.to_contract_dict(),
        "graph_hash": graph.content_hash(),
        "asset_manifest": asset_manifest,
        "asset_manifest_hash": asset_manifest_hash,
        "render_manifest": render_doc,
        "remotion_spec": remotion_spec.to_dict(),
        "remotion_spec_hash": remotion_spec.content_hash(),
        "runtime_spec": runtime_spec,
        "runtime_spec_hash": _canonical_hash(runtime_spec),
    }
    bundle["execution_hash"] = _canonical_hash(bundle)
    return bundle


def prepare_studio_execution(
    sealed_manifest: Mapping[str, Any],
    handoff: Mapping[str, Any],
    *,
    fps: int = 30,
    width: int = 1080,
    height: int = 1920,
) -> dict[str, Any]:
    """Explicit Phase06 authorization -> Studio compilation transition.

    Authorization remains side-effect free. This function deliberately starts
    Studio compilation only through execute_verified_studio_handoff(); it does
    not launch a renderer or claim creative/release authority.
    """
    return execute_verified_studio_handoff(
        sealed_manifest,
        handoff,
        lambda ctx: _prepare_authorized_context(
            ctx,
            sealed_manifest,
            fps=fps,
            width=width,
            height=height,
        ),
    )
