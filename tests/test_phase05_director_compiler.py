from src.direction.compiler import compile_director_graph


def test_director_compiler_covers_entire_timeline_without_gaps():
    result = compile_director_graph(
        'Autonomy removes the bottleneck and improves productivity.',
        project_id='director_demo',
        duration_ms=9000,
        brand='MOTION.OS',
        visual_dna={'style_family': 'premium_product'},
    )
    beats = result.spec.beats
    assert beats[0].start_ms == 0
    assert beats[-1].end_ms == 9000
    assert all(a.end_ms == b.start_ms for a, b in zip(beats, beats[1:]))
    assert all(beat.motion_purpose for beat in beats)
    assert all(beat.attention_target for beat in beats)
    assert result.graph.validate_typed()['ok'] is True


def test_director_compiler_translates_semantics_before_primitives():
    result = compile_director_graph(
        'Autonomy solves the bottleneck.',
        project_id='semantic_demo',
        duration_ms=6000,
    )
    behaviors = [beat.semantic_behavior for beat in result.spec.beats]
    assert 'controller_node' in behaviors
    assert 'geometric_narrowing' in behaviors
    for beat in result.spec.beats:
        assert beat.primitive_candidates
        assert beat.primary_action == beat.primitive_candidates[0]


def test_director_compiler_enforces_master_negative_motion_rules():
    result = compile_director_graph('Focus.', project_id='negative_demo', duration_ms=3000)
    rules = set(result.spec.negative_motion_rules)
    assert 'no_random_motion' in rules
    assert 'no_unreadable_text_during_motion' in rules
    assert 'no_competing_primary_attention_moves' in rules
    negative_nodes = result.graph.query_nodes(kind='NegativeConstraint')
    assert len(negative_nodes) == len(rules)


def test_empty_brief_is_rejected():
    try:
        compile_director_graph('   ', project_id='bad', duration_ms=1000)
    except ValueError as exc:
        assert 'brief cannot be empty' in str(exc)
    else:
        raise AssertionError('empty brief must be rejected')
