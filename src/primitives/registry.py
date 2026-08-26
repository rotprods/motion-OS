from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Primitive:
    id: str
    family: str
    renderer_support: list
    compatible_styles: list
    energy_range: list
    duration_range: list
    requires: list
    conflicts: list
    semantic_intents: list[str] = field(default_factory=list)
    attention_roles: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=list)
    physics_profile: str = 'precision_soft'
    easing_presets: list[str] = field(default_factory=lambda: ['ease_out_cubic'])
    forbidden_combinations: list[str] = field(default_factory=list)
    qa: dict = field(default_factory=dict)


DATA = {
    'camera': ['macro_push', 'parallax_push', 'orbit_2_5d', 'snap_zoom', 'whip_pan', 'micro_dolly', 'rack_focus_fake'],
    'transitions': ['object_occlusion', 'foreground_pass', 'match_motion', 'radial_mask', 'velocity_blur', 'light_flash', 'depth_tunnel', 'ink_wipe', 'iris_reveal'],
    'typography': ['mask_reveal', 'tracking_converge', 'kinetic_stack', 'type_tunnel', 'line_stagger', 'blur_reveal', 'word_swap', 'glyph_slice'],
    'graphics': ['technical_grid_draw', 'dotted_matrix', 'blueprint_arc', 'annotation_trace', 'graph_growth', 'crosshair_lock'],
    'objects': ['hero_float', 'coin_spin', 'card_stack', 'image_stack', 'document_flip', 'object_land'],
    'depth': ['z_stack', 'foreground_parallax', 'depth_fog'],
    'lighting': ['specular_sweep', 'light_rim'],
    'masks': ['split_mask', 'shape_morph_mask'],
    'particles': ['dust_field', 'micro_particle_burst'],
}


FAMILY_CONTRACTS = {
    'camera': {
        'semantic_intents': ['direct_attention', 'reveal_depth', 'change_spatial_relationship'],
        'attention_roles': ['primary', 'secondary'],
        'channels': ['x', 'y', 'z', 'scale', 'focus'],
        'qa': {'no_unjustified_shake': True, 'no_magic_camera': True},
    },
    'transitions': {
        'semantic_intents': ['connect_states', 'preserve_continuity', 'redirect_attention'],
        'attention_roles': ['primary'],
        'channels': ['x', 'y', 'scale', 'opacity', 'mask', 'clipPath', 'blur'],
        'qa': {'must_be_motivated': True, 'prefer_existing_element_origin': True},
    },
    'typography': {
        'semantic_intents': ['communicate_information', 'establish_hierarchy', 'emphasize_language'],
        'attention_roles': ['primary', 'secondary'],
        'channels': ['x', 'y', 'scale', 'opacity', 'tracking', 'mask', 'color'],
        'forbidden_combinations': ['destructive_text_blur', 'glyph_morph_without_source_evidence'],
        'qa': {'text_integrity': 'strict', 'readable_before_transform': True},
    },
    'graphics': {
        'semantic_intents': ['explain_structure', 'support_hierarchy', 'visualize_relationship'],
        'attention_roles': ['secondary', 'micro'],
        'channels': ['path', 'stroke', 'opacity', 'scale', 'color'],
        'qa': {'must_not_compete_with_primary': True},
    },
    'objects': {
        'semantic_intents': ['hero_focus', 'materialize_concept', 'show_product_state'],
        'attention_roles': ['primary', 'secondary'],
        'channels': ['x', 'y', 'z', 'scale', 'rotation', 'shadow'],
        'qa': {'contact_and_weight_coherent': True},
    },
    'depth': {
        'semantic_intents': ['separate_planes', 'increase_spatial_clarity'],
        'attention_roles': ['secondary', 'micro'],
        'channels': ['z', 'parallax', 'opacity', 'blur'],
        'qa': {'text_dof_forbidden': True},
    },
    'lighting': {
        'semantic_intents': ['material_emphasis', 'reveal_surface', 'direct_attention'],
        'attention_roles': ['secondary', 'micro'],
        'channels': ['highlight', 'shadow', 'glow', 'specular'],
        'qa': {'material_response_coherent': True},
    },
    'masks': {
        'semantic_intents': ['reveal', 'transform_geometry', 'connect_states'],
        'attention_roles': ['primary', 'secondary'],
        'channels': ['mask', 'clipPath', 'scale', 'path'],
        'qa': {'geometry_continuity': True},
    },
    'particles': {
        'semantic_intents': ['micro_detail', 'impact_reaction', 'atmosphere'],
        'attention_roles': ['micro'],
        'channels': ['x', 'y', 'z', 'opacity', 'scale'],
        'forbidden_combinations': ['free_particles_without_narrative_function'],
        'qa': {'density_cap_required': True},
    },
}


SPECIFIC_INTENTS = {
    'card_stack': ['show_multiple_modules', 'increase_information_density'],
    'image_stack': ['show_reference_set', 'build_visual_context'],
    'match_motion': ['connect_states', 'preserve_velocity'],
    'object_occlusion': ['connect_states', 'hide_cut', 'preserve_spatial_continuity'],
    'tracking_converge': ['emphasize_language', 'resolve_typographic_tension'],
    'specular_sweep': ['material_emphasis', 'reveal_surface'],
    'micro_particle_burst': ['impact_reaction'],
}


def _semantic_primitive(name: str, family: str) -> Primitive:
    contract = FAMILY_CONTRACTS[family]
    intents = list(dict.fromkeys(contract['semantic_intents'] + SPECIFIC_INTENTS.get(name, [])))
    return Primitive(
        name,
        family,
        ['hyperframes', 'remotion', 'chromium_web'],
        ['editorial_finance', 'swiss_brutalist', 'dark_technical', 'experimental_kinetic', 'premium_product'],
        [.2, .95],
        [.12, 2.5],
        [],
        [],
        semantic_intents=intents,
        attention_roles=list(contract['attention_roles']),
        channels=list(contract['channels']),
        physics_profile='precision_soft',
        easing_presets=['ease_out_cubic', 'ease_in_out_cubic'],
        forbidden_combinations=list(contract.get('forbidden_combinations', [])),
        qa=dict(contract['qa']),
    )


def build_registry():
    return [_semantic_primitive(name, family) for family, names in DATA.items() for name in names]


def validate_registry(reg):
    ids = [p.id for p in reg]
    semantic_complete = all(p.semantic_intents and p.channels and p.qa for p in reg)
    return {
        'count': len(reg),
        'unique': len(ids) == len(set(ids)),
        'families': sorted(set(p.family for p in reg)),
        'gte_30': len(reg) >= 30,
        'semantic_complete': semantic_complete,
    }


def primitive_candidates_for_intent(intent: str, *, attention_role: str | None = None, renderer: str | None = None):
    candidates = []
    for primitive in build_registry():
        if intent not in primitive.semantic_intents:
            continue
        if attention_role and attention_role not in primitive.attention_roles:
            continue
        if renderer and renderer not in primitive.renderer_support:
            continue
        candidates.append(primitive)
    return sorted(candidates, key=lambda p: (p.family, p.id))


def anti_template(sequence):
    problems = [f'repeated:{x}' for x in set(sequence) if sequence.count(x) > 2]
    if sequence and all(x in {'mask_reveal', 'blur_reveal', 'hero_float'} for x in sequence):
        problems.append('low_motion_diversity')
    return problems
