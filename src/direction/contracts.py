from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass(frozen=True)
class EmotionStateSpec:
    phase: str
    emotion: str
    intensity: float

    def __post_init__(self):
        if not 0 <= self.intensity <= 1:
            raise ValueError('emotion intensity must be within [0,1]')


@dataclass(frozen=True)
class MotionPhysicsProfile:
    behavior: str
    acceleration: str
    deceleration: str
    inertia: float
    perceived_weight: float
    elasticity: float
    friction: float
    overshoot: float
    follow_through: float

    def __post_init__(self):
        for field_name in ('inertia', 'perceived_weight', 'elasticity', 'friction', 'overshoot', 'follow_through'):
            value = getattr(self, field_name)
            if not 0 <= value <= 1:
                raise ValueError(f'{field_name} must be within [0,1]')


@dataclass(frozen=True)
class DirectorBeat:
    beat_id: str
    start_ms: int
    end_ms: int
    dominant_element: str
    primary_action: str
    attention_target: str
    secondary_attention: str | None
    suppress: tuple[str, ...]
    narrative_function: str
    motion_purpose: str
    sound_event: str | None
    semantic_behavior: str
    primitive_candidates: tuple[str, ...]

    def __post_init__(self):
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError(f'invalid beat timing {self.beat_id}')
        if not self.motion_purpose.strip():
            raise ValueError('every beat requires a motion purpose')


@dataclass(frozen=True)
class DirectorSpec:
    project_id: str
    brief: str
    piece_type: str
    duration_ms: int
    aspect_ratio: str
    platform: str | None
    brand: str | None
    emotional_curve: tuple[EmotionStateSpec, ...]
    visual_dna: dict[str, Any]
    motion_physics: MotionPhysicsProfile
    beats: tuple[DirectorBeat, ...]
    negative_motion_rules: tuple[str, ...]
    final_frame_memory: str
    brand_motion_language: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.duration_ms <= 0:
            raise ValueError('duration_ms must be positive')
        if not self.beats:
            raise ValueError('DirectorSpec requires at least one beat')
        if self.beats[0].start_ms != 0:
            raise ValueError('timeline must begin at 0ms')
        if self.beats[-1].end_ms != self.duration_ms:
            raise ValueError('timeline must cover full duration')
        for previous, current in zip(self.beats, self.beats[1:]):
            if previous.end_ms != current.start_ms:
                raise ValueError(f'timeline gap/overlap between {previous.beat_id} and {current.beat_id}')

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_NEGATIVE_MOTION_RULES = (
    'no_random_motion',
    'no_gratuitous_zoom',
    'no_generic_transition_without_semantic_or_geometric_link',
    'no_floating_without_physics',
    'no_excessive_motion_blur',
    'no_semantically_unrelated_morph',
    'no_unjustified_camera_shake',
    'no_childish_elasticity_unless_brand_requires_it',
    'no_free_particles',
    'no_unreadable_text_during_motion',
    'no_competing_primary_attention_moves',
    'no_template_or_after_effects_preset_feel',
    'no_motion_that_breaks_brand_rules',
)


def default_precision_physics() -> MotionPhysicsProfile:
    return MotionPhysicsProfile(
        behavior='precision_soft',
        acceleration='fast_controlled',
        deceleration='progressive_soft',
        inertia=0.25,
        perceived_weight=0.45,
        elasticity=0.08,
        friction=0.72,
        overshoot=0.03,
        follow_through=0.12,
    )
