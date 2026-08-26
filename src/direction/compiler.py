from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.semantic_behavior import compile_semantic_behaviors, primitive_candidates
from src.direction.contracts import (
    DEFAULT_NEGATIVE_MOTION_RULES,
    DirectorBeat,
    DirectorSpec,
    EmotionStateSpec,
    default_precision_physics,
)
from src.graph.editing_graph import TypedEditingGraph
from src.graph.model import Edge


@dataclass(frozen=True)
class DirectorCompilation:
    spec: DirectorSpec
    graph: TypedEditingGraph


def _phase_behaviors(brief: str):
    detected = compile_semantic_behaviors(brief)
    if len(detected) >= 3:
        return detected
    if len(detected) == 2:
        return [detected[0], detected[1], detected[1]]
    return [detected[0], detected[0], detected[0]]


def _build_beats(brief: str, duration_ms: int) -> tuple[DirectorBeat, ...]:
    behaviors = _phase_behaviors(brief)
    narrative_functions = ('hook_and_frame', 'develop_and_prove', 'payoff_and_memory')
    sound_events = ('initial_accent', 'development_accent', 'final_payoff')
    boundaries = [0]
    for index in range(1, len(behaviors)):
        boundaries.append(round(duration_ms * index / len(behaviors)))
    boundaries.append(duration_ms)

    beats = []
    for index, behavior in enumerate(behaviors):
        candidates = tuple(primitive_candidates([behavior]))
        dominant = behavior.behavior
        beats.append(
            DirectorBeat(
                beat_id=f'beat_{index + 1:02d}',
                start_ms=boundaries[index],
                end_ms=boundaries[index + 1],
                dominant_element=dominant,
                primary_action=candidates[0] if candidates else 'reveal_mask',
                attention_target=dominant,
                secondary_attention=None,
                suppress=('competing_primary_motion', 'nonessential_fx'),
                narrative_function=narrative_functions[index],
                motion_purpose=behavior.visual_contract,
                sound_event=sound_events[index],
                semantic_behavior=behavior.behavior,
                primitive_candidates=candidates,
            )
        )
    return tuple(beats)


def compile_director_graph(
    brief: str,
    *,
    project_id: str,
    duration_ms: int,
    piece_type: str = 'motion_graphics',
    aspect_ratio: str = '16:9',
    platform: str | None = None,
    brand: str | None = None,
    visual_dna: dict[str, Any] | None = None,
    motion_grammar: str = 'auto',
    final_frame_memory: str = 'one clear resolved image with stable readable hierarchy',
) -> DirectorCompilation:
    if not brief.strip():
        raise ValueError('brief cannot be empty')
    beats = _build_beats(brief, duration_ms)
    spec = DirectorSpec(
        project_id=project_id,
        brief=brief,
        piece_type=piece_type,
        duration_ms=duration_ms,
        aspect_ratio=aspect_ratio,
        platform=platform,
        brand=brand,
        emotional_curve=(
            EmotionStateSpec('initial', 'curiosity', 0.35),
            EmotionStateSpec('development', 'discovery', 0.65),
            EmotionStateSpec('final', 'impact', 0.9),
        ),
        visual_dna=dict(visual_dna or {}),
        motion_physics=default_precision_physics(),
        beats=beats,
        negative_motion_rules=DEFAULT_NEGATIVE_MOTION_RULES,
        final_frame_memory=final_frame_memory,
        brand_motion_language={
            'logo_entry': 'derived_from_existing_geometry_where_possible',
            'transition_rule': 'existing_element_generates_next_state',
            'typography_rule': 'readable_before_transform',
            'motion_master_rule': 'movement_must_direct_attention_communicate_generate_emotion_or_connect_states',
        },
    )

    graph = TypedEditingGraph(graph_id=f'director:{project_id}', project_id=project_id)
    graph.add_node(graph.typed_node('project', 'Project', data={'piece_type': piece_type, 'duration_ms': duration_ms, 'aspect_ratio': aspect_ratio}, authority='authoritative', provenance_refs=['director.md']))
    graph.add_node(graph.typed_node('brief', 'Brief', data={'text': brief}, authority='authoritative', provenance_refs=['user_brief']))
    graph.add_edge(Edge('project', 'brief', 'CONTAINS', {'id': 'director_e_project_brief'}))

    if visual_dna:
        graph.add_node(graph.typed_node('visual_dna', 'StyleSignature', data=dict(visual_dna), authority='inferred', provenance_refs=['visual_dna_input']))
        graph.add_edge(Edge('project', 'visual_dna', 'CONTAINS', {'id': 'director_e_visual_dna'}))

    graph.add_node(graph.typed_node('motion_grammar', 'MotionGrammar', data={'id': motion_grammar}, authority='inferred', provenance_refs=['motion_grammar_system']))
    graph.add_edge(Edge('project', 'motion_grammar', 'CONTAINS', {'id': 'director_e_grammar'}))

    if brand:
        graph.add_node(graph.typed_node('brand_rule', 'BrandRule', data={'brand': brand, 'rule': 'animation amplifies branding; never replaces it'}, authority='authoritative', provenance_refs=['brief:brand']))
        graph.add_edge(Edge('project', 'brand_rule', 'CONTAINS', {'id': 'director_e_brand'}))

    behaviors = _phase_behaviors(brief)
    intent_ids = []
    for index, behavior in enumerate(behaviors):
        intent_id = f'intent_{index + 1:02d}'
        intent_ids.append(intent_id)
        graph.add_node(graph.typed_node(intent_id, 'Intent', data=behavior.to_dict(), authority='inferred', provenance_refs=[behavior.evidence]))
        graph.add_edge(Edge('brief', intent_id, 'DRIVES', {'id': f'director_e_brief_{intent_id}'}))

    for index, emotion in enumerate(spec.emotional_curve):
        emotion_id = f'emotion_{index + 1:02d}'
        graph.add_node(graph.typed_node(emotion_id, 'EmotionState', data={'phase': emotion.phase, 'emotion': emotion.emotion, 'intensity': emotion.intensity}, authority='inferred', provenance_refs=['director.md:01']))
        graph.add_edge(Edge(intent_ids[min(index, len(intent_ids) - 1)], emotion_id, 'SHAPES', {'id': f'director_e_emotion_{index + 1:02d}'}))

    negative_ids = []
    for index, rule in enumerate(spec.negative_motion_rules):
        rule_id = f'negative_{index + 1:02d}'
        negative_ids.append(rule_id)
        graph.add_node(graph.typed_node(rule_id, 'NegativeConstraint', data={'rule': rule}, authority='authoritative', provenance_refs=['director.md:23']))
        graph.add_edge(Edge('brief', rule_id, 'CONSTRAINED_BY', {'id': f'director_e_negative_{index + 1:02d}'}))

    for index, beat in enumerate(spec.beats):
        graph.add_node(graph.typed_node(beat.beat_id, 'NarrativeBeat', data={
            'start_ms': beat.start_ms,
            'end_ms': beat.end_ms,
            'dominant_element': beat.dominant_element,
            'primary_action': beat.primary_action,
            'attention_target': beat.attention_target,
            'secondary_attention': beat.secondary_attention,
            'suppress': list(beat.suppress),
            'narrative_function': beat.narrative_function,
            'motion_purpose': beat.motion_purpose,
            'sound_event': beat.sound_event,
            'semantic_behavior': beat.semantic_behavior,
            'primitive_candidates': list(beat.primitive_candidates),
        }, authority='inferred', provenance_refs=['director.md', f'semantic:{beat.semantic_behavior}']))
        graph.add_edge(Edge(intent_ids[index], beat.beat_id, 'DRIVES', {'id': f'director_e_intent_beat_{index + 1:02d}'}))
        graph.add_edge(Edge('motion_grammar', beat.beat_id, 'CONDITIONS', {'id': f'director_e_grammar_beat_{index + 1:02d}'}))
        if brand:
            graph.add_edge(Edge('brand_rule', beat.beat_id, 'CONDITIONS', {'id': f'director_e_brand_beat_{index + 1:02d}'}))

    if not graph.validate_typed()['ok']:
        raise ValueError(f'Director graph failed validation: {graph.validate_typed()}')
    return DirectorCompilation(spec=spec, graph=graph)
