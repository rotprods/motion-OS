from src.direction.compiler import compile_director_graph
from src.editing.compiler import compile_editing_graph, validate_attention_hierarchy, validate_timeline_coverage
from src.editing.audio_graph import attach_audio_graph


def build_directed():
    return compile_director_graph(
        'Autonomy improves productivity and focus.',
        project_id='editing_demo',
        duration_ms=9000,
        brand='MOTION.OS',
        visual_dna={'style_family': 'apple_premium', 'materials': ['brushed aluminum']},
    )


def test_director_compiles_to_gapless_editing_graph_with_one_primary_attention_layer_per_scene():
    directed = build_directed()
    editing = compile_editing_graph(directed)
    assert len(editing.scene_ids) == 3
    assert len(editing.layer_ids) == 9
    assert len(editing.transition_ids) == 2
    validate_timeline_coverage(editing.graph, 9000)
    validate_attention_hierarchy(editing.graph)
    for scene_id in editing.scene_ids:
        contained = [editing.graph.node(e.target) for e in editing.graph.edges if e.source == scene_id and e.kind == 'CONTAINS']
        primary = [n for n in contained if n.kind == 'Layer' and n.attrs['data'].get('attention_role') == 'primary']
        assert len(primary) == 1


def test_editing_graph_carries_camera_material_typography_and_transition_contracts():
    editing = compile_editing_graph(build_directed())
    graph = editing.graph
    assert len(graph.query_nodes(kind='CameraRig')) == 3
    assert len(graph.query_nodes(kind='Material')) == 1
    assert len(graph.query_nodes(kind='TypographyRole')) == 1
    assert len(graph.query_nodes(kind='Transition')) == 2
    assert graph.query_nodes(kind='Material')[0].attrs['data']['material'] == 'brushed_metal'
    assert all(node.attrs['data']['no_shake'] is True for node in graph.query_nodes(kind='CameraRig'))


def test_audio_graph_gives_every_scene_an_explicit_audio_or_silence_contract():
    directed = build_directed()
    editing = compile_editing_graph(directed)
    audio = attach_audio_graph(
        editing.graph,
        directed.spec,
        bpm=120,
        voice_lines=[{'start_ms': 0, 'end_ms': 2500, 'text': 'Autonomy starts here.'}],
    )
    assert len(audio.audio_cue_ids) == 3
    assert len(audio.music_beat_ids) == 3
    assert len(audio.voice_line_ids) == 1
    assert audio.graph.validate_typed()['ok'] is True
    for scene in audio.graph.query_nodes(kind='Scene'):
        sync_edges = [e for e in audio.graph.edges if e.source == scene.id and e.kind == 'SYNC_WITH']
        assert sync_edges
