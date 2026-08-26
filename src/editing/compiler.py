from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.direction.compiler import DirectorCompilation
from src.graph.editing_graph import TypedEditingGraph
from src.graph.model import Edge


LAYER_STACK = (
    'ENVIRONMENT',
    'BACKGROUND_GRAPHICS',
    'FOOTAGE_PLATES',
    'SUBJECT',
    'MIDGROUND',
    'PRIMARY_UI',
    'TYPOGRAPHY',
    'FOREGROUND',
    'FX',
    'CAPTIONS_BRAND',
)


@dataclass(frozen=True)
class EditingCompilation:
    graph: TypedEditingGraph
    scene_ids: tuple[str, ...]
    layer_ids: tuple[str, ...]
    transition_ids: tuple[str, ...]


def _clone_director_graph(compilation: DirectorCompilation) -> TypedEditingGraph:
    return TypedEditingGraph.from_contract_dict(compilation.graph.to_contract_dict())


def _material_from_visual_dna(visual_dna: dict[str, Any]) -> str:
    text = str(visual_dna).casefold()
    if 'glass' in text:
        return 'glass'
    if 'metal' in text or 'aluminum' in text or 'chrome' in text:
        return 'brushed_metal'
    if 'paper' in text or 'editorial' in text:
        return 'paper'
    return 'matte'


def compile_editing_graph(compilation: DirectorCompilation) -> EditingCompilation:
    spec = compilation.spec
    graph = _clone_director_graph(compilation)
    scene_ids: list[str] = []
    layer_ids: list[str] = []
    transition_ids: list[str] = []

    material_id = 'material_global'
    typography_id = 'typography_primary'
    graph.add_node(graph.typed_node(material_id, 'Material', data={'material': _material_from_visual_dna(spec.visual_dna)}, authority='inferred', provenance_refs=['director:visual_dna']))
    graph.add_node(graph.typed_node(typography_id, 'TypographyRole', data={'role': 'primary', 'readability': 'strict', 'transform_only_after_readability': True}, authority='authoritative', provenance_refs=['director.md:09']))

    for index, beat in enumerate(spec.beats):
        scene_id = f'scene_{index + 1:02d}'
        shot_id = f'shot_{index + 1:02d}'
        camera_id = f'camera_{index + 1:02d}'
        scene_ids.append(scene_id)

        graph.add_node(graph.typed_node(scene_id, 'Scene', data={
            'start_ms': beat.start_ms,
            'end_ms': beat.end_ms,
            'narrative_function': beat.narrative_function,
            'attention_target': beat.attention_target,
            'motion_purpose': beat.motion_purpose,
        }, authority='inferred', provenance_refs=[beat.beat_id]))
        graph.add_node(graph.typed_node(shot_id, 'Shot', data={'start_ms': beat.start_ms, 'end_ms': beat.end_ms, 'stability': 'directed'}, authority='inferred', provenance_refs=[scene_id]))
        graph.add_node(graph.typed_node(camera_id, 'CameraRig', data={
            'framing': 'medium',
            'motion': 'static_or_micro_drift',
            'z_drift': 0.0,
            'focus_behavior': 'locked',
            'no_shake': True,
        }, authority='inferred', provenance_refs=['director.md:10']))
        graph.add_edge(Edge(beat.beat_id, scene_id, 'MATERIALIZES_AS', {'id': f'e_beat_scene_{index:02d}'}))
        graph.add_edge(Edge(scene_id, shot_id, 'CONTAINS', {'id': f'e_scene_shot_{index:02d}'}))
        graph.add_edge(Edge(scene_id, camera_id, 'USES', {'id': f'e_scene_camera_{index:02d}'}))

        layer_specs = (
            ('environment', 'ENVIRONMENT', 'secondary', False),
            ('primary', 'SUBJECT', 'primary', False),
            ('typography', 'TYPOGRAPHY', 'secondary', True),
        )
        for suffix, layer_class, attention_role, uses_type in layer_specs:
            layer_id = f'{scene_id}_layer_{suffix}'
            track_id = f'{layer_id}_track'
            layer_ids.append(layer_id)
            graph.add_node(graph.typed_node(layer_id, 'Layer', data={
                'layer_class': layer_class,
                'z': LAYER_STACK.index(layer_class),
                'semantic_role': suffix,
                'attention_role': attention_role,
                'entry': 'directed',
                'settle': 'required',
                'exit': 'connected_to_next_state',
                'renderer_support': ['remotion', 'hyperframes'],
            }, authority='inferred', provenance_refs=[scene_id, 'director.md']))
            graph.add_node(graph.typed_node(track_id, 'Track', data={
                'start_ms': beat.start_ms,
                'end_ms': beat.end_ms,
                'channels': ['x', 'y', 'scale', 'opacity'],
                'purpose': beat.motion_purpose,
            }, authority='inferred', provenance_refs=[layer_id]))
            graph.add_edge(Edge(scene_id, layer_id, 'CONTAINS', {'id': f'e_{scene_id}_{suffix}'}))
            graph.add_edge(Edge(layer_id, track_id, 'CONTAINS', {'id': f'e_{layer_id}_track'}))
            graph.add_edge(Edge(layer_id, material_id, 'USES', {'id': f'e_{layer_id}_material'}))
            if uses_type:
                graph.add_edge(Edge(layer_id, typography_id, 'USES', {'id': f'e_{layer_id}_type'}))

        primary_layer = f'{scene_id}_layer_primary'
        for primitive in beat.primitive_candidates:
            primitive_id = f'primitive:{primitive}'
            if not graph.query_nodes(attrs={'data': {'name': primitive}}):
                if primitive_id not in {n.id for n in graph.nodes}:
                    graph.add_node(graph.typed_node(primitive_id, 'Primitive', data={'name': primitive, 'semantic_behavior': beat.semantic_behavior}, authority='inferred', provenance_refs=[beat.beat_id]))
            graph.add_edge(Edge(primary_layer, primitive_id, 'ANIMATED_BY', {'id': f'e_{primary_layer}_{primitive}'}))

        if index < len(spec.beats) - 1:
            transition_id = f'transition_{index + 1:02d}_{index + 2:02d}'
            transition_ids.append(transition_id)
            graph.add_node(graph.typed_node(transition_id, 'Transition', data={
                'type': 'match_geometry_or_existing_element',
                'rule': 'transition emerges from element already on screen',
                'from_scene': scene_id,
                'to_scene': f'scene_{index + 2:02d}',
            }, authority='authoritative', provenance_refs=['director.md:11']))
            graph.add_edge(Edge(scene_id, transition_id, 'EXITS_VIA', {'id': f'e_exit_{transition_id}'}))

    for index, transition_id in enumerate(transition_ids):
        next_scene = scene_ids[index + 1]
        graph.add_edge(Edge(next_scene, transition_id, 'ENTERS_VIA', {'id': f'e_enter_{transition_id}'}))

    validation = graph.validate_typed()
    if not validation['ok']:
        raise ValueError(f'EditingGraph validation failed: {validation}')
    validate_timeline_coverage(graph, spec.duration_ms)
    validate_attention_hierarchy(graph)
    return EditingCompilation(graph=graph, scene_ids=tuple(scene_ids), layer_ids=tuple(layer_ids), transition_ids=tuple(transition_ids))


def validate_timeline_coverage(graph: TypedEditingGraph, duration_ms: int) -> None:
    scenes = sorted(graph.query_nodes(kind='Scene'), key=lambda n: n.attrs['data']['start_ms'])
    if not scenes:
        raise ValueError('no scenes')
    cursor = 0
    for scene in scenes:
        data = scene.attrs['data']
        if data['start_ms'] != cursor:
            raise ValueError(f'timeline gap/overlap before {scene.id}: expected {cursor}, got {data["start_ms"]}')
        if data['end_ms'] <= data['start_ms']:
            raise ValueError(f'invalid scene duration: {scene.id}')
        cursor = data['end_ms']
    if cursor != duration_ms:
        raise ValueError(f'timeline does not cover duration: {cursor} != {duration_ms}')


def validate_attention_hierarchy(graph: TypedEditingGraph) -> None:
    for scene in graph.query_nodes(kind='Scene'):
        contained = [e.target for e in graph.edges if e.source == scene.id and e.kind == 'CONTAINS']
        primary = []
        for node_id in contained:
            node = graph.node(node_id)
            if node.kind == 'Layer' and node.attrs['data'].get('attention_role') == 'primary':
                primary.append(node_id)
        if len(primary) > 1:
            raise ValueError(f'multiple primary attention layers in {scene.id}: {primary}')
