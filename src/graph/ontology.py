from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import FrozenSet


class GraphLevel(StrEnum):
    L1_SEMANTIC = "L1_SEMANTIC"
    L2_EDITING = "L2_EDITING"
    L3_RENDER_EVIDENCE = "L3_RENDER_EVIDENCE"


class NodeKind(StrEnum):
    PROJECT = "Project"
    BRIEF = "Brief"
    INTENT = "Intent"
    EMOTION_STATE = "EmotionState"
    NARRATIVE_BEAT = "NarrativeBeat"
    BRAND_RULE = "BrandRule"
    ATTENTION_TARGET = "AttentionTarget"
    PRODUCT_SEMANTIC = "ProductSemantic"
    STYLE_SIGNATURE = "StyleSignature"
    MOTION_GRAMMAR = "MotionGrammar"
    NEGATIVE_CONSTRAINT = "NegativeConstraint"

    SCENE = "Scene"
    SHOT = "Shot"
    LAYER = "Layer"
    TRACK = "Track"
    ASSET = "Asset"
    ASSET_VARIANT = "AssetVariant"
    PRIMITIVE = "Primitive"
    TRANSITION = "Transition"
    CAMERA_RIG = "CameraRig"
    MATERIAL = "Material"
    LIGHT_RIG = "LightRig"
    TYPOGRAPHY_ROLE = "TypographyRole"
    AUDIO_CUE = "AudioCue"
    MUSIC_BEAT = "MusicBeat"
    VOICE_LINE = "VoiceLine"
    EFFECT = "Effect"
    MASK = "Mask"
    COMPOSITION_BLUEPRINT = "CompositionBlueprint"

    RENDERER = "Renderer"
    SKILL = "Skill"
    PROVIDER = "Provider"
    TOOL_CALL = "ToolCall"
    COMPOSITION = "Composition"
    RENDER_REGION = "RenderRegion"
    ARTIFACT = "Artifact"
    RUN = "Run"
    QA_RESULT = "QAResult"
    DEFECT = "Defect"
    ROOT_CAUSE = "RootCause"
    REPAIR_CANDIDATE = "RepairCandidate"
    RELEASE = "Release"


class RelationKind(StrEnum):
    REQUIRES = "REQUIRES"
    DRIVES = "DRIVES"
    SHAPES = "SHAPES"
    MATERIALIZES_AS = "MATERIALIZES_AS"
    CONTAINS = "CONTAINS"
    USES = "USES"
    ANIMATED_BY = "ANIMATED_BY"
    CONSTRAINED_BY = "CONSTRAINED_BY"
    ENTERS_VIA = "ENTERS_VIA"
    EXITS_VIA = "EXITS_VIA"
    SOURCED_FROM = "SOURCED_FROM"
    SUPPORTED_BY = "SUPPORTED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    CONDITIONS = "CONDITIONS"
    COMPILES_TO = "COMPILES_TO"
    RENDERED_BY = "RENDERED_BY"
    REQUIRES_SKILL = "REQUIRES_SKILL"
    SYNC_WITH = "SYNC_WITH"
    FLAGS = "FLAGS"
    CAUSED_BY = "CAUSED_BY"
    GENERATES = "GENERATES"
    MUTATES = "MUTATES"
    PRODUCED_BY = "PRODUCED_BY"
    INVALIDATES = "INVALIDATES"
    DEPENDS_ON = "DEPENDS_ON"
    ROUTES_TO = "ROUTES_TO"
    EVALUATES = "EVALUATES"
    PROMOTES = "PROMOTES"
    ROLLS_BACK_TO = "ROLLS_BACK_TO"


LEVEL_BY_KIND: dict[NodeKind, GraphLevel] = {
    **{kind: GraphLevel.L1_SEMANTIC for kind in (
        NodeKind.PROJECT, NodeKind.BRIEF, NodeKind.INTENT, NodeKind.EMOTION_STATE,
        NodeKind.NARRATIVE_BEAT, NodeKind.BRAND_RULE, NodeKind.ATTENTION_TARGET,
        NodeKind.PRODUCT_SEMANTIC, NodeKind.STYLE_SIGNATURE, NodeKind.MOTION_GRAMMAR,
        NodeKind.NEGATIVE_CONSTRAINT,
    )},
    **{kind: GraphLevel.L2_EDITING for kind in (
        NodeKind.SCENE, NodeKind.SHOT, NodeKind.LAYER, NodeKind.TRACK, NodeKind.ASSET,
        NodeKind.ASSET_VARIANT, NodeKind.PRIMITIVE, NodeKind.TRANSITION, NodeKind.CAMERA_RIG,
        NodeKind.MATERIAL, NodeKind.LIGHT_RIG, NodeKind.TYPOGRAPHY_ROLE, NodeKind.AUDIO_CUE,
        NodeKind.MUSIC_BEAT, NodeKind.VOICE_LINE, NodeKind.EFFECT, NodeKind.MASK,
        NodeKind.COMPOSITION_BLUEPRINT,
    )},
    **{kind: GraphLevel.L3_RENDER_EVIDENCE for kind in (
        NodeKind.RENDERER, NodeKind.SKILL, NodeKind.PROVIDER, NodeKind.TOOL_CALL,
        NodeKind.COMPOSITION, NodeKind.RENDER_REGION, NodeKind.ARTIFACT, NodeKind.RUN,
        NodeKind.QA_RESULT, NodeKind.DEFECT, NodeKind.ROOT_CAUSE, NodeKind.REPAIR_CANDIDATE,
        NodeKind.RELEASE,
    )},
}


LEGACY_KIND_ALIASES: dict[str, NodeKind] = {
    "Beat": NodeKind.NARRATIVE_BEAT,
    "Brief": NodeKind.BRIEF,
    "Asset": NodeKind.ASSET,
    "Renderer": NodeKind.RENDERER,
    "Scene": NodeKind.SCENE,
    "Shot": NodeKind.SHOT,
    "Layer": NodeKind.LAYER,
    "Transition": NodeKind.TRANSITION,
    "Primitive": NodeKind.PRIMITIVE,
    "Defect": NodeKind.DEFECT,
    "Artifact": NodeKind.ARTIFACT,
}


@dataclass(frozen=True)
class RelationRule:
    source_levels: FrozenSet[GraphLevel]
    target_levels: FrozenSet[GraphLevel]
    allow_same_node: bool = False


ALL_LEVELS = frozenset(GraphLevel)
SEMANTIC_TO_ANY = RelationRule(frozenset({GraphLevel.L1_SEMANTIC}), ALL_LEVELS)
EDITING_TO_ANY = RelationRule(frozenset({GraphLevel.L2_EDITING}), ALL_LEVELS)
RENDER_TO_ANY = RelationRule(frozenset({GraphLevel.L3_RENDER_EVIDENCE}), ALL_LEVELS)
ANY_TO_ANY = RelationRule(ALL_LEVELS, ALL_LEVELS)


RELATION_RULES: dict[RelationKind, RelationRule] = {
    RelationKind.REQUIRES: ANY_TO_ANY,
    RelationKind.DRIVES: SEMANTIC_TO_ANY,
    RelationKind.SHAPES: SEMANTIC_TO_ANY,
    RelationKind.MATERIALIZES_AS: RelationRule(frozenset({GraphLevel.L1_SEMANTIC}), frozenset({GraphLevel.L2_EDITING})),
    RelationKind.CONTAINS: ANY_TO_ANY,
    RelationKind.USES: ANY_TO_ANY,
    RelationKind.ANIMATED_BY: RelationRule(frozenset({GraphLevel.L2_EDITING}), frozenset({GraphLevel.L2_EDITING})),
    RelationKind.CONSTRAINED_BY: ANY_TO_ANY,
    RelationKind.ENTERS_VIA: RelationRule(frozenset({GraphLevel.L2_EDITING}), frozenset({GraphLevel.L2_EDITING})),
    RelationKind.EXITS_VIA: RelationRule(frozenset({GraphLevel.L2_EDITING}), frozenset({GraphLevel.L2_EDITING})),
    RelationKind.SOURCED_FROM: RelationRule(frozenset({GraphLevel.L2_EDITING}), frozenset({GraphLevel.L3_RENDER_EVIDENCE})),
    RelationKind.SUPPORTED_BY: ANY_TO_ANY,
    RelationKind.DERIVED_FROM: ANY_TO_ANY,
    RelationKind.CONDITIONS: ANY_TO_ANY,
    RelationKind.COMPILES_TO: RelationRule(frozenset({GraphLevel.L1_SEMANTIC, GraphLevel.L2_EDITING}), frozenset({GraphLevel.L2_EDITING, GraphLevel.L3_RENDER_EVIDENCE})),
    RelationKind.RENDERED_BY: RelationRule(frozenset({GraphLevel.L2_EDITING, GraphLevel.L3_RENDER_EVIDENCE}), frozenset({GraphLevel.L3_RENDER_EVIDENCE})),
    RelationKind.REQUIRES_SKILL: RelationRule(ALL_LEVELS, frozenset({GraphLevel.L3_RENDER_EVIDENCE})),
    RelationKind.SYNC_WITH: RelationRule(frozenset({GraphLevel.L2_EDITING}), frozenset({GraphLevel.L2_EDITING})),
    RelationKind.FLAGS: RelationRule(frozenset({GraphLevel.L3_RENDER_EVIDENCE}), ALL_LEVELS),
    RelationKind.CAUSED_BY: RelationRule(frozenset({GraphLevel.L3_RENDER_EVIDENCE}), ALL_LEVELS),
    RelationKind.GENERATES: ANY_TO_ANY,
    RelationKind.MUTATES: RelationRule(frozenset({GraphLevel.L3_RENDER_EVIDENCE}), ALL_LEVELS),
    RelationKind.PRODUCED_BY: RelationRule(frozenset({GraphLevel.L3_RENDER_EVIDENCE}), frozenset({GraphLevel.L3_RENDER_EVIDENCE})),
    RelationKind.INVALIDATES: ANY_TO_ANY,
    RelationKind.DEPENDS_ON: ANY_TO_ANY,
    RelationKind.ROUTES_TO: RelationRule(frozenset({GraphLevel.L2_EDITING, GraphLevel.L3_RENDER_EVIDENCE}), frozenset({GraphLevel.L3_RENDER_EVIDENCE})),
    RelationKind.EVALUATES: RelationRule(frozenset({GraphLevel.L3_RENDER_EVIDENCE}), ALL_LEVELS),
    RelationKind.PROMOTES: RelationRule(frozenset({GraphLevel.L3_RENDER_EVIDENCE}), frozenset({GraphLevel.L3_RENDER_EVIDENCE})),
    RelationKind.ROLLS_BACK_TO: RelationRule(frozenset({GraphLevel.L3_RENDER_EVIDENCE}), frozenset({GraphLevel.L3_RENDER_EVIDENCE})),
}


def canonical_kind(value: str | NodeKind) -> NodeKind:
    if isinstance(value, NodeKind):
        return value
    try:
        return NodeKind(value)
    except ValueError:
        if value in LEGACY_KIND_ALIASES:
            return LEGACY_KIND_ALIASES[value]
        raise ValueError(f"Unknown canonical node kind: {value}") from None


def level_for_kind(value: str | NodeKind) -> GraphLevel:
    return LEVEL_BY_KIND[canonical_kind(value)]


def relation_is_legal(relation: str | RelationKind, source_kind: str | NodeKind, target_kind: str | NodeKind) -> bool:
    rel = relation if isinstance(relation, RelationKind) else RelationKind(relation)
    source_level = level_for_kind(source_kind)
    target_level = level_for_kind(target_kind)
    rule = RELATION_RULES[rel]
    return source_level in rule.source_levels and target_level in rule.target_levels
