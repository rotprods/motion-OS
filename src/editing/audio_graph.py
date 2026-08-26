from __future__ import annotations

from dataclasses import dataclass

from src.direction.contracts import DirectorSpec
from src.graph.editing_graph import TypedEditingGraph
from src.graph.model import Edge


@dataclass(frozen=True)
class AudioGraphResult:
    graph: TypedEditingGraph
    audio_cue_ids: tuple[str, ...]
    music_beat_ids: tuple[str, ...]
    voice_line_ids: tuple[str, ...]


def attach_audio_graph(
    graph: TypedEditingGraph,
    spec: DirectorSpec,
    *,
    bpm: float | None = None,
    voice_lines: list[dict] | None = None,
) -> AudioGraphResult:
    audio_ids: list[str] = []
    beat_ids: list[str] = []
    voice_ids: list[str] = []

    for index, beat in enumerate(spec.beats):
        scene_id = f'scene_{index + 1:02d}'
        if not graph.query_nodes(kind='Scene', attrs={'data': graph.node(scene_id).attrs['data']}):
            raise ValueError(f'missing scene for beat: {beat.beat_id}')
        cue_id = f'audio_cue_{index + 1:02d}'
        audio_ids.append(cue_id)
        graph.add_node(graph.typed_node(cue_id, 'AudioCue', data={
            'at_ms': beat.start_ms,
            'event': beat.sound_event or 'intentional_silence',
            'role': 'motion_sync_anchor',
            'narrative_function': beat.narrative_function,
        }, authority='inferred', provenance_refs=[beat.beat_id, 'director.md:15']))
        graph.add_edge(Edge(scene_id, cue_id, 'SYNC_WITH', {'id': f'e_sync_{scene_id}_{cue_id}'}))

        if bpm:
            beat_id = f'music_beat_{index + 1:02d}'
            beat_ids.append(beat_id)
            graph.add_node(graph.typed_node(beat_id, 'MusicBeat', data={
                'at_ms': beat.start_ms,
                'bpm': bpm,
                'sync_policy': 'selective_not_every_motion',
            }, authority='measured', provenance_refs=['audio:bpm']))
            graph.add_edge(Edge(cue_id, beat_id, 'SYNC_WITH', {'id': f'e_music_{index + 1:02d}'}))

    for index, line in enumerate(voice_lines or []):
        start = int(line['start_ms'])
        end = int(line['end_ms'])
        if start < 0 or end <= start or end > spec.duration_ms:
            raise ValueError(f'invalid voice line timing: {line}')
        voice_id = f'voice_line_{index + 1:02d}'
        voice_ids.append(voice_id)
        graph.add_node(graph.typed_node(voice_id, 'VoiceLine', data={
            'start_ms': start,
            'end_ms': end,
            'text': str(line['text']),
        }, authority=line.get('authority', 'authoritative'), provenance_refs=list(line.get('provenance_refs', ['voice_script']))))
        overlapping = [scene for scene in graph.query_nodes(kind='Scene') if scene.attrs['data']['start_ms'] < end and scene.attrs['data']['end_ms'] > start]
        for scene in overlapping:
            graph.add_edge(Edge(scene.id, voice_id, 'SYNC_WITH', {'id': f'e_voice_{scene.id}_{voice_id}'}))

    validation = graph.validate_typed()
    if not validation['ok']:
        raise ValueError(f'AudioGraph validation failed: {validation}')
    validate_audio_coverage(graph)
    return AudioGraphResult(graph=graph, audio_cue_ids=tuple(audio_ids), music_beat_ids=tuple(beat_ids), voice_line_ids=tuple(voice_ids))


def validate_audio_coverage(graph: TypedEditingGraph) -> None:
    scenes = graph.query_nodes(kind='Scene')
    for scene in scenes:
        synced = [e for e in graph.edges if e.source == scene.id and e.kind == 'SYNC_WITH' and graph.node(e.target).kind in {'AudioCue', 'VoiceLine'}]
        if not synced:
            raise ValueError(f'scene has no audio/silence choreography contract: {scene.id}')
