from src.blueprints.registry import build_blueprint_registry, select_blueprints, validate_blueprints
from src.primitives.registry import build_registry, primitive_candidates_for_intent, validate_registry


def test_all_existing_primitives_are_semantically_enriched_without_losing_count():
    registry = build_registry()
    validation = validate_registry(registry)
    assert validation['count'] >= 45
    assert validation['unique'] is True
    assert validation['semantic_complete'] is True
    assert all(p.semantic_intents for p in registry)
    assert all(p.channels for p in registry)
    assert all(p.qa for p in registry)


def test_typography_and_particles_have_strict_family_constraints():
    registry = build_registry()
    typography = [p for p in registry if p.family == 'typography']
    particles = [p for p in registry if p.family == 'particles']
    assert typography
    assert particles
    assert all(p.qa.get('text_integrity') == 'strict' for p in typography)
    assert all('micro' in p.attention_roles for p in particles)
    assert all('free_particles_without_narrative_function' in p.forbidden_combinations for p in particles)


def test_semantic_intent_routes_to_portable_primitive_candidates():
    candidates = primitive_candidates_for_intent('connect_states', attention_role='primary', renderer='remotion')
    ids = {p.id for p in candidates}
    assert 'match_motion' in ids
    assert 'object_occlusion' in ids
    assert all('remotion' in p.renderer_support for p in candidates)


def test_blueprint_registry_is_structural_unique_and_has_no_brand_copy():
    blueprints = build_blueprint_registry()
    validation = validate_blueprints(blueprints)
    assert validation == {
        'count': 7,
        'unique': True,
        'no_fixed_copy': True,
        'all_structural': True,
    }
    assert all('no_fixed_copy' in bp.negative_rules for bp in blueprints)


def test_blueprint_selector_routes_apple_and_audio_grammars_correctly():
    apple = select_blueprints(piece_type='premium desktop product reveal', motion_grammar='APPLE_PREMIUM_DESKTOP', style_family='premium_product', limit=1)
    audio = select_blueprints(piece_type='music app commercial', motion_grammar='HYPER_COMMERCIAL_AUDIO', style_family='dark_technical', limit=1)
    assert apple[0]['blueprint'].blueprint_id == 'apple_product_reveal'
    assert audio[0]['blueprint'].blueprint_id == 'audio_pulse_commercial'
