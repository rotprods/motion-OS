from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CompositionBlueprint:
    blueprint_id: str
    use_cases: tuple[str, ...]
    preferred_grammars: tuple[str, ...]
    compatible_styles: tuple[str, ...]
    required_beat_roles: tuple[str, ...]
    layer_topology: tuple[str, ...]
    primitive_families: tuple[str, ...]
    transition_policy: str
    audio_policy: str
    required_capabilities: tuple[str, ...]
    negative_rules: tuple[str, ...]
    notes: str = ''

    def __post_init__(self):
        if not self.blueprint_id:
            raise ValueError('blueprint_id required')
        if not self.required_beat_roles:
            raise ValueError(f'{self.blueprint_id}: required beat roles cannot be empty')
        if not self.layer_topology:
            raise ValueError(f'{self.blueprint_id}: layer topology cannot be empty')
        if not self.transition_policy:
            raise ValueError(f'{self.blueprint_id}: transition policy required')


_COMMON_NEGATIVE = (
    'no_fixed_copy',
    'no_unmotivated_transition',
    'no_competing_primary_attention',
    'no_text_blur_without_source_or_director_evidence',
    'no_template_feel',
)


def build_blueprint_registry() -> tuple[CompositionBlueprint, ...]:
    return (
        CompositionBlueprint(
            'apple_product_reveal',
            ('product_reveal', 'desktop_product_demo', 'premium_brand_film', 'ui_motion'),
            ('APPLE_PREMIUM_DESKTOP',),
            ('premium_product', 'editorial_minimal', 'minimal_orbit'),
            ('calm_hook', 'feature_reveal', 'workflow_proof', 'focus_hold', 'ship_resolve'),
            ('ENVIRONMENT', 'SUBJECT', 'MIDGROUND', 'PRIMARY_UI', 'TYPOGRAPHY', 'FOREGROUND', 'CAPTIONS_BRAND'),
            ('camera', 'objects', 'depth', 'lighting', 'typography', 'transitions'),
            'prefer match_geometry / object-origin transitions / panel expansion; preserve generous negative space',
            'quiet premium sound design; sparse impacts; no constant beat chasing',
            ('vector_ui', 'layered_compositing'),
            _COMMON_NEGATIVE + ('no_excessive_glass', 'no_startup_dashboard_density', 'no_harsh_neon'),
        ),
        CompositionBlueprint(
            'saas_ui_proof',
            ('saas_explainer', 'product_demo', 'workflow_demo'),
            ('APPLE_PREMIUM_DESKTOP', 'UI_PROOF_SAAS'),
            ('ui_saas_glow', 'portal_glass_ui', 'dark_technical'),
            ('problem', 'interaction', 'proof', 'system_view', 'resolve'),
            ('ENVIRONMENT', 'BACKGROUND_GRAPHICS', 'PRIMARY_UI', 'TYPOGRAPHY', 'FOREGROUND', 'CAPTIONS_BRAND'),
            ('graphics', 'typography', 'depth', 'masks', 'transitions'),
            'UI state changes create transitions; cursor/focus events must correspond to real interaction logic',
            'UI clicks and state confirmation synced selectively to actions',
            ('vector_ui',),
            _COMMON_NEGATIVE + ('no_fake_dashboard_without_product_semantics',),
        ),
        CompositionBlueprint(
            'hyper_reward_commercial',
            ('gamified_commercial', 'habit_product', 'education_app', 'fitness_reward'),
            ('HYPER_COMMERCIAL_GAMIFIED',),
            ('experimental_kinetic', 'premium_product'),
            ('hook', 'action', 'success', 'reward', 'pressure', 'competition', 'calm_hold', 'brand_condense'),
            ('ENVIRONMENT', 'BACKGROUND_GRAPHICS', 'PRIMARY_UI', 'SUBJECT', 'TYPOGRAPHY', 'FOREGROUND', 'FX', 'CAPTIONS_BRAND'),
            ('objects', 'typography', 'graphics', 'transitions', 'particles'),
            'spring-snappy but hierarchy-controlled; reward systems condense into brand anchor',
            'reward hits, counters and unlocks synchronize to commercial score; calm hold before climax',
            ('vector_ui', 'audio_timing'),
            _COMMON_NEGATIVE + ('no_chaos_without_single_hero', 'no_childish_rubber_hose_by_default'),
        ),
        CompositionBlueprint(
            'audio_pulse_commercial',
            ('music_product', 'audio_app', 'culture_commercial'),
            ('HYPER_COMMERCIAL_AUDIO',),
            ('dark_technical', 'experimental_kinetic', 'portal_glass_ui'),
            ('identity_hook', 'player_state', 'discovery', 'interaction', 'lyrics_or_content', 'audio_space', 'calm_hold', 'brand_condense'),
            ('ENVIRONMENT', 'BACKGROUND_GRAPHICS', 'PRIMARY_UI', 'TYPOGRAPHY', 'FOREGROUND', 'FX', 'CAPTIONS_BRAND'),
            ('graphics', 'typography', 'depth', 'transitions', 'lighting'),
            'audio event may generate visual topology changes; module condensation resolves to brand',
            'AudioGraph is authoritative choreography input; not post-added music',
            ('vector_ui', 'audio_timing'),
            _COMMON_NEGATIVE + ('no_random_waveform_spam', 'no_unsynced_equalizer_as_decoration'),
        ),
        CompositionBlueprint(
            'editorial_kinetic',
            ('editorial_motion', 'brand_manifesto', 'kinetic_typography', 'social_ad'),
            ('EDITORIAL_KINETIC',),
            ('editorial_minimal', 'print_editorial', 'experimental_kinetic'),
            ('hook', 'language_build', 'visual_argument', 'contrast', 'resolve'),
            ('ENVIRONMENT', 'BACKGROUND_GRAPHICS', 'FOOTAGE_PLATES', 'TYPOGRAPHY', 'FOREGROUND', 'CAPTIONS_BRAND'),
            ('typography', 'graphics', 'masks', 'transitions'),
            'typography and geometry carry continuity; readability precedes transformation',
            'type gestures align selectively with accents and pauses',
            ('vector_text',),
            _COMMON_NEGATIVE + ('no_decorative_glyph_morph',),
        ),
        CompositionBlueprint(
            'minimal_orbit_ident',
            ('ident', 'brand_lockup', 'premium_tech_intro'),
            ('MINIMAL_ORBIT',),
            ('minimal_orbit', 'editorial_minimal'),
            ('seed', 'orbit', 'assemble', 'resolve', 'lockup'),
            ('ENVIRONMENT', 'BACKGROUND_GRAPHICS', 'SUBJECT', 'FOREGROUND', 'CAPTIONS_BRAND'),
            ('graphics', 'objects', 'lighting', 'transitions'),
            'keep background stable; primary shape morph/orbit creates continuity',
            'soft minimal sound cues; no aggressive commercial pacing',
            ('vector_shapes',),
            _COMMON_NEGATIVE + ('no_harsh_snap', 'one_accent_max_per_scene'),
        ),
        CompositionBlueprint(
            'portal_glass_demo',
            ('cinematic_product_demo', 'ai_product', 'tool_demo'),
            ('PORTAL_GLASS', 'APPLE_PREMIUM_DESKTOP'),
            ('portal_glass_ui', 'frosted_atmosphere', 'dark_technical'),
            ('atmosphere', 'hero_card', 'interaction', 'multi_module_proof', 'focus', 'resolve'),
            ('ENVIRONMENT', 'BACKGROUND_GRAPHICS', 'FOOTAGE_PLATES', 'MIDGROUND', 'PRIMARY_UI', 'TYPOGRAPHY', 'FOREGROUND', 'FX', 'CAPTIONS_BRAND'),
            ('depth', 'graphics', 'masks', 'lighting', 'typography', 'transitions'),
            'one atmospheric gradient per scene; glass is hierarchical, not ubiquitous; orbital motif reserved for transitions',
            'subtle UI feedback plus cinematic swells; sound follows interaction and spatial reveal',
            ('vector_ui', 'layered_compositing'),
            _COMMON_NEGATIVE + ('no_glass_everywhere', 'no_low_contrast_text'),
        ),
    )


def validate_blueprints(blueprints: Iterable[CompositionBlueprint]) -> dict:
    items = tuple(blueprints)
    ids = [item.blueprint_id for item in items]
    fixed_copy_markers = ('DUOLINGO', 'SPOTIFY', 'KEEP GOING', 'NOW PLAYING', 'RACHA 128')
    no_fixed_copy = all(
        not any(marker in str(item).upper() for marker in fixed_copy_markers)
        for item in items
    )
    return {
        'count': len(items),
        'unique': len(ids) == len(set(ids)),
        'no_fixed_copy': no_fixed_copy,
        'all_structural': all(item.required_beat_roles and item.layer_topology and item.primitive_families for item in items),
    }


def select_blueprints(*, piece_type: str = '', motion_grammar: str = '', style_family: str = '', limit: int = 3):
    query = f'{piece_type} {motion_grammar} {style_family}'.casefold()
    scored = []
    for blueprint in build_blueprint_registry():
        score = 0
        reasons = []
        if motion_grammar and motion_grammar in blueprint.preferred_grammars:
            score += 5
            reasons.append('motion_grammar_exact')
        if style_family and style_family in blueprint.compatible_styles:
            score += 3
            reasons.append('style_exact')
        for use_case in blueprint.use_cases:
            tokens = use_case.replace('_', ' ').split()
            overlap = sum(token in query for token in tokens)
            if overlap:
                score += overlap
                reasons.append(f'use_case:{use_case}')
        if blueprint.blueprint_id.replace('_', ' ') in query:
            score += 4
            reasons.append('blueprint_name_match')
        scored.append((score, blueprint.blueprint_id, reasons, blueprint))
    ranked = sorted(scored, key=lambda item: (item[0], item[1]), reverse=True)
    return [
        {'blueprint': blueprint, 'score': score, 'reasons': tuple(reasons)}
        for score, _, reasons, blueprint in ranked[:limit]
        if score > 0
    ]
